<?php
$config = require __DIR__ . '/../config.php';
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title><?= htmlspecialchars($config['app_title']) ?></title>
    <link rel="stylesheet" href="assets/style.css">
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
</head>
<body>

<header>
    <h1>☀️ <?= htmlspecialchars($config['app_title']) ?></h1>
    <p class="subtitle">Will it rain tomorrow? Enter the last 14 days of weather and find out.</p>
</header>

<main>
    <div id="live-status" class="live-status hidden"></div>

    <section class="card">
        <div class="toolbar">
            <button type="button" id="btn-live">🌐 Load Last 14 Days (Live)</button>
            <button type="button" id="btn-clear">Clear All</button>
            <label class="model-select">
                Model:
                <select id="model-select">
                    <option value="both" selected>Both (compare)</option>
                    <option value="rf">🌳 Random Forest</option>
                    <option value="gb">🚀 Gradient Boosting</option>
                </select>
            </label>
        </div>

        <form id="input-form">
            <div class="table-wrap">
                <table id="input-table">
                    <thead>
                        <tr>
                            <th>Date</th>
                            <th>Temp (°C)</th>
                            <th>Humidity (%)</th>
                            <th>Precip (mm)</th>
                            <th>Wind (km/h)</th>
                            <th>Pressure (hPa)</th>
                            <th>Cloud (%)</th>
                        </tr>
                    </thead>
                    <tbody></tbody>
                </table>
            </div>

            <div class="actions">
                <button type="submit" id="btn-predict">🔮 Predict Next 7 Days</button>
            </div>
        </form>

        <div id="error-box" class="error-box hidden"></div>
    </section>

    <section id="results" class="hidden">
        <div class="results-header">
            <h2>7-Day Forecast</h2>
            <div class="results-actions">
                <button type="button" id="btn-download" class="btn-secondary">⬇ Download CSV</button>
            </div>
        </div>
        <p id="results-meta" class="meta"></p>
        <div id="forecast-view"></div>
    </section>
</main>

<footer class="attribution">
    Weather data by <a href="https://open-meteo.com/" target="_blank" rel="noopener">Open-Meteo.com</a> (CC BY 4.0)
</footer>

<script>
    window.APP_CONFIG = {
        minDays: <?= (int)$config['min_days'] ?>,
        maxDays: <?= (int)$config['max_days'] ?>
    };
</script>
<script src="assets/script.js?v=3"></script>
</body>
</html>