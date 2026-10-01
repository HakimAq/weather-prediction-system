<?php

header('Content-Type: application/json');

require __DIR__ . '/../src/Validator.php';
require __DIR__ . '/../src/WeatherApiClient.php';

$config = require __DIR__ . '/../config.php';

$raw  = file_get_contents('php://input');
$body = json_decode($raw, true);

if (!is_array($body) || !isset($body['history']) || !is_array($body['history'])) {
    http_response_code(400);
    echo json_encode(['ok' => false, 'error' => 'Invalid request: missing history array.']);
    exit;
}

$model = $body['model'] ?? 'both';
if (!in_array($model, ['rf', 'gb', 'both'], true)) {
    $model = 'both';
}

$validation = Validator::validateHistory(
    $body['history'],
    $config['min_days'],
    $config['max_days']
);

if (!$validation['ok']) {
    http_response_code(400);
    echo json_encode(['ok' => false, 'error' => 'Validation failed.', 'details' => $validation['errors']]);
    exit;
}

$client = new WeatherApiClient($config['api_base_url'], $config['api_timeout']);
$result = $client->predict($validation['clean'], $model);

if (!$result['ok']) {
    http_response_code(502);
    echo json_encode(['ok' => false, 'error' => $result['error'] ?? 'Prediction API error.']);
    exit;
}

echo json_encode(['ok' => true, 'forecast' => $result['data']]);