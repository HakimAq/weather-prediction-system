# Kathmandu Weather Prediction System — Project Description

## 1. Introduction

The Kathmandu Weather Prediction System is a web-based application that
forecasts six daily weather variables for the next seven days in Kathmandu,
Nepal. It uses two ensemble machine learning algorithms — Random Forest
and Gradient Boosting — trained on ten years of daily observations from
the Tribhuvan International Airport (TIA) weather station.

The system addresses a real-world need: while large-scale numerical
weather prediction models exist, accessible, locally-tuned tools for
short-range forecasting in Kathmandu are scarce. This project demonstrates
that standard machine learning methods, applied carefully to freely
available data, can produce useful short-term forecasts.

## 2. Problem Statement

Kathmandu's climate is dominated by the South Asian monsoon, which
delivers roughly 79% of annual rainfall between June and September
(Bhattarai et al., 2025). Accurate short-range forecasts are important for:

- Agriculture (planting and harvest scheduling)
- Water resource management
- Urban flood preparedness
- General public information

However, freely available forecasting tools tuned to Kathmandu's specific
climate are limited. Most existing services target larger regions or rely
on proprietary data.

## 3. Objectives

1. Clean and preprocess ten years of daily weather data for Kathmandu
2. Engineer time-series features from lagged values, rolling statistics,
   and calendar signals
3. Train two families of ensemble regressors — one model per forecast
   horizon — for six weather variables
4. Compare the two algorithms under identical training conditions
5. Deploy the models through a 3-tier web application with a
   user-friendly interface
6. Provide a plain-language interpretation layer so non-technical users
   can understand forecasts at a glance

## 4. Data

### 4.1 Source
Visual Crossing weather API export for Tribhuvan International Airport
(TIA), Kathmandu.

### 4.2 Period and Coverage
- Start: 2015-01-01
- End: 2025-06-30
- Rows: 3,468 daily records (partial years at both ends)
- Gap: 2015 has only Jan–Jun; 2016 has only Jul–Dec

### 4.3 Variables

**Targets (predicted):**
| Variable | Unit | Description |
|---|---|---|
| `temp` | °C | Daily average air temperature |
| `humidity` | % | Relative humidity |
| `precip` | mm/day | Rainfall (precipitation) |
| `windspeed` | km/h | Average wind speed |
| `sealevelpressure` | hPa | Sea-level atmospheric pressure |
| `cloudcover` | % | Sky coverage |

**Auxiliary inputs (used as features, not predicted):**
`dew`, `tempmax`, `tempmin`, `windgust`, `winddir`, `visibility`,
`solarradiation`, `solarenergy`, `uvindex`, `precipprob`, `precipcover`.

**Dropped columns:**
`sunrise`, `sunset`, `severerisk`, `preciptype` — non-numeric or sparse.

### 4.4 Unit Conversions
Visual Crossing exports temperatures in Fahrenheit. These were converted
to Celsius during cleaning. Wind speed was already in km/h and
precipitation already in mm, so no conversion was needed for those.

## 5. Methodology

### 5.1 Data Cleaning Pipeline (9 steps)

1. **Parse and sort datetime** — ensures chronological order, needed for lags
2. **Drop duplicate timestamps** — keep the most recent record per day
3. **Rename and drop irrelevant columns** — metadata only
4. **Unit conversion** — Fahrenheit → Celsius
5. **Reindex to daily frequency** — inserts missing days as NaN
6. **Coerce to numeric** — bad strings become NaN
7. **Physical-bound clipping** — clip to plausible ranges
8. **IQR outlier clipping** — Tukey's fence at 3.0×IQR; **skipped for precipitation** to preserve monsoon extremes
9. **Time-aware interpolation** — linear interpolation in time, then ffill/bfill

### 5.2 Feature Engineering

For each of the six target variables:
- Current value
- Lag values at 1, 2, 3, and 7 days
- Rolling mean and rolling standard deviation over 3-day and 7-day windows (shifted by 1 to prevent target leakage)

