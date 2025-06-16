import pandas as pd
import pytest

from your_package.parser import create_minimal_test_data, parse_flight_dataframe

def test_parse_minimal_test_data():
    # 1) build a tiny DataFrame
    df = create_minimal_test_data()
    # 2) invoke your parser (the same function your chatbot backend uses)
    result = parse_flight_dataframe(df)

    # 3) assert a few key things:
    #    – max altitude
    assert result["max_altitude"] == pytest.approx(85.0)
    #    – first GPS-quality dip below 2.0 happens at the 4th reading (i.e. minute 3)
    assert result["first_poor_gps_minute"] == 3
    #    – battery low threshold detected
    assert result["min_voltage"] == pytest.approx(11.8)
