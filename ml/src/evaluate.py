import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

from .config import TARGETS, OUTPUT_DIR


def compute_metrics(y_true, y_pred, algo: str, horizon: int) -> list[dict]:
    rows = []
    for i, tgt in enumerate(TARGETS):
        yt, yp = y_true[:, i], y_pred[:, i]
        rows.append({
            "model":   algo,
            "horizon": horizon,
            "target":  tgt,
            "MSE":     mean_squared_error(yt, yp),
            "MAE":     mean_absolute_error(yt, yp),
            "R2":      r2_score(yt, yp),
        })
    return rows


def plot_heatmap(results_df: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    for ax, algo in zip(axes, ["RF", "GB"]):
        sub = results_df[results_df["model"] == algo]
        pivot = sub.pivot_table(index="horizon", columns="target", values="R2")
        im = ax.imshow(pivot.values, cmap="RdYlGn", vmin=0, vmax=1, aspect="auto")
        ax.set_xticks(range(len(pivot.columns)))
        ax.set_xticklabels(pivot.columns, rotation=45, ha="right")
        ax.set_yticks(range(len(pivot.index)))
        ax.set_yticklabels([f"t+{h}" for h in pivot.index])
        ax.set_title(f"{algo} — R² by horizon & target")
        for i in range(pivot.shape[0]):
            for j in range(pivot.shape[1]):
                ax.text(j, i, f"{pivot.values[i, j]:.2f}",
                        ha="center", va="center", fontsize=8)
    plt.colorbar(im, ax=axes, shrink=0.8)
    plt.tight_layout()
    out = OUTPUT_DIR / "r2_heatmap.png"
    plt.savefig(out, dpi=120)
    plt.close()
    print(f"\n📊 Heatmap saved to {out}")