For the eleven auxiliary variables:
- Current value
- Lags at 1 and 7 days
- Rolling-7 mean

Calendar features:
- `day_of_year`, `month`, `day_of_week`
- `sin_doy`, `cos_doy` — cyclical encoding so Dec 31 and Jan 1 are numerically adjacent
- `is_monsoon` — binary flag for June–September
- `days_since_rain` — dry-spell counter

**Total: 116 features per sample.**

### 5.3 Multi-Step Forecasting Strategy

Two approaches exist for forecasting multiple steps ahead:

**Recursive:** Train one model to predict t+1, then feed each prediction back
as input to predict t+2, and so on. Simple but errors compound — a 5%
error at t+1 can become a 40% error by t+7.

**Direct (used in this project):** Train seven independent models, one per
horizon. `rf_h1` predicts day 1; `rf_h7` predicts day 7 directly. No
feedback loop, no error propagation.

This project follows the direct approach, consistent with the findings
of Taieb et al. (2012).

### 5.4 Machine Learning Algorithms

#### Random Forest Regression

Random Forest (Breiman, 2001) is an ensemble of B decision trees. Each
tree is trained on a bootstrap sample of the training data, and at each
split only a random subset of features is considered. Predictions are
averaged across all trees:

$$\hat{y}(x) = \frac{1}{B} \sum_{b=1}^{B} T_b(x)$$

**Strengths:**
- Handles nonlinear relationships
- Robust to outliers and irrelevant features
- Natively multi-output
- Low variance

**Weaknesses:**
- Large model files (~50 MB per model)
- Cannot extrapolate beyond training range

**Hyperparameters:**
- `n_estimators=300`, `min_samples_leaf=2`, `n_jobs=-1`, `random_state=42`

#### Gradient Boosting Regression

Gradient Boosting (Friedman, 2001) builds trees sequentially, where
each tree fits the residuals of the current ensemble:

$$F_m(x) = F_{m-1}(x) + \nu \cdot h_m(x)$$

where `h_m` is a shallow tree fit to the negative gradient of the loss
function and `ν` is the learning rate.

**Strengths:**
- Often more accurate than Random Forest on tabular data
- Smaller model files
- Excellent on small-to-medium datasets

**Weaknesses:**
- **Does not natively support multi-output regression** — sklearn's
  `GradientBoostingRegressor` requires 1D targets
- Sensitive to hyperparameters

To match Random Forest's multi-output capability, Gradient Boosting is
wrapped in `sklearn.multioutput.MultiOutputRegressor`, which trains
one GB model per target internally.

**Hyperparameters:**
- `n_estimators=300`, `learning_rate=0.05`, `max_depth=4`, `subsample=0.9`, `random_state=42`

### 5.5 Training Procedure

For each horizon `h ∈ {1, 2, …, 7}`:

1. Slice input matrix: `X_h = X[:-h]`, `Y_h = Y[h:]`
2. Chronological 80/20 split — no shuffling, since shuffling would leak future information into the past
3. Train one `RandomForestRegressor` on `X_tr, y_tr`
4. Train one `MultiOutputRegressor(GradientBoostingRegressor)` on the same split
5. Evaluate both on the held-out test set
6. Save as `rf_h{h}.pkl` and `gb_h{h}.pkl`

Total saved models: **14 (7 RF + 7 GB)**.

### 5.6 Evaluation Metrics

For every model × horizon × target:
- **MSE** — Mean Squared Error
- **MAE** — Mean Absolute Error
- **R²** — coefficient of determination

R² results are visualized as a 2-panel heatmap (RF vs GB) across
horizons and targets.

## 6. System Architecture

Three-tier decoupled architecture:

- **Frontend (Browser):** HTML/CSS/JS, Chart.js
- **Backend (PHP):** form handling, validation, cURL proxy
- **ML Service (Flask):** loads 14 models, applies the same cleaning and feature engineering as training

