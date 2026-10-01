<?php

class WeatherApiClient
{
    public function __construct(
        private string $baseUrl,
        private int $timeout = 30
    ) {}

    public function health(): array
    {
        return $this->request('GET', '/health');
    }

    public function predict(array $history, string $model = 'both'): array
    {
        return $this->request('POST', '/predict', [
            'history' => $history,
            'model'   => $model,
        ]);
    }

    private function request(string $method, string $path, ?array $body = null): array
    {
        $url = rtrim($this->baseUrl, '/') . $path;
        $ch  = curl_init($url);

        $headers = ['Accept: application/json'];

        curl_setopt_array($ch, [
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_TIMEOUT        => $this->timeout,
            CURLOPT_CUSTOMREQUEST  => $method,
        ]);

        if ($body !== null) {
            $json = json_encode($body);
            $headers[] = 'Content-Type: application/json';
            curl_setopt($ch, CURLOPT_POSTFIELDS, $json);
        }

        curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);

        $raw    = curl_exec($ch);
        $errno  = curl_errno($ch);
        $errmsg = curl_error($ch);
        $status = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);

        if ($errno !== 0) {
            return [
                'ok'      => false,
                'status'  => 0,
                'error'   => "Connection to prediction API failed: {$errmsg}",
                'data'    => null,
            ];
        }

        $data = json_decode($raw, true);
        if (!is_array($data)) {
            return [
                'ok'     => false,
                'status' => $status,
                'error'  => "Malformed response from API (status {$status}).",
                'data'   => null,
            ];
        }

        return [
            'ok'     => $status >= 200 && $status < 300,
            'status' => $status,
            'error'  => $data['error'] ?? null,
            'data'   => $data,
        ];
    }
}