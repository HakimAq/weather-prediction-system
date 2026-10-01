# 🎤 5-Minute Demo Script — Kathmandu Weather Prediction System

## Pre-Demo Checklist (do this 10 minutes before)

- [ ] **Terminal 1** — Flask API running (`python app.py`)
- [ ] **Terminal 2** — PHP server running (`php -S localhost:8000 -t public`)
- [ ] **Browser** — tab open at `http://localhost:8000`
- [ ] **Browser** — DevTools closed (F12), so console isn't visible
- [ ] **Internet** — confirmed working (for live Open-Meteo fetch)
- [ ] **Fallback CSV** — confirmed at `ml/data/raw/`
- [ ] **Fresh copy of the CSV forecast** — for showing in Excel
- [ ] **Charts render** — pre-run one prediction so charts are cached

---

## The Demo (5 minutes)

### 🎬 Opening (30 seconds)

> "Good morning. My project is the **Kathmandu Weather Prediction System** —
> a full-stack web application that predicts the next 7 days of weather
> for Kathmandu using two ensemble machine learning algorithms.
>
> The system answers one question for the user: **'Will it rain tomorrow?'**
> — but it does so by training 14 separate models on 10 years of daily
> weather data."

---

### 🎬 Show the Input Form (45 seconds)

Point at the screen.

> "Here's the input form. The user needs to enter 14 days of weather history.
> Typing this manually would be painful — so I built a one-click live data
> loader that pulls real Kathmandu weather from Open-Meteo, a free weather
> archive API."

**Click: 🌐 Load Last 14 Days (Live)**

> "In one second, the form fills with the last 14 days of real Kathmandu
> weather — temperature, humidity, rainfall, wind, pressure, cloud cover.
>
> If the internet is down, the system automatically falls back to the last
> 14 rows of the training dataset — so my demo never fails."

---

### 🎬 Run the Prediction (20 seconds)

**Click: 🔮 Predict Next 7 Days**

> "Now I submit this to the PHP backend, which validates the input and
> forwards it to a Flask API running on port 5000. Flask loads 14 trained
> models — 7 for Random Forest, 7 for Gradient Boosting — and returns
> the forecast."

---

### 🎬 Walk Through the Results (90 seconds)

Point at the **hero card** at the top.

> "The first thing the user sees is **tomorrow's verdict**. For example:
> 'YES — it will rain, 72% chance.' That number is derived from the model's
> predicted precipitation, humidity, and cloud cover — presented as a
> confidence indicator for the user.
>
> Below it, an emoji summary — light wind, humid, comfortable temperature."

Point at the **7-day strip**.

> "The 7-day strip shows rain likelihood per day at a glance. Users can see
> at once which days will be dry and which will be rainy — no numbers to
> interpret."

Point at the **model comparison**.

> "Because I trained **two** algorithms, the system shows both side by side.
> Random Forest and Gradient Boosting rarely agree exactly — this comparison
> lets the user judge the forecast's reliability."

**Click: ▸ Show detailed numbers**

> "For technical users, one click reveals the full numerical tables and
> six charts — one per variable — showing both model trajectories."

---

### 🎬 Show the CSV Download (15 seconds)

**Click: ⬇ Download CSV**

> "The forecast can be downloaded as a CSV — ready for Excel or further
> analysis."

---

### 🎬 Technical Highlights (60 seconds)

Switch to talking points, no clicking.

> "Behind the scenes, three technical decisions matter most:
>
> **One — Direct multi-step forecasting.** I train 7 independent models,
> one per forecast horizon. This avoids the error compounding that plagues
> recursive forecasting, where day-7 errors can be 5x day-1 errors.
>
> **Two — Train/serve parity.** The inference module imports the exact same
> cleaning and feature-engineering functions used during training. This
> prevents train/serve skew — a classic production ML bug where the model
> sees different preprocessing at inference time than it saw in training.
>
> **Three — Decoupled architecture.** PHP handles the UI and validation,
> Python handles the ML, and they communicate over JSON. Each layer can
> be tested and replaced independently."

