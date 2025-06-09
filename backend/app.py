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

import openai
from chat_state import push_msg, history
from prompts import build_prompt
from parse import parse_bin_to_df  # make sure this lives alongside app.py

# ─── Config ────────────────────────────────────────────────────────────────────
load_dotenv()  # loads OPENAI_API_KEY
openai.api_key = os.getenv("OPENAI_API_KEY")

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
    # generate a new session
    session_id = str(uuid.uuid4())

    # read & parse
    raw = await file.read()
    try:
        df = parse_bin_to_df(io.BytesIO(raw))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse log: {e}")

    # save
    path = os.path.join(TELEMETRY_DIR, f"{session_id}.parquet")
    df.to_parquet(path, index=False)

    return {
        "session_id": session_id,
        "rows": len(df),
        "columns": list(df.columns),
    }


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
    resp = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[system, *hist],
        temperature=0.2,
    )
    answer = resp.choices[0].message.content.strip()

    # store assistant
    push_msg(req.flight_id, "assistant", answer)
    return ChatResponse(answer=answer)
