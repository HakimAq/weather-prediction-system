<?php

class LiveDataFetcher
{
    private const DAILY_VARS = [
        'temperature_2m_mean',
        'relative_humidity_2m_mean',
        'precipitation_sum',
        'wind_speed_10m_max',
        'surface_pressure_mean',
        'cloud_cover_mean',
    ];

    public function __construct(
        private array $config
    ) {}

    public function fetch(): array
    {
        $live = $this->tryOpenMeteo();
        if ($live['ok']) {
            return [
                'ok'     => true,
                'source' => 'open-meteo',
                'rows'   => $live['rows'],
            ];
        }

        $fallback = $this->tryFallbackCsv();
        if ($fallback['ok']) {
            return [
                'ok'     => true,
                'source' => 'fallback-csv',
                'rows'   => $fallback['rows'],
                'note'   => 'Live weather service unreachable — using historical dataset (through 2025-06-30).',
            ];
        }

        return [
            'ok'     => false,
            'source' => 'none',
            'error'  => 'Both live fetch and fallback failed: ' . $live['error'],
        ];
    }

    private function tryOpenMeteo(): array
    {
        $cfg   = $this->config['open_meteo'];
        $end   = new DateTime('yesterday', new DateTimeZone($cfg['timezone']));
        $start = (clone $end)->modify('-13 days');

        $url = $cfg['base_url'] . '?' . http_build_query([
            'latitude'   => $cfg['latitude'],
            'longitude'  => $cfg['longitude'],
            'start_date' => $start->format('Y-m-d'),
            'end_date'   => $end->format('Y-m-d'),
            'daily'      => implode(',', self::DAILY_VARS),
            'timezone'   => $cfg['timezone'],
        ]);

        $raw = $this->curlGet($url);
        if (!$raw['ok']) {
            return ['ok' => false, 'error' => 'Open-Meteo request failed: ' . $raw['error']];
        }

        $data = json_decode($raw['body'], true);
        if (!is_array($data) || !isset($data['daily']['time'])) {
            return ['ok' => false, 'error' => 'Malformed Open-Meteo response'];
        }

        return ['ok' => true, 'rows' => $this->mapOpenMeteo($data, (float)$cfg['pressure_offset'])];
    }

    private function mapOpenMeteo(array $data, float $pressureOffset): array
    {
        $d = $data['daily'];
        $rows = [];

        for ($i = 0; $i < count($d['time']); $i++) {
            $pressure = isset($d['surface_pressure_mean'][$i])
                ? (float)$d['surface_pressure_mean'][$i] + $pressureOffset
                : null;

            $rows[] = [
                'datetime'         => $d['time'][$i],
                'temp'             => isset($d['temperature_2m_mean'][$i])       ? round((float)$d['temperature_2m_mean'][$i], 1) : null,
                'humidity'         => isset($d['relative_humidity_2m_mean'][$i]) ? round((float)$d['relative_humidity_2m_mean'][$i], 1) : null,
                'precip'           => isset($d['precipitation_sum'][$i])         ? round((float)$d['precipitation_sum'][$i], 1) : null,
                'windspeed'        => isset($d['wind_speed_10m_max'][$i])        ? round((float)$d['wind_speed_10m_max'][$i], 1) : null,
                'sealevelpressure' => $pressure !== null                          ? round($pressure, 1) : null,
                'cloudcover'       => isset($d['cloud_cover_mean'][$i])          ? round((float)$d['cloud_cover_mean'][$i], 1) : null,
            ];
        }

        return $rows;
    }

    private function tryFallbackCsv(): array
    {
        $path = $this->config['fallback_csv'];
        if (!file_exists($path)) {
            return ['ok' => false, 'error' => "Fallback CSV not found at {$path}"];
        }

        $handle = fopen($path, 'r');
        if ($handle === false) {
            return ['ok' => false, 'error' => 'Cannot open fallback CSV'];
        }

        $header = fgetcsv($handle);
        if ($header === false) {
            fclose($handle);
            return ['ok' => false, 'error' => 'Empty fallback CSV'];
        }

        $header = array_map('trim', $header);
        $allRows = [];
        while (($line = fgetcsv($handle)) !== false) {
            $allRows[] = array_combine($header, $line);
        }
        fclose($handle);

        $wanted  = ['datetime', 'temp', 'humidity', 'precip', 'windspeed', 'sealevelpressure', 'cloudcover'];
        $missing = array_diff($wanted, $header);
        if (!empty($missing)) {
            return ['ok' => false, 'error' => 'Fallback CSV missing columns: ' . implode(', ', $missing)];
        }

        $tail = array_slice($allRows, -14);

        $out = [];
        foreach ($tail as $r) {
            $out[] = [
                'datetime'         => substr($r['datetime'], 0, 10),
                'temp'             => round((float)$r['temp'], 1),
                'humidity'         => round((float)$r['humidity'], 1),
                'precip'           => round((float)$r['precip'], 1),
                'windspeed'        => round((float)$r['windspeed'], 1),
                'sealevelpressure' => round((float)$r['sealevelpressure'], 1),
                'cloudcover'       => round((float)$r['cloudcover'], 1),
            ];
        }

        return ['ok' => true, 'rows' => $out];
    }

    private function curlGet(string $url): array
    {
        $ch = curl_init($url);
        curl_setopt_array($ch, [
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_TIMEOUT        => 15,
            CURLOPT_CONNECTTIMEOUT => 8,
            CURLOPT_FOLLOWLOCATION => true,
            CURLOPT_SSL_VERIFYPEER => true,
        ]);
        $body   = curl_exec($ch);
        $errno  = curl_errno($ch);
        $errmsg = curl_error($ch);
        $status = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);

        if ($errno !== 0) {
            return ['ok' => false, 'error' => $errmsg];
        }
        if ($status < 200 || $status >= 300) {
            return ['ok' => false, 'error' => "HTTP {$status}"];
        }
        return ['ok' => true, 'body' => $body];
    }
}