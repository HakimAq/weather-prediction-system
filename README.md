# 🌦️ Kathmandu Weather Prediction System

A full-stack weather forecasting web application that predicts six daily
weather variables for the next 7 days in Kathmandu, Nepal, using two
ensemble machine learning algorithms — **Random Forest** and **Gradient
Boosting**.

Users enter the last 14 days of observed weather (or click one button to
fetch real data from Open-Meteo), and the system returns:

- A **plain-language verdict** for tomorrow ("YES — it will rain, 72% chance")
- A **7-day visual strip** showing rain likelihood per day
- A side-by-side **model comparison**
- Full **numerical tables and charts** for technical users
- A **downloadable CSV** of the forecast

---

## 📋 Table of Contents

1. [Features](#features)
2. [Architecture](#architecture)
3. [Tech Stack](#tech-stack)
4. [Project Structure](#project-structure)
5. [Installation](#installation)
6. [Running the System](#running-the-system)
7. [Machine Learning Pipeline](#machine-learning-pipeline)
8. [API Reference](#api-reference)
9. [Known Limitations](#known-limitations)
10. [Credits](#credits)

---

## ✨ Features

### User-Facing
- **One-click live data load** from Open-Meteo (no API key required)
- **Offline fallback** to bundled historical CSV if the live API fails
- **Child-friendly verdict** — "Will it rain tomorrow?" answered in plain English
- **Rain chance %** derived from precipitation, humidity, and cloud cover
- **Weather emoji** per day (☀️ ⛅ 🌦️ 🌧️ ⛈️) for instant recognition
- **Day cards and comparison cards** for glanceable summaries
- **Toggle between Simple and Detailed views** (numbers + charts)
- **Download forecast as CSV** for Excel/Sheets

### Technical
- **Direct multi-step forecasting** — 7 independent models per algorithm, no recursive error propagation
- **Train/serve parity** — inference imports the exact same cleaning and feature engineering modules used during training
- **116 engineered features** — lags, rolling statistics, cyclical calendar encodings, monsoon flags
- **Two-tier comparison** — Random Forest vs Gradient Boosting trained under identical splits
- **14 saved models** (`rf_h1.pkl` … `rf_h7.pkl`, `gb_h1.pkl` … `gb_h7.pkl`)

---

## 🏗️ Architecture

Three-tier decoupled architecture:

```
┌──────────────────┐   HTTP+JSON   ┌──────────────────┐   HTTP+JSON   ┌──────────────────┐
│  Browser UI      │ ────────────▶ │  PHP Backend     │ ────────────▶ │  Flask ML API    │
│  HTML/CSS/JS     │               │  Validation      │               │  Inference       │
│  Chart.js        │ ◀──────────── │  cURL            │ ◀──────────── │  14 models       │
└──────────────────┘               └──────────────────┘               └──────────────────┘
                                                                            │
                                                                            ▼ (offline, one-time)
                                                                   ┌──────────────────┐
                                                                   │  Training        │
                                                                   │  Pipeline        │
                                                                   │  (Python)        │
                                                                   └──────────────────┘
```

**Why this design?**
- PHP has no mature ML libraries → Python handles all ML
- The Flask API is **stateless** — easy to test and debug
- The **same cleaning + feature code** runs at training and inference → prevents train/serve skew
- Layers can be developed, tested, and swapped independently

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| ML training | Python 3.10+, pandas, numpy, scikit-learn, joblib, matplotlib | Train and evaluate models |
| ML serving | Flask 3.x | HTTP inference API |
| Web backend | PHP 8.x (built-in server) | Form handling, validation, cURL proxy |
| Frontend | HTML5, CSS3, vanilla JS, Chart.js (CDN) | UI and visualizations |
| Live data | Open-Meteo (CC BY 4.0) | Free weather archive API |
| Communication | HTTP + JSON | Between all tiers |

---

## 📁 Project Structure

```
weather-prediction-system/
│
├── README.md                          ← this file
│
├── ml/                                # 🐍 Machine Learning pipeline
│   ├── data/raw/
│   │   └── TIA-WEATHER-DATA-2015-01-01-TO-2025-06-30.csv
│   ├── models/                        # Trained artifacts
│   │   ├── rf_h1.pkl … rf_h7.pkl
│   │   ├── gb_h1.pkl … gb_h7.pkl
│   │   ├── feature_columns.pkl
│   │   ├── target_columns.pkl
│   │   ├── climate_lookup.csv         # Day-of-year medians for extra features
│   │   └── metrics.csv
│   ├── outputs/
│   │   └── r2_heatmap.png
│   ├── src/
│   │   ├── __init__.py
│   │   ├── config.py                  # Paths, targets, hyperparameters
│   │   ├── cleaner.py                 # 9-step cleaning pipeline
│   │   ├── data_loader.py             # CSV → cleaner
│   │   ├── feature_engineering.py     # 116 features
│   │   ├── train.py                   # Training entry point
│   │   ├── evaluate.py                # Metrics + heatmap
│   │   └── inference.py               # Prediction logic
│   ├── build_climate_lookup.py
│   ├── test_inference.py
│   └── requirements.txt
│
├── api/                               # ⚡ Flask API
│   ├── app.py                         # /health, /predict
│   ├── test_api.py
│   └── requirements.txt
│
└── backend/                           # 🐘 PHP web app
    ├── config.php
    ├── src/
    │   ├── Validator.php              # Input validation
    │   ├── WeatherApiClient.php       # cURL wrapper for Flask
    │   └── LiveDataFetcher.php        # Open-Meteo + CSV fallback
    └── public/
        ├── index.php                  # Form UI
        ├── predict.php                # JSON endpoint → Flask
        ├── fetch_live.php             # JSON endpoint → Open-Meteo
        └── assets/
            ├── style.css
            └── script.js
```

---

## ⚙️ Installation

### Prerequisites

- **Python 3.10+** — https://www.python.org/downloads/
- **PHP 8.x (Thread Safe)** — https://windows.php.net/download/
- **Windows** (Linux/macOS work with equivalent commands)

### Step 1 — Clone / copy the project

Place the `weather-prediction-system/` folder anywhere on disk.

### Step 2 — Set up Python environment

```powershell
cd weather-prediction-system\ml
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
pip install flask flask-cors requests
```

### Step 3 — Place the training CSV

Put `TIA-WEATHER-DATA-2015-01-01-TO-2025-06-30.csv` in `ml\data\raw\`.

### Step 4 — Enable PHP cURL extension

Edit `C:\php\php.ini` and uncomment:

```ini
extension=curl
extension=openssl
```

Verify:

```powershell
php -m | findstr curl
```

Should output `curl`.

---

## ▶️ Running the System

You need **three terminals** running simultaneously.

### Terminal 1 — Flask ML API

```powershell
cd C:\weather-prediction-system\api
C:\weather-prediction-system\ml\.venv\Scripts\python.exe app.py
```

Should print:
```
INFO:src.inference: Loaded 7 RF + 7 GB models
* Running on http://127.0.0.1:5000
```

### Terminal 2 — PHP web server

```powershell
cd C:\weather-prediction-system\backend
php -S localhost:8000 -t public
```

Should print:
```
PHP Development Server (http://localhost:8000) started
```

### Terminal 3 — Browser

Open **http://localhost:8000**

Workflow:
1. Click **🌐 Load Last 14 Days (Live)** → form auto-fills
2. Click **🔮 Predict Next 7 Days**
3. Read the verdict, explore the 7-day strip, download CSV

---

## 🧠 Machine Learning Pipeline

### Data

- **Source:** Visual Crossing export for Tribhuvan International Airport (TIA), Kathmandu
- **Period:** 2015-01-01 → 2025-06-30
- **Rows:** 3,468 daily records (some years partial)
- **Targets:** `temp (°C)`, `humidity (%)`, `precip (mm)`, `windspeed (km/h)`, `sealevelpressure (hPa)`, `cloudcover (%)`

### Cleaning (9 steps)

1. Parse datetime and sort chronologically
2. Drop duplicate timestamps
3. Rename/drop irrelevant columns (sunrise, sunset, severerisk, preciptype)
4. Unit conversion — Fahrenheit → Celsius
5. Reindex to continuous daily frequency
6. Coerce all targets to numeric
7. Physical-bound clipping (e.g. temp ∈ [−5, 42] °C)
8. IQR outlier clipping — **skipped for precipitation** to preserve monsoon extremes
9. Time-aware interpolation for missing days

### Feature Engineering (116 features)

Per target (× 6 targets):
- Current value
- Lags at 1, 2, 3, 7 days
- Rolling mean and std over 3 and 7 days, shifted by 1 to prevent leakage

Extra inputs (`dew`, `tempmax`, `tempmin`, `windgust`, `winddir`, `visibility`, `solarradiation`, `solarenergy`, `uvindex`, `precipprob`, `precipcover`):
- Current value
- Lags at 1 and 7 days
- Rolling-7 mean

Calendar features:
- `day_of_year`, `month`, `day_of_week`
- `sin_doy`, `cos_doy` — cyclical encoding
- `is_monsoon` — binary (June–September)
- `days_since_rain` — dry-spell counter

### Multi-Step Strategy: **Direct Forecasting**

Two approaches exist:
- **Recursive:** train one model for t+1, feed outputs back — errors compound badly
- **Direct (used here):** train 7 independent models, one per horizon — no error propagation

### Models

**Random Forest** (Breiman, 2001)
- 300 trees, `min_samples_leaf=2`
- Natively multi-output — predicts all 6 targets in one `.predict()`
- **7 models** (`rf_h1.pkl` … `rf_h7.pkl`)

**Gradient Boosting** (Friedman, 2001)
- 300 estimators, learning rate 0.05, max depth 4, subsample 0.9
- **Does not natively support multi-output** → wrapped in `MultiOutputRegressor` (6 GB models per horizon, one per target)
- **7 wrapped models** (`gb_h1.pkl` … `gb_h7.pkl`)

### Training

```powershell
cd ml
python -m src.train
```

Outputs to `ml/models/`:
- 14 `.pkl` files
- `feature_columns.pkl`, `target_columns.pkl`
- `metrics.csv`
- `ml/outputs/r2_heatmap.png`

### Evaluation

For every model × horizon × target:
- **MSE** — Mean Squared Error
- **MAE** — Mean Absolute Error
- **R²** — coefficient of determination

Typical R² (from training):
| Target | R² (approx) | Notes |
|---|---|---|
| Temperature | 0.85–0.95 | Strongly seasonal |
| Humidity | 0.75–0.90 | |
| Sea-Level Pressure | 0.80–0.92 | |
| Cloud Cover | 0.45–0.65 | |
| Wind Speed | 0.30–0.55 | |
| **Precipitation** | **0.00–0.30** | Genuinely hard — skewed distribution |

---

## 🔌 API Reference

### Flask API (`http://localhost:5000`)

#### `GET /health`

```json
{
  "status": "ok",
  "models_loaded": true,
  "service": "kathmandu-weather-api"
}
```

#### `POST /predict`

**Request body:**

```json
{
  "history": [
    {
      "datetime": "2025-06-17",
      "temp": 20.0,
      "humidity": 75.0,
      "precip": 0.0,
      "windspeed": 9.0,
      "sealevelpressure": 1008.0,
      "cloudcover": 40.0
    }
    /* ...at least 14 days... */
  ],
  "model": "both"
}
```

`model` ∈ `"rf"`, `"gb"`, `"both"`.

**Response:**

```json
{
  "status": "success",
  "location": "Kathmandu",
  "input_days": 14,
  "last_input_date": "2025-06-30",
  "forecast": {
    "random_forest": [
      { "day": 1, "date": "2025-07-01", "temp": 23.73, "humidity": 80.05, ... }
      /* ...7 days... */
    ],
    "gradient_boosting": [ /* ...7 days... */ ]
  }
}
```

**Errors:** `400` for validation, `500` for server issues.

### PHP Backend (`http://localhost:8000`)

| Endpoint | Method | Purpose |
|---|---|---|
| `/` | GET | Form UI |
| `/predict.php` | POST | Validates + forwards to Flask |
| `/fetch_live.php` | GET | Fetches last 14 days from Open-Meteo (with CSV fallback) |

---

## ⚠️ Known Limitations

1. **Precipitation is intrinsically difficult.** Kathmandu rainfall is heavily skewed — most days are dry, occasional monsoon days deliver 100+ mm. R² is low. This is expected and reflects the chaotic nature of convective rainfall, not a model failure.

2. **Data ends June 2025.** Forecasts are valid for patterns within that climate regime.

3. **Single-station training.** The TIA records represent the airport, not the entire valley. Sundarijal (Mulkharka) receives roughly twice the annual rainfall of Khumaltar.

4. **No exogenous variables.** ENSO, Indian Ocean Dipole, and other large-scale circulation indices are not used — future work.

5. **Daily resolution only.** No hourly nowcasting.

6. **Rain Chance % is a derived indicator, not a calibrated probability.** It combines predicted precipitation, humidity, and cloud cover heuristically. It's intended as a confidence guide for end users, not a strict statistical probability.

7. **No database.** The application is fully stateless — nothing is persisted between requests. Suitable for a demonstration and small-scale use.

---

## 🎓 Credits

- **Dataset:** Visual Crossing weather API export (TIA station)
- **Live data:** [Open-Meteo](https://open-meteo.com/) (CC BY 4.0)
- **Algorithms:**
  - Breiman, L. (2001). *Random Forests*. Machine Learning, 45(1), 5–32.
  - Friedman, J. H. (2001). *Greedy function approximation: A gradient boosting machine*. Annals of Statistics, 29(5), 1189–1232.
- **Multi-step theory:** Taieb, S. B. et al. (2012). *A review and comparison of strategies for multi-step ahead time series forecasting*. Expert Systems with Applications, 39(8), 7067–7083.
- **Regional rainfall context:** Bhattarai, S., Bagale, D., & Shrestha, S. (2025). *Rainfall variability in Kathmandu Valley, Nepal*. Scientific World, 18(18).

---

## 📄 License

This project was developed as a final-year undergraduate project. Free to use for academic and educational purposes.