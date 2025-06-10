import os
import io
import uuid
from dotenv import load_dotenv
from fastapi import Request, Response

import pandas as pd
from fastapi import FastAPI, UploadFile, File, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware 
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from openai import OpenAI
from chat_state import push_msg, history
from prompts import build_prompt
from parse import parse_bin_to_df  # make sure this lives alongside app.py

# ─── Config ────────────────────────────────────────────────────────────────────
load_dotenv()  # loads OPENAI_API_KEY
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# directory to store parsed telemetry
TELEMETRY_DIR = os.path.join(os.path.dirname(__file__), "_telemetry")
os.makedirs(TELEMETRY_DIR, exist_ok=True)

app = FastAPI(
    title="UAVLogViewer Chatbot API",
    description="Upload .bin logs and ask questions via LLM",
    version="0.1",
)
"""
class BodySizeLimiter(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        max_bytes = 150 * 1024 * 1024    # 150 MB
        body = await request.body()
        if len(body) > max_bytes:
            return Response("Payload too large", status_code=413)
        return await call_next(request)
app.add_middleware(BodySizeLimiter)
"""



# Allow Vue dev server on localhost:8080
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Models ────────────────────────────────────────────────────────────────────
class ChatRequest(BaseModel):
    flight_id: str
    question: str

class ChatResponse(BaseModel):
    answer: str

# ─── Endpoints ─────────────────────────────────────────────────────────────────
@app.get("/ping")
async def ping():
    """Health check."""
    return {"pong": True}


@app.post("/upload-log")
async def upload_log(file: UploadFile = File(...)):
    """
    Receive a .bin file, parse it into a DataFrame, store as parquet, and return session_id.
    """
    import time
    start_time = time.time()
    
    # generate a new session
    session_id = str(uuid.uuid4())
    print(f"Starting upload for session {session_id}")

    # read & parse
    raw = await file.read()
    print(f"File read in {time.time() - start_time:.2f}s, size: {len(raw)} bytes")
    
    try:
        df = parse_bin_to_df(io.BytesIO(raw), filename=file.filename)
        print(f"Parse completed in {time.time() - start_time:.2f}s, filename: {file.filename}")
    except Exception as e:
        print(f"Parse failed after {time.time() - start_time:.2f}s: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to parse log: {e}")

    # save (skip if too slow)
    try:
        path = os.path.join(TELEMETRY_DIR, f"{session_id}.parquet")
        df.to_parquet(path, index=False)
        print(f"Total upload time: {time.time() - start_time:.2f}s")
    except Exception as e:
        print(f"Failed to save parquet, but continuing: {e}")
        print(f"Upload time before save failure: {time.time() - start_time:.2f}s")

    return {
        "session_id": session_id,
        "rows": len(df),
        "columns": list(df.columns),
    }


@app.get("/api/tlog-data/{session_id}")
async def get_tlog_data(session_id: str):
    """
    Return parsed TLOG data for frontend visualization.
    """
    import json
    import numpy as np
    
    path = os.path.join(TELEMETRY_DIR, f"{session_id}.parquet")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="invalid session_id")

    # load DF and convert to dict for frontend
    df = pd.read_parquet(path)
    
    # Convert to JSON-serializable format more safely
    data = []
    for record in df.to_dict('records'):
        clean_record = {}
        for key, value in record.items():
            try:
                # Handle None/NaN values first
                if value is None or pd.isna(value):
                    clean_record[key] = None
                # Handle numpy numeric types
                elif isinstance(value, (np.integer, np.int8, np.int16, np.int32, np.int64)):
                    clean_record[key] = int(value)
                elif isinstance(value, (np.floating, np.float16, np.float32, np.float64)):
                    # Check for inf/-inf values
                    if np.isinf(value):
                        clean_record[key] = None
                    else:
                        clean_record[key] = float(value)
                elif isinstance(value, np.bool_):
                    clean_record[key] = bool(value)
                # Handle complex types (arrays, lists, etc.)
                elif isinstance(value, (np.ndarray, list, tuple)):
                    clean_record[key] = str(value)
                # Handle datetime objects
                elif hasattr(value, 'isoformat'):
                    clean_record[key] = value.isoformat()
                # Handle other numpy types
                elif hasattr(value, 'item'):
                    clean_record[key] = value.item()
                # Keep basic Python types as-is
                else:
                    clean_record[key] = value
            except Exception as e:
                # If any conversion fails, convert to string as fallback
                print(f"Warning: Failed to convert {key}={value}, using string: {e}")
                clean_record[key] = str(value)
        data.append(clean_record)
    
    return data


@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest):
    """
    Ask the LLM about the flight. Expects flight_id to exist in TELEMETRY_DIR.
    """
    path = os.path.join(TELEMETRY_DIR, f"{req.flight_id}.parquet")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="invalid session_id")

    # load DF
    df = pd.read_parquet(path)

    # pull & push user message
    hist = history(req.flight_id)
    push_msg(req.flight_id, "user", req.question)
    hist.append({"role":"user", "content": req.question})

    # build prompt + call OpenAI
    system = build_prompt(df, hist)
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[system, *hist],
        temperature=0.2,
    )
    answer = resp.choices[0].message.content.strip()

    # store assistant
    push_msg(req.flight_id, "assistant", answer)
    return ChatResponse(answer=answer)
