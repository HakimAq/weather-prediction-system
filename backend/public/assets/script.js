// =========================================================================
// CONFIG
// =========================================================================
const TARGETS = [
    { key: 'temp',             label: 'Temperature',        unit: '°C'   },
    { key: 'humidity',         label: 'Humidity',           unit: '%'    },
    { key: 'precip',           label: 'Precipitation',      unit: 'mm'   },
    { key: 'windspeed',        label: 'Wind Speed',         unit: 'km/h' },
    { key: 'sealevelpressure', label: 'Sea-Level Pressure', unit: 'hPa'  },
    { key: 'cloudcover',       label: 'Cloud Cover',        unit: '%'    },
];

const MODEL_LABELS = {
    random_forest:     '🌳 Random Forest',
    gradient_boosting: '🚀 Gradient Boosting',
};

// =========================================================================
// DOM REFS
// =========================================================================
const tbody        = document.querySelector('#input-table tbody');
const form         = document.querySelector('#input-form');
const btnPredict   = document.querySelector('#btn-predict');
const btnLive      = document.querySelector('#btn-live');
const btnClear     = document.querySelector('#btn-clear');
const btnDownload  = document.querySelector('#btn-download');
const errorBox     = document.querySelector('#error-box');
const liveStatus   = document.querySelector('#live-status');
const results      = document.querySelector('#results');
const forecastView = document.querySelector('#forecast-view');

// =========================================================================
// STATE
// =========================================================================
let chartInstances = [];
let currentView    = 'simple';
let latestForecast = null;

// =========================================================================
// DATE HELPERS
// =========================================================================
function isoDate(d) { return d.toISOString().slice(0, 10); }

function shortDate(iso) {
    const d   = new Date(iso + 'T00:00:00');
    const day = ['Sun','Mon','Tue','Wed','Thu','Fri','Sat'][d.getDay()];
    const mon = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'][d.getMonth()];
    return `${day}, ${mon} ${d.getDate()}`;
}

function shortDayName(iso) {
    const d = new Date(iso + 'T00:00:00');
    return ['Sun','Mon','Tue','Wed','Thu','Fri','Sat'][d.getDay()];
}

// =========================================================================
// INTERPRETATION HELPERS
// =========================================================================
function rainChance(precip, humidity, cloud) {
    const p = Math.min(precip / 15, 1) * 60;
    const h = Math.max((humidity - 60) / 40, 0) * 25;
    const c = (cloud / 100) * 15;
    return Math.min(Math.round(p + h + c), 95);
}

function rainVerdict(pct) {
    if (pct < 15) return { say: 'NO — it will be dry',      emoji: '☀️', cls: 'verdict-dry'   };
    if (pct < 35) return { say: 'MAYBE — a small chance',   emoji: '⛅', cls: 'verdict-maybe' };
    if (pct < 60) return { say: 'MAYBE — keep an umbrella', emoji: '🌦️', cls: 'verdict-maybe' };
    if (pct < 80) return { say: 'YES — it will rain',       emoji: '🌧️', cls: 'verdict-rain'  };
    return              { say: 'YES — heavy rain expected', emoji: '⛈️', cls: 'verdict-storm' };
}

function simpleTemp(t) {
    if (t < 10) return 'Cold';
    if (t < 18) return 'Cool';
    if (t < 26) return 'Comfortable';
    if (t < 32) return 'Warm';
    return 'Hot';
}

function simpleHumidity(h) {
    if (h < 40) return 'Dry air';
    if (h < 60) return 'Nice air';
    if (h < 80) return 'Humid';
    return 'Very humid';
}

function simpleWind(w) {
    if (w < 5)  return 'No wind';
    if (w < 20) return 'Light wind';
    if (w < 40) return 'Windy';
    return 'Very windy';
}

