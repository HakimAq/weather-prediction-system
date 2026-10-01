import pandas as pd

from src.config import MODEL_DIR
from src.data_loader import load_raw_data


def main() -> None:
    df = load_raw_data(verbose=False)
    climate = (
        df.assign(doy=df["datetime"].dt.dayofyear)
          .groupby("doy")[["dew", "tempmax", "tempmin", "windgust", "winddir",
                           "visibility", "solarradiation", "solarenergy",
                           "uvindex", "precipprob", "precipcover"]]
          .median()
    )
    out = MODEL_DIR / "climate_lookup.csv"
    climate.to_csv(out)
    print(f"✅ Saved {len(climate)} rows to {out}")


if __name__ == "__main__":
    main()