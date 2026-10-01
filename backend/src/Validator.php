<?php

class Validator
{
    private const RANGES = [
        'temp'             => [-5.0,   45.0],
        'humidity'         => [0.0,   100.0],
        'precip'           => [0.0,   400.0],
        'windspeed'        => [0.0,   180.0],
        'sealevelpressure' => [950.0, 1050.0],
        'cloudcover'       => [0.0,   100.0],
    ];

    public static function validateHistory(array $rows, int $minDays, int $maxDays): array
    {
        $errors = [];
        $count  = count($rows);

        if ($count < $minDays || $count > $maxDays) {
            $errors[] = "Please provide between {$minDays} and {$maxDays} days of data (got {$count}).";
            return ['ok' => false, 'errors' => $errors, 'clean' => []];
        }

        $clean = [];
        foreach ($rows as $i => $row) {
            $dayNum = $i + 1;
            $out    = [];

            if (empty($row['datetime'])) {
                $errors[] = "Day {$dayNum}: date is required.";
                continue;
            }

            $ts = strtotime($row['datetime']);
            if ($ts === false) {
                $errors[] = "Day {$dayNum}: invalid date '{$row['datetime']}'.";
                continue;
            }
            $out['datetime'] = date('Y-m-d', $ts);

            foreach (self::RANGES as $field => [$lo, $hi]) {
                if (!isset($row[$field]) || $row[$field] === '') {
                    $errors[] = "Day {$dayNum}: '{$field}' is required.";
                    continue;
                }
                if (!is_numeric($row[$field])) {
                    $errors[] = "Day {$dayNum}: '{$field}' must be numeric.";
                    continue;
                }
                $v = (float) $row[$field];
                if ($v < $lo || $v > $hi) {
                    $errors[] = "Day {$dayNum}: '{$field}' = {$v} is outside [{$lo}, {$hi}].";
                    continue;
                }
                $out[$field] = $v;
            }

            $clean[] = $out;
        }

        return [
            'ok'     => empty($errors),
            'errors' => $errors,
            'clean'  => $clean,
        ];
    }
}