import json
from datetime import datetime, timedelta

import requests


BASE = "http://localhost:5000"


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


def main() -> None:
    print("=" * 60)
    print("GET /health")
    print("=" * 60)
    r = requests.get(f"{BASE}/health", timeout=10)
    print(r.status_code, r.json())
    print()

    print("=" * 60)
    print("POST /predict  (model=both)")
    print("=" * 60)
    payload = {"history": build_sample_history(), "model": "both"}
    r = requests.post(f"{BASE}/predict", json=payload, timeout=30)
    print(r.status_code)
    print(json.dumps(r.json(), indent=2)[:1500], "...\n")

    print("=" * 60)
    print("POST /predict  (invalid — only 5 days)")
    print("=" * 60)
    r = requests.post(f"{BASE}/predict",
                      json={"history": build_sample_history()[:5]},
                      timeout=30)
    print(r.status_code, r.json())


if __name__ == "__main__":
    main()