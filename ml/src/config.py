from pathlib import Path

ROOT_DIR   = Path(__file__).resolve().parents[1]
DATA_DIR   = ROOT_DIR / "data" / "raw"
MODEL_DIR  = ROOT_DIR / "models"
OUTPUT_DIR = ROOT_DIR / "outputs"

DATA_FILE = DATA_DIR / "TIA-WEATHER-DATA-2015-01-01-TO-2025-06-30.csv"

MODEL_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

TARGETS = ["temp", "humidity", "precip",
           "windspeed", "sealevelpressure", "cloudcover"]

FORECAST_HORIZON = 7
LAGS             = [1, 2, 3, 7]
ROLLING_WINDOWS  = [3, 7]

DROP_COLS = ["conditions", "description", "icon", "preciptype",
             "stations", "sunrise", "sunset", "severerisk"]

TEST_SPLIT   = 0.20
RANDOM_STATE = 42

RF_PARAMS = dict(
    n_estimators=300,
    min_samples_leaf=2,
    n_jobs=-1,
    random_state=RANDOM_STATE,
)

GB_PARAMS = dict(
    n_estimators=300,
    learning_rate=0.05,
    max_depth=4,
    subsample=0.9,
    random_state=RANDOM_STATE,
)

DROP_COLS = ["conditions", "description", "icon", "preciptype",
             "stations", "sunrise", "sunset",
             "severerisk"]