// =========================================================================
// FORM BUILDING
// =========================================================================
function buildRows(n) {
    tbody.innerHTML = '';
    const start = new Date();
    start.setDate(start.getDate() - n);

    for (let i = 0; i < n; i++) {
        const d = new Date(start);
        d.setDate(start.getDate() + i + 1);
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td><input type="date" name="datetime" value="${isoDate(d)}"></td>
            <td><input type="number" step="0.1" name="temp"></td>
            <td><input type="number" step="0.1" name="humidity"></td>
            <td><input type="number" step="0.1" name="precip"></td>
            <td><input type="number" step="0.1" name="windspeed"></td>
            <td><input type="number" step="0.1" name="sealevelpressure"></td>
            <td><input type="number" step="0.1" name="cloudcover"></td>
        `;
        tbody.appendChild(tr);
    }
}

function clearAll() {
    tbody.querySelectorAll('input').forEach(el => {
        if (el.type !== 'date') el.value = '';
    });
}

function collectHistory() {
    const rows = [];
    tbody.querySelectorAll('tr').forEach(tr => {
        const row = {};
        tr.querySelectorAll('input').forEach(input => {
            row[input.name] = input.value;
        });
        rows.push(row);
    });
    return rows;
}

// =========================================================================
// STATUS MESSAGES
// =========================================================================
function showError(msg) {
    if (!errorBox) return;
    errorBox.innerHTML = msg;
    errorBox.classList.remove('hidden');
}

function hideError() {
    if (!errorBox) return;
    errorBox.classList.add('hidden');
    errorBox.innerHTML = '';
}

function showLiveStatus(msg, type) {
    if (!liveStatus) return;
    liveStatus.textContent = msg;
    liveStatus.className = 'live-status ' + (type || 'info');
    liveStatus.classList.remove('hidden');
}

function hideLiveStatus() {
    if (!liveStatus) return;
    liveStatus.classList.add('hidden');
}

// =========================================================================
// CHARTS
// =========================================================================
function destroyCharts() {
    chartInstances.forEach(c => c.destroy());
    chartInstances = [];
}

function renderCharts(forecast) {
    destroyCharts();
    const container = document.querySelector('#charts');
    if (!container) return;
    container.innerHTML = '';

    const modelKeys   = Object.keys(forecast);
    const modelColors = { random_forest: '#1e40af', gradient_boosting: '#dc2626' };
    const days        = forecast[modelKeys[0]].map(r => `t+${r.day}`);

    TARGETS.forEach(t => {
        const card = document.createElement('div');
        card.className = 'chart-card';
        card.innerHTML = `<h4>${t.label} (${t.unit})</h4><canvas></canvas>`;
        container.appendChild(card);

        const datasets = modelKeys.map(m => ({
            label: MODEL_LABELS[m] || m,
            data: forecast[m].map(r => r[t.key]),
            borderColor: modelColors[m] || '#333',
            backgroundColor: (modelColors[m] || '#333') + '22',
            tension: 0.35,
            fill: false,
        }));

        const chart = new Chart(card.querySelector('canvas'), {
            type: 'line',
            data: { labels: days, datasets },
            options: {
                responsive: true,
                plugins: { legend: { position: 'bottom' } },
                scales: { y: { beginAtZero: false } }
            }
        });
        chartInstances.push(chart);
    });
}

// =========================================================================
// SIMPLE VIEW
// =========================================================================
function renderSimpleView(forecast) {
    const models   = Object.keys(forecast);
    const primary  = forecast[models[0]];
    const tomorrow = primary[0];
    const rainPct  = rainChance(tomorrow.precip, tomorrow.humidity, tomorrow.cloudcover);
    const verdict  = rainVerdict(rainPct);

    let html = '';

    html += `
        <div class="hero ${verdict.cls}">
            <div class="hero-label">TOMORROW · ${shortDate(tomorrow.date)}</div>
            <div class="hero-emoji">${verdict.emoji}</div>
            <div class="hero-verdict">${verdict.say}</div>
            <div class="hero-chance">${rainPct}% chance of rain</div>
            <div class="hero-summary">
                ${simpleTemp(tomorrow.temp)} · ${simpleHumidity(tomorrow.humidity)} · ${simpleWind(tomorrow.windspeed)}
            </div>
        </div>
    `;

    html += '<h3 class="section-title">Next 7 days at a glance</h3>';
    html += '<div class="day-strip">';
    primary.forEach((row, idx) => {
        const pct   = rainChance(row.precip, row.humidity, row.cloudcover);
        const v     = rainVerdict(pct);
        const isTom = idx === 0;

        html += `
            <div class="strip-day ${v.cls} ${isTom ? 'strip-today' : ''}">
                <div class="strip-name">${isTom ? 'Tomorrow' : shortDayName(row.date)}</div>
                <div class="strip-emoji">${v.emoji}</div>
                <div class="strip-pct">${pct}%</div>
                <div class="strip-temp">${Math.round(row.temp)}°C</div>
            </div>
        `;
    });
    html += '</div>';

    html += '<h3 class="section-title">Both models agree?</h3>';
    html += '<div class="model-compare">';
    models.forEach(m => {
        const t        = forecast[m][0];
        const p        = rainChance(t.precip, t.humidity, t.cloudcover);
        const v        = rainVerdict(p);
        const rainDays = forecast[m].filter(r =>
            rainChance(r.precip, r.humidity, r.cloudcover) >= 60
        ).length;

        html += `
            <div class="compare-card">
                <div class="compare-model">${MODEL_LABELS[m] || m}</div>
                <div class="compare-emoji">${v.emoji}</div>
                <div class="compare-verdict">${v.say}</div>
                <div class="compare-meta">
                    <strong>${p}%</strong> rain tomorrow ·
                    <strong>${rainDays}</strong> of next 7 days rainy
                </div>
            </div>
        `;
    });
    html += '</div>';

    html += `
        <div class="details-toggle">
            <button type="button" id="btn-show-details">▸ Show detailed numbers</button>
        </div>
    `;

    return html;
}

// =========================================================================
// DETAILED VIEW
// =========================================================================
function renderDayCards(modelData) {
    let html = '<div class="day-cards">';
    modelData.forEach(row => {
        const pct  = rainChance(row.precip, row.humidity, row.cloudcover);
        const rain = rainVerdict(pct);

        html += `
            <div class="day-card">
                <div class="day-card-header">Day ${row.day} · ${shortDate(row.date)}</div>
                <div class="day-card-emoji">${rain.emoji}</div>
                <div class="day-card-summary">
                    <span class="rain-badge">${pct}% rain</span>
                </div>
                <div class="day-card-row"><span class="day-card-label">Temp</span><span class="day-card-value">${row.temp} °C</span></div>
                <div class="day-card-row"><span class="day-card-label">Humidity</span><span class="day-card-value">${row.humidity} %</span></div>
                <div class="day-card-row"><span class="day-card-label">Rainfall</span><span class="day-card-value">${row.precip} mm</span></div>
                <div class="day-card-row"><span class="day-card-label">Wind</span><span class="day-card-value">${row.windspeed} km/h</span></div>
                <div class="day-card-row"><span class="day-card-label">Pressure</span><span class="day-card-value">${row.sealevelpressure} hPa</span></div>
                <div class="day-card-row"><span class="day-card-label">Cloud</span><span class="day-card-value">${row.cloudcover} %</span></div>
            </div>
        `;
    });
    html += '</div>';
    return html;
}

function renderDetailedView(forecast) {
    const models = Object.keys(forecast);

    let html = `
        <div class="details-toggle">
            <button type="button" id="btn-hide-details">▾ Hide detailed numbers</button>
        </div>
    `;

    html += '<div class="forecast-grid">';
    models.forEach(m => {
        html += `<div class="model-panel"><h3>${MODEL_LABELS[m] || m}</h3>`;
        html += renderDayCards(forecast[m]);
        html += '</div>';
    });
    html += '</div>';

    html += '<h3 class="section-title">Charts</h3>';
    html += '<div id="charts"></div>';

    return html;
}

// =========================================================================
// MAIN RENDER
// =========================================================================
function renderForecastView(forecast) {
    if (!forecastView) return;

    forecastView.innerHTML = (currentView === 'simple')
        ? renderSimpleView(forecast)
        : renderDetailedView(forecast);

    if (currentView === 'details') {
        renderCharts(forecast);
    }
}

// =========================================================================
// CSV DOWNLOAD
// =========================================================================
function escapeCsv(value) {
    if (value === null || value === undefined) return '';
    const s = String(value);
    if (s.includes(',') || s.includes('"') || s.includes('\n')) {
        return '"' + s.replace(/"/g, '""') + '"';
    }
    return s;
}

function downloadForecastCsv() {
    if (!latestForecast) {
        alert('No forecast to download yet — generate a forecast first.');
        return;
    }

    const header = ['model', 'location', 'generated_for', 'day', 'date',
                    ...TARGETS.map(t => `${t.key}_${t.unit.replace(/[()]/g, '').trim()}`)];

    const lines = [header.join(',')];

    Object.keys(latestForecast.forecast).forEach(m => {
        latestForecast.forecast[m].forEach(row => {
            const line = [
                escapeCsv(MODEL_LABELS[m] || m),
                escapeCsv(latestForecast.location),
                escapeCsv(latestForecast.last_input_date),
                row.day,
                row.date,
                ...TARGETS.map(t => row[t.key])
            ];
            lines.push(line.join(','));
        });
    });

    const blob = new Blob([lines.join('\n')], { type: 'text/csv;charset=utf-8' });
    const url  = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `kathmandu_forecast_${new Date().toISOString().slice(0, 10)}.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
}

// =========================================================================
// LIVE FETCH
// =========================================================================
async function loadLive() {
    hideLiveStatus();
    hideError();
    if (!btnLive) return;
    btnLive.disabled = true;
    btnLive.textContent = 'Fetching...';

    try {
        const res  = await fetch('fetch_live.php');
        const data = await res.json();

        if (!res.ok || !data.ok) {
            showLiveStatus('Failed to load data: ' + (data.error || 'unknown error'), 'error');
            return;
        }

        const rows = data.rows;
        const trs  = tbody.querySelectorAll('tr');

        if (rows.length !== trs.length) {
            showLiveStatus(`Got ${rows.length} rows but form has ${trs.length} rows.`, 'error');
            return;
        }

        rows.forEach((row, i) => {
            const tr = trs[i];
            tr.querySelector('[name=datetime]').value         = row.datetime;
            tr.querySelector('[name=temp]').value             = row.temp;
            tr.querySelector('[name=humidity]').value         = row.humidity;
            tr.querySelector('[name=precip]').value           = row.precip;
            tr.querySelector('[name=windspeed]').value        = row.windspeed;
            tr.querySelector('[name=sealevelpressure]').value = row.sealevelpressure;
            tr.querySelector('[name=cloudcover]').value       = row.cloudcover;
        });

        if (data.source === 'open-meteo') {
            showLiveStatus('✓ Loaded ' + rows.length + ' days of live data.', 'success');
        } else if (data.source === 'fallback-csv') {
            showLiveStatus('⚠ ' + (data.note || 'Using fallback data.'), 'warning');
        } else {
            showLiveStatus('✓ Loaded ' + rows.length + ' days.', 'success');
        }
    } catch (err) {
        showLiveStatus('Network error: ' + err.message, 'error');
    } finally {
        btnLive.disabled = false;
        btnLive.textContent = '🌐 Load Last 14 Days (Live)';
    }
}

// =========================================================================
// SUBMIT
// =========================================================================
async function submitForm(e) {
    e.preventDefault();
    hideError();
    if (results) results.classList.add('hidden');

    const history = collectHistory();
    const model   = document.querySelector('#model-select').value;

    if (btnPredict) {
        btnPredict.disabled = true;
        btnPredict.textContent = 'Predicting...';
    }

    try {
        const res  = await fetch('predict.php', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ history, model })
        });
        const data = await res.json();

        if (!res.ok || !data.ok) {
            let msg = data.error || 'Prediction failed.';
            if (Array.isArray(data.details)) {
                msg += '<ul>' + data.details.map(d => `<li>${d}</li>`).join('') + '</ul>';
            }
            showError(msg);
            return;
        }

        latestForecast = data.forecast;

        const meta = document.querySelector('#results-meta');
        if (meta) {
            meta.textContent =
                `Location: ${data.forecast.location} | Input days: ${data.forecast.input_days} | Last input date: ${data.forecast.last_input_date}`;
        }

        currentView = 'simple';
        renderForecastView(data.forecast.forecast);

        if (results) {
            results.classList.remove('hidden');
            results.scrollIntoView({ behavior: 'smooth' });
        }
    } catch (err) {
        showError('Network error: ' + err.message);
    } finally {
        if (btnPredict) {
            btnPredict.disabled = false;
            btnPredict.textContent = '🔮 Predict Next 7 Days';
        }
    }
}

// =========================================================================
// TOGGLE HANDLERS (event delegation)
// =========================================================================
document.addEventListener('click', (e) => {
    if (e.target.id === 'btn-show-details') {
        currentView = 'details';
        if (latestForecast) renderForecastView(latestForecast.forecast);
    }
    if (e.target.id === 'btn-hide-details') {
        currentView = 'simple';
        if (latestForecast) renderForecastView(latestForecast.forecast);
    }
});

// =========================================================================
// BOOT
// =========================================================================
document.addEventListener('DOMContentLoaded', () => {
    buildRows((window.APP_CONFIG && window.APP_CONFIG.maxDays) || 14);

    if (btnLive)     btnLive.addEventListener('click', loadLive);
    if (btnClear)    btnClear.addEventListener('click', clearAll);
    if (form)        form.addEventListener('submit', submitForm);
    if (btnDownload) btnDownload.addEventListener('click', downloadForecastCsv);
});