import numpy as np
import pandas as pd

from .config import TARGETS, LAGS, ROLLING_WINDOWS


EXTRA_FEATURES = [
    "dew", "tempmax", "tempmin", "windgust", "winddir",
    "visibility", "solarradiation", "solarenergy", "uvindex",
    "precipprob", "precipcover",
]

EXTRA_LAGS = [1, 7]
EXTRA_ROLLS = [7]


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    feat = {}

    doy = df["datetime"].dt.dayofyear
    feat["day_of_year"] = doy
    feat["month"]       = df["datetime"].dt.month
    feat["day_of_week"] = df["datetime"].dt.dayofweek
    feat["sin_doy"]     = np.sin(2 * np.pi * doy / 365.25)
    feat["cos_doy"]     = np.cos(2 * np.pi * doy / 365.25)
    feat["is_monsoon"]  = df["month"].isin([6, 7, 8, 9]).astype(int) if "month" in df else \
                          df["datetime"].dt.month.isin([6, 7, 8, 9]).astype(int)

    for tgt in TARGETS:
        for lag in LAGS:
            feat[f"{tgt}_lag{lag}"] = df[tgt].shift(lag)
        for w in ROLLING_WINDOWS:
            feat[f"{tgt}_roll{w}_mean"] = df[tgt].shift(1).rolling(w).mean()
            feat[f"{tgt}_roll{w}_std"]  = df[tgt].shift(1).rolling(w).std()
        feat[f"{tgt}_now"] = df[tgt]

    for c in EXTRA_FEATURES:
        if c not in df.columns:
            continue
        feat[f"{c}_now"] = df[c]
        for lag in EXTRA_LAGS:
            feat[f"{c}_lag{lag}"] = df[c].shift(lag)
        for w in EXTRA_ROLLS:
            feat[f"{c}_roll{w}_mean"] = df[c].shift(1).rolling(w).mean()

    dry = (df["precip"] < 0.1).astype(int)
    feat["days_since_rain"] = dry.groupby((dry == 0).cumsum()).cumsum()

    out = pd.concat([df.reset_index(drop=True),
                     pd.DataFrame(feat).reset_index(drop=True)], axis=1)
    return out.dropna().reset_index(drop=True)