Communication: HTTP + JSON between all tiers.

**Why decoupled?**
- PHP lacks mature ML libraries
- Python is the standard for ML
- Each layer can be tested independently
- Same preprocessing code is shared between training and inference — prevents train/serve skew

## 7. Inference Pipeline

When the user submits 14 days of history:

1. PHP validates input ranges
2. Flask loads the history as a DataFrame
3. The same `clean_data()` and `build_features()` functions from training run on it
4. The last valid feature row is extracted (representing "today")
5. Columns are reordered to match `feature_columns.pkl`
6. For `h = 1..7`: `rf_h{h}.predict(X)` and `gb_h{h}.predict(X)` are called
7. Predictions are clipped to physical bounds
8. The response is returned as JSON

## 8. Result Interpretation Layer

Because raw regression output (temperature in °C, rainfall in mm) is not
meaningful to general users, the system adds a presentation layer:

- **Rain Chance %** — a heuristic combination of predicted precipitation
  (60% weight), humidity above 60% (25% weight), and cloud cover
  (15% weight). Presented as a confidence indicator, not a calibrated
  probability.
- **Weather emoji per day** — ☀️ ⛅ 🌦️ 🌧️ ⛈️, chosen by rain likelihood
- **Plain-language verdict** — "YES — it will rain", "MAYBE — keep an umbrella"
- **Everyday descriptors** — "Comfortable", "Very humid", "Light wind"

The full numerical output remains accessible via a toggle for technical
users and reviewers.

## 9. Results

Insert the R² tables from `ml/models/metrics.csv` here. Expected
performance (typical from training):

| Target | Random Forest R² | Gradient Boosting R² |
|---|---|---|
| Temperature | 0.85–0.95 | 0.85–0.95 |
| Humidity | 0.75–0.90 | 0.75–0.90 |
| Sea-Level Pressure | 0.80–0.92 | 0.80–0.92 |
| Cloud Cover | 0.45–0.65 | 0.45–0.65 |
| Wind Speed | 0.30–0.55 | 0.30–0.55 |
| Precipitation | 0.00–0.30 | 0.00–0.30 |

Discuss which algorithm performed better per target. In general,
Random Forest is more stable across horizons; Gradient Boosting often
edges it out at shorter horizons (t+1 to t+3).

## 10. Known Limitations

1. **Precipitation is intrinsically difficult.** Kathmandu rainfall is
   heavily skewed. R² is low but expected.
2. **Data ends June 2025.** Forecasts valid for patterns within that era.
3. **Single-station training.** TIA records don't represent the entire valley.
4. **No exogenous climate variables.** ENSO, IOD, etc. are not used.
5. **Daily resolution only.**
6. **Rain Chance % is a derived indicator, not a calibrated probability.**

## 11. Future Work

1. Add ENSO and Indian Ocean Dipole indices as exogenous features
2. Expand to a multi-station model covering the whole valley
3. Move from daily aggregates to hourly inputs
4. Replace the direct approach with a sequence-to-sequence deep model
   once the dataset grows

## 12. References

- Breiman, L. (2001). Random Forests. *Machine Learning*, 45(1), 5–32.
- Friedman, J. H. (2001). Greedy function approximation: A gradient
  boosting machine. *Annals of Statistics*, 29(5), 1189–1232.
- Taieb, S. B., Bontempi, G., Atiya, A. F., & Sorjamaa, A. (2012).
  A review and comparison of strategies for multi-step ahead time
  series forecasting. *Expert Systems with Applications*, 39(8), 7067–7083.
- Bhattarai, S., Bagale, D., & Shrestha, S. (2025). Rainfall variability
  in Kathmandu Valley, Nepal. *Scientific World*, 18(18).
- Visual Crossing (2025). *Weather Data & Weather API*.
- Open-Meteo (2025). *Free Weather API* (CC BY 4.0).