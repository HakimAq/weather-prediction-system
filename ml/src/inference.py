from __future__ import annotations

import logging
from datetime import timedelta

import joblib
import numpy as np
import pandas as pd

from .config import MODEL_DIR, TARGETS, FORECAST_HORIZON
from .cleaner import clean_data
from .feature_engineering import build_features, EXTRA_FEATURES


log = logging.getLogger(__name__)

CORE_COLS = TARGETS
MIN_HISTORY_DAYS = 14
MAX_HISTORY_DAYS = 60

_MODELS_RF: dict[int, object] = {}
_MODELS_GB: dict[int, object] = {}
_FEATURE_COLS: list[str] | None = None
_CLIMATE: pd.DataFrame | None = None


def load_models() -> None:
    global _FEATURE_COLS, _CLIMATE
    if _MODELS_RF:
        return

    _FEATURE_COLS = joblib.load(MODEL_DIR / "feature_columns.pkl")

    for h in range(1, FORECAST_HORIZON + 1):
        _MODELS_RF[h] = joblib.load(MODEL_DIR / f"rf_h{h}.pkl")
        _MODELS_GB[h] = joblib.load(MODEL_DIR / f"gb_h{h}.pkl")

    climate_path = MODEL_DIR / "climate_lookup.csv"
    if climate_path.exists():
        _CLIMATE = pd.read_csv(climate_path).set_index("doy")
    else:
        log.warning("climate_lookup.csv not found — extras will be zero-filled")
        _CLIMATE = None

    log.info("Loaded %d RF + %d GB models", len(_MODELS_RF), len(_MODELS_GB))


def is_loaded() -> bool:
    return bool(_MODELS_RF)


def _fill_missing_extras(df: pd.DataFrame) -> pd.DataFrame:
    missing = [c for c in EXTRA_FEATURES if c not in df.columns]
    if not missing:
        return df

    log.info("Filling %d missing extra columns from climate lookup", len(missing))

    if _CLIMATE is None:
        for c in missing:
            df[c] = 0.0
        return df

    doy = df["datetime"].dt.dayofyear
    for c in missing:
        if c in _CLIMATE.columns:
            df[c] = doy.map(_CLIMATE[c]).ffill().bfill().values
        else:
            df[c] = 0.0
    return df


def _sanity_warn(df: pd.DataFrame) -> None:
    checks = {
        "temp":             (-5.0,   45.0),
        "humidity":         (0.0,   100.0),
        "precip":           (0.0,   400.0),
        "windspeed":        (0.0,   180.0),
        "sealevelpressure": (950.0, 1050.0),
        "cloudcover":       (0.0,   100.0),
    }
    for c, (lo, hi) in checks.items():
        if c not in df.columns:
            continue
        bad = ((df[c] < lo) | (df[c] > hi)).sum()
        if bad:
            log.warning("Column '%s' has %d values outside [%s, %s] — will be clipped",
                        c, bad, lo, hi)


def _prepare_input(history: list[dict]) -> pd.DataFrame:
    if not history:
        raise ValueError("history is empty")

    n = len(history)
    if n < MIN_HISTORY_DAYS:
        raise ValueError(f"at least {MIN_HISTORY_DAYS} days required, got {n}")
    if n > MAX_HISTORY_DAYS:
        raise ValueError(f"at most {MAX_HISTORY_DAYS} days allowed, got {n}")

    df = pd.DataFrame(history)
    if "datetime" not in df.columns:
        raise ValueError("history rows must contain 'datetime'")
    if "precipitation" in df.columns and "precip" not in df.columns:
        df = df.rename(columns={"precipitation": "precip"})

    for c in CORE_COLS:
        if c not in df.columns:
            raise ValueError(f"history rows must contain '{c}'")

    df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")
    df = df.dropna(subset=["datetime"]).sort_values("datetime").reset_index(drop=True)

    df = _fill_missing_extras(df)
    return df


def _build_feature_matrix(df: pd.DataFrame) -> tuple[np.ndarray, pd.Timestamp]:
    cleaned = clean_data(df, verbose=False)
    featured = build_features(cleaned)

    if featured.empty:
        raise ValueError("Not enough history after cleaning. Provide at least 14 consecutive days.")

    last_row = featured.iloc[[-1]].copy()
    last_date = last_row["datetime"].iloc[0]

    X = last_row.reindex(columns=_FEATURE_COLS, fill_value=0.0).values.astype(np.float64)
    return X, last_date


def _format_forecast(raw: np.ndarray, last_date: pd.Timestamp) -> list[dict]:
    out = []
    for h, row in enumerate(raw, start=1):
        target_date = (last_date + timedelta(days=h)).strftime("%Y-%m-%d")
        item = {"day": h, "date": target_date}
        for i, t in enumerate(TARGETS):
            item[t] = round(float(row[i]), 2)
        out.append(item)
    return out


def _clip_predictions(arr: np.ndarray) -> np.ndarray:
    arr[:, TARGETS.index("humidity")]         = np.clip(arr[:, TARGETS.index("humidity")], 0, 100)
    arr[:, TARGETS.index("precip")]           = np.clip(arr[:, TARGETS.index("precip")], 0, None)
    arr[:, TARGETS.index("windspeed")]        = np.clip(arr[:, TARGETS.index("windspeed")], 0, None)
    arr[:, TARGETS.index("cloudcover")]       = np.clip(arr[:, TARGETS.index("cloudcover")], 0, 100)
    arr[:, TARGETS.index("sealevelpressure")] = np.clip(arr[:, TARGETS.index("sealevelpressure")], 950, 1050)
    return arr


def predict_7_days(history: list[dict], model: str = "both") -> dict:
    if not is_loaded():
        load_models()

    if model not in ("rf", "gb", "both"):
        raise ValueError("model must be 'rf', 'gb', or 'both'")

    df = _prepare_input(history)
    _sanity_warn(df)

    X, last_date = _build_feature_matrix(df)

    rf_raw = np.vstack([_MODELS_RF[h].predict(X)[0] for h in range(1, FORECAST_HORIZON + 1)])
    gb_raw = np.vstack([_MODELS_GB[h].predict(X)[0] for h in range(1, FORECAST_HORIZON + 1)])

    rf_raw = _clip_predictions(rf_raw)
    gb_raw = _clip_predictions(gb_raw)

    forecast = {
        "random_forest":     _format_forecast(rf_raw, last_date),
        "gradient_boosting": _format_forecast(gb_raw, last_date),
    }
    if model == "rf":
        forecast.pop("gradient_boosting")
    elif model == "gb":
        forecast.pop("random_forest")

    return {
        "status": "success",
        "location": "Kathmandu",
        "input_days": len(df),
        "last_input_date": last_date.strftime("%Y-%m-%d"),
        "forecast": forecast,
    }