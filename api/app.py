from __future__ import annotations

import logging
import sys
from pathlib import Path

from flask import Flask, jsonify, request
from flask_cors import CORS


API_DIR = Path(__file__).resolve().parent
ML_DIR  = API_DIR.parent / "ml"
sys.path.insert(0, str(ML_DIR))

from src.inference import load_models, predict_7_days, is_loaded  # noqa: E402


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("api")

app = Flask(__name__)
CORS(app)


@app.get("/health")
def health():
    return jsonify({
        "status": "ok",
        "models_loaded": is_loaded(),
        "service": "kathmandu-weather-api",
    })


@app.post("/predict")
def predict():
    if not request.is_json:
        return jsonify({"status": "error", "error": "Content-Type must be application/json"}), 400

    payload = request.get_json(silent=True) or {}
    history = payload.get("history")
    model   = payload.get("model", "both")

    if not isinstance(history, list):
        return jsonify({"status": "error", "error": "'history' must be a list of day-objects"}), 400

    try:
        result = predict_7_days(history=history, model=model)
    except ValueError as e:
        log.warning("Validation error: %s", e)
        return jsonify({"status": "error", "error": str(e)}), 400
    except Exception as e:
        log.exception("Prediction failed")
        return jsonify({"status": "error", "error": f"internal error: {e}"}), 500

    return jsonify(result)


@app.errorhandler(404)
def not_found(_):
    return jsonify({"status": "error", "error": "not found"}), 404


@app.errorhandler(405)
def method_not_allowed(_):
    return jsonify({"status": "error", "error": "method not allowed"}), 405


if __name__ == "__main__":
    log.info("Loading models at startup...")
    load_models()
    log.info("Models loaded. Starting Flask on http://localhost:5000")
    app.run(host="0.0.0.0", port=5000, debug=False)