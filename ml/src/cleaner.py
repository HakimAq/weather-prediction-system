from __future__ import annotations

import pandas as pd

from .config import TARGETS, DROP_COLS


PHYSICAL_BOUNDS = {
    "temp":             (-5.0,   42.0),
    "humidity":         (0.0,   100.0),
    "precip":           (0.0,   400.0),
    "windspeed":        (0.0,   180.0),
    "sealevelpressure": (950.0, 1050.0),
    "cloudcover":       (0.0,   100.0),
}

IQR_FACTOR = 3.0

FAHRENHEIT_COLS = ["temp", "tempmax", "tempmin", "dew"]


def _fahrenheit_to_celsius(df: pd.DataFrame) -> None:
    for c in FAHRENHEIT_COLS:
        if c in df.columns and df[c].max(skipna=True) > 45:
            df[c] = (df[c] - 32.0) * 5.0 / 9.0


def clean_data(df: pd.DataFrame, verbose: bool = True) -> pd.DataFrame:
    report = {}
    report["raw_rows"] = len(df)

    df = df.copy()
    df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")
    before = len(df)
    df = df.dropna(subset=["datetime"])
    report["bad_datetime_dropped"] = before - len(df)

    df = df.sort_values("datetime").reset_index(drop=True)

    before = len(df)
    df = df.drop_duplicates(subset="datetime", keep="last").reset_index(drop=True)
    report["duplicates_dropped"] = before - len(df)

    if "precipitation" in df.columns and "precip" not in df.columns:
        df = df.rename(columns={"precipitation": "precip"})

    drop = sorted(set(c for c in DROP_COLS if c in df.columns))
    df = df.drop(columns=drop, errors="ignore")
    report["columns_dropped"] = drop

    _fahrenheit_to_celsius(df)

    df = df.set_index("datetime").asfreq("D")
    report["missing_days_inserted"] = int(df[TARGETS].isna().all(axis=1).sum())

    for c in TARGETS:
        if c not in df.columns:
            raise ValueError(f"Required target column missing: {c}")
        df[c] = pd.to_numeric(df[c], errors="coerce")

    clip_counts = {}
    for c, (lo, hi) in PHYSICAL_BOUNDS.items():
        if c not in df.columns:
            continue
        mask = (df[c] < lo) | (df[c] > hi)
        clip_counts[c] = int(mask.sum())
        df[c] = df[c].clip(lower=lo, upper=hi)
    report["physical_clips"] = clip_counts

    iqr_counts = {}
    for c in TARGETS:
        if c == "precip":
            continue
        q1, q3 = df[c].quantile([0.25, 0.75])
        iqr = q3 - q1
        if iqr == 0:
            continue
        lo = q1 - IQR_FACTOR * iqr
        hi = q3 + IQR_FACTOR * iqr
        mask = (df[c] < lo) | (df[c] > hi)
        iqr_counts[c] = int(mask.sum())
        df[c] = df[c].clip(lower=lo, upper=hi)
    report["iqr_clips"] = iqr_counts

    before = int(df[TARGETS].isna().sum().sum())
    df[TARGETS] = (
        df[TARGETS]
        .interpolate(method="time", limit=3, limit_direction="both")
        .ffill()
        .bfill()
    )
    report["missing_values_imputed"] = before

    constant_cols = [
        c for c in df.columns
        if c != "datetime" and c not in TARGETS and df[c].nunique(dropna=False) <= 1
    ]
    if constant_cols:
        df = df.drop(columns=constant_cols)
    report["constant_columns_dropped"] = constant_cols

    df = df.reset_index()
    report["final_rows"] = len(df)

    if verbose:
        _print_report(report)

    return df


def _print_report(r: dict) -> None:
    print("\n" + "=" * 55)
    print("           DATA CLEANING REPORT")
    print("=" * 55)
    print(f"  Raw rows                          : {r['raw_rows']}")
    print(f"  Bad datetime rows dropped         : {r['bad_datetime_dropped']}")
    print(f"  Duplicate timestamps dropped      : {r['duplicates_dropped']}")
    print(f"  Columns dropped                   : {r['columns_dropped']}")
    print(f"  Missing days inserted (reindex)   : {r['missing_days_inserted']}")
    print(f"  Physical-bound clips              : {r['physical_clips']}")
    print(f"  IQR outlier clips                 : {r['iqr_clips']}")
    print(f"  Missing values imputed            : {r['missing_values_imputed']}")
    print(f"  Constant columns dropped          : {r['constant_columns_dropped']}")
    print(f"  Final rows                        : {r['final_rows']}")
    print("=" * 55 + "\n")