---

### 🎬 Known Limitations (30 seconds) — BE HONEST

> "Two limitations I want to be upfront about:
>
> **Precipitation is intrinsically hard to predict.** Kathmandu rainfall is
> heavily skewed — most days have zero, occasional monsoon days deliver
> over 100 mm. R² for precipitation is low, in the 0.0 to 0.3 range. This
> is normal for rainfall and reflects the chaotic nature of convective
> storms, not a failure of the model.
>
> **The training data ends June 2025 and represents a single station** —
> Tribhuvan International Airport. Spatial variability within the valley is
> significant; Sundarijal in the north gets twice the rainfall of Khumaltar
> in the center."

---

### 🎬 Closing (30 seconds)

> "In summary: this project demonstrates that standard ensemble learning
> algorithms, combined with careful feature engineering and a clean web
> architecture, can produce useful 7-day weather forecasts for Kathmandu.
>
> The system is fully functional, uses real live data, handles offline
> fallback gracefully, and presents results in a way that anyone — even
> a child — can understand at a glance.
>
> Thank you. I'm happy to take questions."

---

## Anticipated Questions & Answers

**Q: Why not use deep learning / LSTM?**
> For 3,400 rows of daily data, tree ensembles outperform deep networks.
> LSTMs need tens of thousands of samples to beat Random Forest on tabular
> time series. Given the dataset size, tree methods were the right choice.

**Q: Why two models and not just the best one?**
> Comparing two methods trained under identical conditions is standard
> practice in ML research. It gives the user a confidence signal —
> agreement between RF and GB suggests a reliable forecast, disagreement
> suggests uncertainty.

**Q: How do you prevent overfitting?**
> Three ways: (1) chronological 80/20 split, never shuffled, so the test
> set is strictly future data; (2) `min_samples_leaf=2` in RF and depth-4
> trees in GB, both restricting model complexity; (3) early stopping in
> GB via the `n_estimators` ceiling.

**Q: What's the Rain Chance % based on?**
> A weighted combination of predicted precipitation (60% weight),
> humidity above 60% (25% weight), and cloud cover (15% weight). It's a
> derived indicator, not a trained classifier — I present it as a
> confidence guide, not a calibrated probability.

**Q: How would you extend this?**
> Four directions: (1) add ENSO and Indian Ocean Dipole indices as
> exogenous features; (2) expand to a multi-station model covering the
> whole valley; (3) replace daily aggregates with hourly inputs for
> finer resolution; (4) replace the direct approach with a
> seq2seq deep model once the dataset grows.

**Q: Why PHP for the backend and not Node/Django?**
> PHP is ubiquitous in shared hosting, well-suited to form handling and
> templating, and doesn't require a Python runtime on the web server.
> Since the ML lives in Python, PHP only needs to do I/O and validation —
> which it does cleanly.

**Q: Why no database?**
> The application is stateless. Forecasts are generated on demand and not
> persisted — this is intentional. Adding a database would only be useful
> for logging predictions for later analysis, which is outside the scope
> of the current project.

---

## Troubleshooting (if something breaks during the demo)

| Symptom | Fix |
|---|---|
| Live fetch fails | Yellow banner appears, CSV fallback auto-fills — proceed normally |
| Predict button spins forever | Check Terminal 1 (Flask) — model may not be loaded |
| Charts don't render | Refresh page; Chart.js CDN might be blocked |
| Browser shows old JS | `Ctrl+Shift+R` hard refresh |
| Flask crashes | Restart Terminal 1: `python app.py` |

---

## Timing Summary

| Section | Time |
|---|---|
| Opening | 0:30 |
| Show input form + live load | 0:45 |
| Run prediction | 0:20 |
| Walk through results | 1:30 |
| CSV download | 0:15 |
| Technical highlights | 1:00 |
| Limitations | 0:30 |
| Closing | 0:30 |
| **Total** | **5:20** |

Trim the "Technical Highlights" section first if you're over time.