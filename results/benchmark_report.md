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

## Classifier Metrics

| Classifier | Accuracy | Precision | Recall | F1 | TP | TN | FP | FN |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| threshold | 0.6570 | 0.5947 | 0.9860 | 0.7419 | 493 | 164 | 336 | 7 |
| fsm | 0.8360 | 0.9828 | 0.6840 | 0.8066 | 342 | 494 | 6 | 158 |
| lut_like | 0.6780 | 0.9495 | 0.3760 | 0.5387 | 188 | 490 | 10 | 312 |
| tiny_snn | 0.7630 | 0.9817 | 0.5360 | 0.6934 | 268 | 495 | 5 | 232 |

## Activity Proxies

> These values are software-estimated operation counts, not hardware power or energy measurements.

| Classifier | Total Operations | Mean / Sample | Max / Sample |
|---|---:|---:|---:|
| threshold | 164991 | 164.99 | 173 |
| fsm | 68715 | 68.72 | 76 |
| lut_like | 225000 | 225.00 | 225 |
| tiny_snn | 142421 | 142.42 | 164 |

## Interpretation

`fsm` has the strongest F1 score in this run. Activity values only compare software work; RTL simulation and synthesis are required before drawing hardware power or area conclusions.
