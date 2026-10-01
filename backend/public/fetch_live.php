<?php

header('Content-Type: application/json');

require __DIR__ . '/../src/LiveDataFetcher.php';

$config = require __DIR__ . '/../config.php';

$fetcher = new LiveDataFetcher($config);
$result  = $fetcher->fetch();

if (!$result['ok']) {
    http_response_code(502);
    echo json_encode(['ok' => false, 'error' => $result['error']]);
    exit;
}

echo json_encode([
    'ok'     => true,
    'source' => $result['source'],
    'note'   => $result['note'] ?? null,
    'rows'   => $result['rows'],
]);