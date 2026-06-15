# Tiny SNN RFID Benchmark Report

## Configuration Summary

- Seed: `1234`
- Samples: `1000`
- Sequence shape: `32 x 4`
- Valid pattern: `[0, 1, 2]`
- Noise / jitter / dropout: `0.03` / `0.2` / `0.1`

## Dataset Summary

- Labels: `{'0': 500, '1': 500}`
- Input shape: `[1000, 32, 4]`
- Scenarios: `{'clean_positive': 239, 'jittered_positive': 124, 'dropped_positive': 137, 'noise_negative': 482, 'accidental_pattern_negative': 5, 'dense_noise_negative': 13}`

## Classifier Metrics

| Classifier | Accuracy | Precision | Recall | F1 | TP | TN | FP | FN |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| threshold | 0.6570 | 0.5947 | 0.9860 | 0.7419 | 493 | 164 | 336 | 7 |
| fsm | 0.8360 | 0.9828 | 0.6840 | 0.8066 | 342 | 494 | 6 | 158 |
| lut_like | 0.6780 | 0.9495 | 0.3760 | 0.5387 | 188 | 490 | 10 | 312 |
| tiny_snn | 0.7630 | 0.9817 | 0.5360 | 0.6934 | 268 | 495 | 5 | 232 |

## Per-Scenario Metrics

| Classifier | Scenario | Count | Accuracy | Precision | Recall | F1 | FP | FN |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| threshold | accidental_pattern_negative | 5 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 5 | 0 |
| threshold | clean_positive | 239 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0 | 0 |
| threshold | dense_noise_negative | 13 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 13 | 0 |
| threshold | dropped_positive | 137 | 0.9489 | 1.0000 | 0.9489 | 0.9738 | 0 | 7 |
| threshold | jittered_positive | 124 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0 | 0 |
| threshold | noise_negative | 482 | 0.3402 | 0.0000 | 0.0000 | 0.0000 | 318 | 0 |
| fsm | accidental_pattern_negative | 5 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 5 | 0 |
| fsm | clean_positive | 239 | 0.9247 | 1.0000 | 0.9247 | 0.9609 | 0 | 18 |
| fsm | dense_noise_negative | 13 | 0.9231 | 0.0000 | 0.0000 | 0.0000 | 1 | 0 |
| fsm | dropped_positive | 137 | 0.1241 | 1.0000 | 0.1241 | 0.2208 | 0 | 120 |
| fsm | jittered_positive | 124 | 0.8387 | 1.0000 | 0.8387 | 0.9123 | 0 | 20 |
| fsm | noise_negative | 482 | 1.0000 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 |
| lut_like | accidental_pattern_negative | 5 | 0.4000 | 0.0000 | 0.0000 | 0.0000 | 3 | 0 |
| lut_like | clean_positive | 239 | 0.4603 | 1.0000 | 0.4603 | 0.6304 | 0 | 129 |
| lut_like | dense_noise_negative | 13 | 1.0000 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 |
| lut_like | dropped_positive | 137 | 0.1533 | 1.0000 | 0.1533 | 0.2658 | 0 | 116 |
| lut_like | jittered_positive | 124 | 0.4597 | 1.0000 | 0.4597 | 0.6298 | 0 | 67 |
| lut_like | noise_negative | 482 | 0.9855 | 0.0000 | 0.0000 | 0.0000 | 7 | 0 |
| tiny_snn | accidental_pattern_negative | 5 | 0.2000 | 0.0000 | 0.0000 | 0.0000 | 4 | 0 |
| tiny_snn | clean_positive | 239 | 0.7280 | 1.0000 | 0.7280 | 0.8426 | 0 | 65 |
| tiny_snn | dense_noise_negative | 13 | 0.9231 | 0.0000 | 0.0000 | 0.0000 | 1 | 0 |
| tiny_snn | dropped_positive | 137 | 0.1095 | 1.0000 | 0.1095 | 0.1974 | 0 | 122 |
| tiny_snn | jittered_positive | 124 | 0.6371 | 1.0000 | 0.6371 | 0.7783 | 0 | 45 |
| tiny_snn | noise_negative | 482 | 1.0000 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 |

## Activity Proxies

> These values are software-estimated operation counts, not hardware power or energy measurements.

| Classifier | Total Operations | Mean / Sample | Max / Sample |
|---|---:|---:|---:|
| threshold | 164991 | 164.99 | 173 |
| fsm | 68715 | 68.72 | 76 |
| lut_like | 225000 | 225.00 | 225 |
| tiny_snn | 142421 | 142.42 | 164 |

## Interpretation

`fsm` has the strongest overall F1 score in this run.

- `threshold` worst scenario: `accidental_pattern_negative` (accuracy 0.0000, F1 0.0000).
- `fsm` worst scenario: `accidental_pattern_negative` (accuracy 0.0000, F1 0.0000).
- `lut_like` worst scenario: `dropped_positive` (accuracy 0.1533, F1 0.2658).
- `tiny_snn` worst scenario: `dropped_positive` (accuracy 0.1095, F1 0.1974).

Scenario metrics are benchmark diagnostics, not hardware conclusions. Activity values only compare software work; RTL simulation and synthesis are required before drawing power or area conclusions.
