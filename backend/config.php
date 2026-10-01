<?php

return [
    'api_base_url'   => 'http://localhost:5000',
    'api_timeout'    => 30,
    'min_days'       => 14,
    'max_days'       => 14,
    'app_title'      => 'Kathmandu Weather Prediction',

    'open_meteo' => [
        'base_url'        => 'https://archive-api.open-meteo.com/v1/archive',
        'latitude'        => 27.7172,
        'longitude'       => 85.3240,
        'timezone'        => 'Asia/Kathmandu',
        'pressure_offset' => 140.0,
    ],

    'fallback_csv' => __DIR__ . '/../ml/data/raw/TIA-WEATHER-DATA-2015-01-01-TO-2025-06-30.csv',
];