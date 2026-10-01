import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.multioutput import MultiOutputRegressor

from .config import (
    TARGETS, FORECAST_HORIZON, TEST_SPLIT,
    RF_PARAMS, GB_PARAMS, MODEL_DIR,
)
from .data_loader import load_raw_data
from .feature_engineering import build_features
from .evaluate import compute_metrics, plot_heatmap


def _make_gb():
    return MultiOutputRegressor(GradientBoostingRegressor(**GB_PARAMS))


def main() -> None:
    print("Loading data...")
    df = load_raw_data()
    print(f"  Raw shape: {df.shape}")

    print("Engineering features...")
    df = build_features(df)
    print(f"  After feature engineering: {df.shape}")

    feature_cols = [c for c in df.columns if c not in ["datetime"] + TARGETS]
    X_all = df[feature_cols].values.astype(np.float64)
    Y_all = df[TARGETS].values.astype(np.float64)

    print(f"  Features: {len(feature_cols)} | Samples: {len(X_all)}")

    joblib.dump(feature_cols, MODEL_DIR / "feature_columns.pkl")
    joblib.dump(TARGETS,      MODEL_DIR / "target_columns.pkl")

    all_metrics = []

    for h in range(1, FORECAST_HORIZON + 1):
        print(f"\n=== Horizon t+{h} ===")

        X_h = X_all[:-h]
        Y_h = Y_all[h:]

        split = int(len(X_h) * (1 - TEST_SPLIT))
        X_tr, X_te = X_h[:split], X_h[split:]
        y_tr, y_te = Y_h[:split], Y_h[split:]

        rf = RandomForestRegressor(**RF_PARAMS).fit(X_tr, y_tr)
        gb = _make_gb().fit(X_tr, y_tr)

        rf_pred = rf.predict(X_te)
        gb_pred = np.asarray(gb.predict(X_te))
        if gb_pred.ndim == 1:
            gb_pred = gb_pred.reshape(-1, len(TARGETS))

        rf_metrics = compute_metrics(y_te, rf_pred, "RF", h)
        gb_metrics = compute_metrics(y_te, gb_pred, "GB", h)
        all_metrics += rf_metrics + gb_metrics

        print("  RF R2: " + " | ".join(f"{m['target']}={m['R2']:.3f}" for m in rf_metrics))
        print("  GB R2: " + " | ".join(f"{m['target']}={m['R2']:.3f}" for m in gb_metrics))

        joblib.dump(rf, MODEL_DIR / f"rf_h{h}.pkl")
        joblib.dump(gb, MODEL_DIR / f"gb_h{h}.pkl")

    results_df = pd.DataFrame(all_metrics)
    results_df.to_csv(MODEL_DIR / "metrics.csv", index=False)

    print("\n============================================")
    print("           FINAL METRICS SUMMARY (R²)")
    print("============================================")
    for algo in ["RF", "GB"]:
        print(f"\n--- {algo} ---")
        pivot = results_df[results_df["model"] == algo].pivot_table(
            index="horizon", columns="target", values="R2"
        )
        print(pivot.round(3))

    plot_heatmap(results_df)

    print(f"\n✅ All models + metrics saved to '{MODEL_DIR}/'")


if __name__ == "__main__":
    main()