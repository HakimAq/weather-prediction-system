import json
from datetime import datetime, timedelta

from src.inference import predict_7_days, load_models


def build_sample_history() -> list[dict]:
    base = datetime(2025, 6, 17)
    rows = []
    for i in range(14):
        rows.append({
            "datetime":         (base + timedelta(days=i)).strftime("%Y-%m-%d"),
            "temp":             20.0 + i * 0.3,
            "humidity":         75.0 + i * 0.5,
            "precip":           float(i % 4) * 3.5,
            "windspeed":        9.0 + i * 0.2,
            "sealevelpressure": 1008.0 + (i % 5),
            "cloudcover":       40.0 + (i % 6) * 8,
        })
    return rows


if __name__ == "__main__":
    load_models()
    result = predict_7_days(build_sample_history(), model="both")
    print(json.dumps(result, indent=2))