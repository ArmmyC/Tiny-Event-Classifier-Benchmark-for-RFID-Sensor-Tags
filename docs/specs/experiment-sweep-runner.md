# Feature Spec: Experiment Sweep Runner

## Goal

Add a reproducible Python sweep runner for the Tiny Event Classifier Benchmark for RFID Sensor Tags. The runner should execute the existing dataset generation and benchmark pipeline across multiple noise, jitter, dropout, dense-noise, and future SNN-v2 settings, then summarize when each classifier performs best.

The feature is Python-only. It does not implement RTL, training, or hardware power analysis.

## Requirements

- Add a CLI module at `python/tinysnnrfid/run_sweep.py`.
- Add a default sweep config at `configs/sweep_default.json`.
- Add `make sweep`.
- Keep `make data`, `make eval`, `make benchmark`, and `make test` working.
- Sweep at least:
  - `dataset.noise_probability`
  - `dataset.jitter_probability`
  - `dataset.dropout_probability`
  - `scenario.dense_noise_spike_threshold`
- Allow future sweep entries under `classifiers.tiny_snn_v2`.
- For each sweep point:
  - create a deterministic dataset from a seed,
  - run the existing enabled classifiers,
  - collect overall metrics,
  - collect per-scenario metrics,
  - collect activity proxy metrics.
- Write generated outputs under `results/sweeps/`:
  - `sweep_results.json`
  - `sweep_report.md`
- Do not commit generated sweep outputs.

## Sweep Config

Default shape:

```json
{
  "name": "default",
  "base_config": "configs/default.json",
  "output_dir": "results/sweeps",
  "dataset_output_root": "results/sweeps/generated",
  "seeds": [1234, 1235],
  "overrides": {
    "dataset.num_samples": 300
  },
  "parameters": {
    "dataset.noise_probability": [0.0, 0.03, 0.08],
    "dataset.jitter_probability": [0.0, 0.2],
    "dataset.dropout_probability": [0.0, 0.1],
    "scenario.dense_noise_spike_threshold": [8, 12]
  },
  "comparison": {
    "reference_classifier": "fsm",
    "candidate_classifier": "tiny_snn_v2"
  }
}
```

Supported parameter paths for this MVP:

- `dataset.noise_probability`
- `dataset.jitter_probability`
- `dataset.dropout_probability`
- `scenario.dense_noise_spike_threshold`
- `classifiers.tiny_snn_v2.hidden_threshold`
- `classifiers.tiny_snn_v2.output_threshold`
- `classifiers.tiny_snn_v2.leak`

Every expanded benchmark config must pass the existing benchmark config validation.

## Outputs

`sweep_results.json` must include:

- full sweep config,
- run count,
- one entry per sweep run,
- effective swept parameters and seed,
- dataset summary,
- classifier metrics,
- per-scenario metrics,
- activity proxy metrics,
- aggregate classifier summaries,
- `tiny_snn_v2` versus `fsm` comparison.

`sweep_report.md` must include:

- sweep setup,
- best classifier by F1 for each sweep point,
- best classifier by scenario,
- `tiny_snn_v2` versus `fsm` comparison table,
- cases where `tiny_snn_v2` wins,
- cases where `tiny_snn_v2` loses,
- a warning that activity proxies are software proxies and not hardware power.

## Definition of Done

- `python -m tinysnnrfid.run_sweep --config configs/sweep_default.json` works with `PYTHONPATH=python`.
- `make sweep` invokes the sweep runner.
- `make test` passes.
- Sweep JSON and Markdown are generated locally and ignored by git.
- Existing single-run benchmark behavior is not broken.
- No RTL, training, heavyweight ML dependency, or hardware power claim is introduced.
