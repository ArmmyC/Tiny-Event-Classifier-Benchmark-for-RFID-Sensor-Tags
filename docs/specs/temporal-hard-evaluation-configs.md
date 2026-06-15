# Feature Spec: Temporal-Hard Evaluation Configs

## 1. Goal

Add ready-to-run temporal-hard sweep and SNN-search configs so the new harder scenario suite is actually used by the research workflow.

The repo now supports `scenario_suite.mode = temporal_hard`, but the existing default sweep and SNN search configs still target the legacy dataset unless the user manually creates new configs. This task adds first-class commands and configs for temporal-hard evaluation.

The goal is:

```text
Run benchmark, sweep, and SNN search on temporal_hard scenarios with one-command workflows.
```

## 2. Non-goals

Do not implement:

- RTL.
- Training.
- New classifiers.
- New scenario tags.
- Heavy dependencies.
- Hardware power claims.

This is an experiment-configuration and integration task.

## 3. Required work

1. Keep `configs/temporal_hard.json` working.
2. Add `configs/sweep_temporal_hard.json`.
3. Add `configs/snn_search_temporal_hard.json`.
4. Add Makefile targets:

```makefile
temporal-sweep:
	python python/run_sweep.py --config configs/sweep_temporal_hard.json

temporal-snn-search:
	python python/run_snn_search.py --config configs/snn_search_temporal_hard.json
```

5. Update README with a short section explaining:
   - `make temporal-benchmark`,
   - `make temporal-sweep`,
   - `make temporal-snn-search`,
   - how these differ from legacy/default runs.
6. Ensure temporal sweep output goes under:

```text
results/temporal_sweeps/
```

7. Ensure temporal SNN search output goes under:

```text
results/temporal_snn_search/
```

8. Update `make clean` to remove temporal generated outputs and run directories.
9. Add tests that load the new configs and verify they use `scenario_suite.mode = temporal_hard`.
10. Add a tiny integration test that runs sweep/search logic with temporal-hard configs using small sample/candidate limits or temporary config copies.
11. Do not commit generated outputs.

## 4. Suggested config design

### `configs/sweep_temporal_hard.json`

Use:

```json
{
  "name": "temporal_hard_sweep",
  "base_config": "configs/temporal_hard.json",
  "output_dir": "results/temporal_sweeps",
  "dataset_output_root": "results/temporal_sweeps/generated",
  "seeds": [2026, 2027],
  "overrides": {
    "dataset.num_samples": 240
  },
  "parameters": {
    "dataset.noise_probability": [0.0, 0.02, 0.06],
    "dataset.jitter_probability": [0.0],
    "dataset.dropout_probability": [0.0]
  },
  "comparison": {
    "reference_classifier": "fsm",
    "candidate_classifier": "tiny_snn_v2",
    "f1_tolerance": 0.03
  }
}
```

### `configs/snn_search_temporal_hard.json`

Use:

```json
{
  "name": "temporal_hard_snn_search",
  "base_config": "configs/temporal_hard.json",
  "output_dir": "results/temporal_snn_search",
  "dataset_output_root": "results/temporal_snn_search/generated",
  "seeds": [2026, 2027],
  "dataset_overrides": {
    "dataset.num_samples": 240
  },
  "dataset_parameters": {
    "dataset.noise_probability": [0.0, 0.02, 0.06],
    "dataset.jitter_probability": [0.0],
    "dataset.dropout_probability": [0.0]
  },
  "snn_parameters": {
    "classifiers.tiny_snn_v2.hidden_threshold": [3, 4, 5],
    "classifiers.tiny_snn_v2.output_threshold": [2, 3, 4],
    "classifiers.tiny_snn_v2.leak": [0, 1],
    "classifiers.tiny_snn_v2.reset_on_spike": [true, false]
  },
  "weight_variants": [
    "current_default",
    "ternary_event_order",
    "ternary_noise_guard",
    "low_activity_sparse",
    "balanced_small_int"
  ],
  "comparison": {
    "reference_classifier": "fsm",
    "candidate_classifier": "tiny_snn_v2",
    "f1_tolerance": 0.03
  },
  "selection": {
    "strategy": "balanced_round_robin"
  },
  "limits": {
    "max_candidates": 80
  }
}
```

Keep values modest enough that CI/local runs remain reasonable.

## 5. Tests

Add or update tests for:

1. `configs/sweep_temporal_hard.json` loads through `load_sweep_config`.
2. `configs/snn_search_temporal_hard.json` loads through `load_search_config`.
3. Both configs point to `configs/temporal_hard.json` as their base config.
4. Loading the base config gives `scenario_suite.mode == temporal_hard`.
5. A tiny temporal sweep run writes JSON/CSV/Markdown outputs.
6. A tiny temporal SNN search run writes JSON/CSV/Markdown outputs.
7. Generated outputs remain ignored by git.

## 6. Manual checks

Run:

```bash
make test
make temporal-benchmark
make temporal-sweep
make temporal-snn-search
```

Inspect:

```text
results/benchmark_report.md
results/temporal_sweeps/sweep_report.md
results/temporal_snn_search/search_report.md
```

Confirm reports include temporal-hard scenario names and still call activity metrics software proxies, not hardware power.

## 7. Definition of done

This task is done when:

- Temporal-hard benchmark, sweep, and SNN search are all one-command workflows.
- New configs exist and load.
- Tests cover config loading and tiny execution paths.
- README documents the commands.
- `make clean` removes temporal outputs.
- No generated outputs are committed.
