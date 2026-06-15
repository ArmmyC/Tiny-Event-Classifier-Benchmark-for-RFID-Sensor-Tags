# Feature Spec: Benchmark Sweeps and Pareto Summary

## 1. Goal

Build an experiment-sweep layer for the existing Tiny Event Classifier Benchmark for RFID Sensor Tags.

The current project can generate one dataset from one config and evaluate threshold, FSM, LUT-like, `tiny_snn`, and `tiny_snn_v2` classifiers. That is useful for smoke testing, but it is not enough for research. A single default run cannot answer when an SNN-style classifier is useful.

This feature adds automated parameter sweeps across noise, jitter, dropout, and optional SNN v2 weight precision variants. It should produce machine-readable sweep results and a human-readable Markdown summary that identifies where each classifier performs well or poorly.

The main research goal is to answer:

```text
Under which input conditions, if any, does tiny_snn_v2 become competitive with simpler digital baselines?
```

## 2. Non-goals

Do not build:

- RTL implementation.
- Synthesis flow.
- Gate-level power estimation.
- Plotting dependency that requires a heavy graphics stack.
- Web dashboard.
- Training loop.
- Hyperparameter optimizer.
- Large ML framework integration.
- Database storage.
- Cloud execution.

This is still a lightweight Python experiment-management feature.

## 3. Assumptions

- The repository already includes scenario-tagged datasets.
- The repository already includes `tiny_snn_v2`.
- The repository already includes `make data`, `make eval`, `make benchmark`, and `make test`.
- Generated artifacts under `data/generated/` and `results/` are ignored by git.
- Sweep outputs should also be generated artifacts and should not be committed.
- Experiments should be deterministic when a seed is provided.
- JSON is preferred for configuration because it avoids requiring PyYAML.
- NumPy is already available and acceptable.
- Matplotlib should not be required for this task. Markdown and CSV/JSON are enough.

## 4. User stories

- As a researcher, I want to run many benchmark settings automatically, so that I can compare classifier behavior across noise, jitter, and dropout.
- As a digital design intern, I want a simple command like `make sweep`, so that I can generate research evidence without manually editing config files.
- As a researcher, I want per-scenario sweep summaries, so that I can see whether `tiny_snn_v2` helps under specific conditions.
- As a project maintainer, I want sweep results saved as JSON and CSV, so that results can be processed later by scripts or notebooks.
- As a future RTL implementer, I want a Pareto-style summary using accuracy/F1 versus activity proxy, so that I can choose which classifier is worth translating to hardware.
- As a reviewer, I want the report to clearly avoid hardware-power claims, so that software activity proxies are not confused with real silicon power.

## 5. UX / UI requirements

This feature has command-line UX only.

Add these commands:

```bash
make sweep
PYTHONPATH=python python -m tinysnnrfid.run_sweep --config configs/sweep_default.json
```

The CLI should print concise progress:

```text
Sweep configuration loaded: configs/sweep_default.json
Running 36 sweep points...
[1/36] noise=0.00 jitter=0.00 dropout=0.00 seed=1234
...
Sweep results written: results/sweeps/sweep_results.json
Sweep report written: results/sweeps/sweep_report.md
```

The sweep should not require an existing dataset. It should generate temporary per-run datasets internally or write per-run datasets into a sweep-specific generated directory.

Recommended output directory:

```text
results/sweeps/
```

Optional temporary dataset directory:

```text
results/sweeps/generated/
```

The CLI must exit non-zero and print a clear error when:

- sweep config is missing,
- sweep config has invalid parameter values,
- no sweep points are generated,
- an experiment fails unexpectedly,
- output files cannot be written.

No responsive behavior is required because there is no browser UI.

## 6. Functional requirements

1. Add a default sweep config file at `configs/sweep_default.json`.
2. The sweep config must define a base benchmark config path, sweep parameter values, seed values, output directory, and enabled classifiers.
3. The sweep config must support sweeping at least:
   - `dataset.noise_probability`
   - `dataset.jitter_probability`
   - `dataset.dropout_probability`
4. The sweep config must support multiple random seeds.
5. The sweep runner must generate one benchmark run for every Cartesian product of configured sweep values and seeds.
6. The sweep runner must create a complete effective config for each sweep point by merging the base config with the sweep overrides.
7. Each sweep point must generate its own dataset deterministically.
8. Each sweep point must evaluate all enabled classifiers using the existing benchmark logic or a shared internal function.
9. Each sweep point result must include the parameter values, seed, dataset summary, classifier metrics, activity proxy, and per-scenario metrics.
10. The sweep runner must write `results/sweeps/sweep_results.json`.
11. The sweep runner must write `results/sweeps/sweep_summary.csv`.
12. The sweep runner must write `results/sweeps/sweep_report.md`.
13. The JSON result must preserve full per-run details.
14. The CSV summary must include one row per sweep point per classifier.
15. The CSV summary must include at least: run id, seed, noise probability, jitter probability, dropout probability, classifier, accuracy, precision, recall, F1, FP, FN, mean activity proxy, and max activity proxy.
16. The Markdown report must include a sweep configuration summary.
17. The Markdown report must include an overall classifier summary aggregated across all sweep points.
18. The Markdown report must include best and worst conditions for each classifier by F1.
19. The Markdown report must include cases where `tiny_snn_v2` beats `fsm` on F1, if any.
20. The Markdown report must include cases where `tiny_snn_v2` beats `fsm` on activity proxy while staying within a configurable F1 tolerance, if any.
21. The Markdown report must include a warning that activity proxy is not hardware power.
22. The sweep runner must not commit generated files.
23. The sweep runner must be deterministic for the same sweep config.
24. Existing single-run benchmark commands must continue to work.
25. Existing tests must continue to pass.
26. Add tests for sweep config loading and validation.
27. Add tests for sweep point generation.
28. Add tests for end-to-end sweep execution on a tiny sweep config.
29. Add tests for CSV and Markdown output creation.
30. Add tests that verify `tiny_snn_v2` comparison fields are present in the report or summary data.

## 7. Technical requirements

### Architecture

Prefer adding a new module:

```text
python/tinysnnrfid/run_sweep.py
```

Optional helper modules:

```text
python/tinysnnrfid/sweep.py
python/tinysnnrfid/csv_utils.py
```

Update:

```text
Makefile
README.md
configs/sweep_default.json
tests/test_sweep.py
```

Reuse existing functions wherever possible:

- `load_config`
- `DatasetConfig.from_mapping`
- `save_dataset`
- `run_benchmark`
- `write_reports`

Avoid duplicating classifier evaluation logic.

### Sweep config format

Create `configs/sweep_default.json` with this shape:

```json
{
  "base_config": "configs/default.json",
  "output_dir": "results/sweeps",
  "temporary_data_dir": "results/sweeps/generated",
  "seeds": [1234, 1235, 1236],
  "sweep": {
    "dataset.noise_probability": [0.0, 0.03, 0.08, 0.15],
    "dataset.jitter_probability": [0.0, 0.2, 0.5],
    "dataset.dropout_probability": [0.0, 0.1, 0.3]
  },
  "comparison": {
    "reference_classifier": "fsm",
    "candidate_classifier": "tiny_snn_v2",
    "f1_tolerance": 0.03
  }
}
```

### Sweep config validation

Validate:

- `base_config` is a non-empty string path.
- `output_dir` is a non-empty string path.
- `temporary_data_dir` is a non-empty string path.
- `seeds` is a non-empty list of integers.
- `sweep` is a non-empty object.
- Supported sweep keys are known safe config paths.
- Sweep values are non-empty lists.
- Probability sweep values are numbers in `[0.0, 1.0]`.
- `comparison.reference_classifier` and `comparison.candidate_classifier` are non-empty strings.
- `comparison.f1_tolerance` is a non-negative number.

Allowed sweep keys for this task:

```text
dataset.noise_probability
dataset.jitter_probability
dataset.dropout_probability
classifiers.tiny_snn_v2.hidden_threshold
classifiers.tiny_snn_v2.output_threshold
classifiers.tiny_snn_v2.leak
```

Do not support arbitrary nested config paths yet. Avoid letting users override unknown fields.

### Data flow

For each sweep point:

1. Load base config.
2. Deep-copy base config.
3. Apply sweep parameter overrides.
4. Set `dataset.random_seed` to the current seed.
5. Set `paths.data_dir` to a unique per-run temporary dataset directory.
6. Set `paths.results_dir` to a unique per-run temporary result directory or avoid writing per-run reports if using an internal API.
7. Generate dataset.
8. Run benchmark.
9. Extract classifier metrics.
10. Append to sweep results.
11. Continue until all sweep points finish.

After all sweep points:

1. Aggregate per-classifier metrics.
2. Generate CSV summary.
3. Generate Markdown report.
4. Write JSON, CSV, and Markdown outputs.

### Run identifiers

Each run should have a stable run id such as:

```text
run_0000
run_0001
run_0002
```

Each sweep point should record:

```json
{
  "run_id": "run_0000",
  "seed": 1234,
  "parameters": {
    "dataset.noise_probability": 0.03,
    "dataset.jitter_probability": 0.2,
    "dataset.dropout_probability": 0.1
  }
}
```

### CSV output

Use Python standard library `csv`.

Do not add pandas.

Required CSV columns:

```text
run_id
seed
noise_probability
jitter_probability
dropout_probability
classifier
accuracy
precision
recall
f1
tp
tn
fp
fn
mean_activity_proxy
max_activity_proxy
```

If a parameter is not swept, use the effective base config value.

### Markdown report contents

`results/sweeps/sweep_report.md` must include:

```text
# Benchmark Sweep Report

## Sweep Setup
## Aggregate Classifier Summary
## Best and Worst Conditions
## tiny_snn_v2 vs fsm
## Notes and Limitations
```

Aggregate classifier summary should include mean and best values across runs:

```text
Classifier | Runs | Mean F1 | Best F1 | Worst F1 | Mean Accuracy | Mean Activity Proxy
```

`tiny_snn_v2 vs fsm` should include:

- Number of runs where `tiny_snn_v2` F1 is greater than `fsm` F1.
- Number of runs where `tiny_snn_v2` activity proxy is lower than `fsm` and F1 is within tolerance.
- A compact table of the top few cases where `tiny_snn_v2` is most competitive.

### Permissions and security

- Do not execute code from configs.
- Do not support arbitrary config path writes.
- Do not write outside the configured output directory except generated temporary data paths under the repo.
- Do not require network access.
- Do not store secrets.

## 8. Files likely involved

Create:

```text
configs/sweep_default.json
python/tinysnnrfid/run_sweep.py
tests/test_sweep.py
```

Optionally create:

```text
python/tinysnnrfid/sweep.py
```

Modify:

```text
Makefile
README.md
.gitignore
```

Do not modify generated result files.

## 9. Data model

No database is required.

Add generated files:

```text
results/sweeps/sweep_results.json
results/sweeps/sweep_summary.csv
results/sweeps/sweep_report.md
```

These files must be ignored by git.

### `sweep_results.json`

Suggested shape:

```json
{
  "sweep_config": {},
  "run_count": 36,
  "classifiers": ["threshold", "fsm", "lut_like", "tiny_snn", "tiny_snn_v2"],
  "runs": [
    {
      "run_id": "run_0000",
      "seed": 1234,
      "parameters": {
        "dataset.noise_probability": 0.03,
        "dataset.jitter_probability": 0.2,
        "dataset.dropout_probability": 0.1
      },
      "dataset": {},
      "classifiers": {}
    }
  ],
  "aggregate": {
    "fsm": {
      "runs": 36,
      "mean_f1": 0.0,
      "best_f1": 0.0,
      "worst_f1": 0.0,
      "mean_accuracy": 0.0,
      "mean_activity_proxy": 0.0
    }
  },
  "comparison": {
    "reference_classifier": "fsm",
    "candidate_classifier": "tiny_snn_v2",
    "candidate_f1_wins": 0,
    "candidate_activity_wins_within_f1_tolerance": 0
  }
}
```

### `sweep_summary.csv`

One row per sweep point per classifier.

### `sweep_report.md`

Human-readable summary.

## 10. API contract

No HTTP API is required.

### Command: run sweep

- Name: `run_sweep`
- Method: CLI command
- Path:

```bash
PYTHONPATH=python python -m tinysnnrfid.run_sweep --config configs/sweep_default.json
```

Request body: none.

Arguments:

```text
--config: path to sweep JSON config
--output-dir: optional override for sweep output directory
```

Outputs:

```text
results/sweeps/sweep_results.json
results/sweeps/sweep_summary.csv
results/sweeps/sweep_report.md
```

Error cases:

- Missing sweep config.
- Invalid sweep config.
- Base config missing.
- Unsupported sweep key.
- Invalid probability value.
- No sweep points generated.
- Benchmark run failure.
- Output path cannot be created.

### Make target

Add:

```makefile
sweep:
	PYTHONPATH=python python -m tinysnnrfid.run_sweep --config configs/sweep_default.json
```

## 11. Edge cases

- Only one sweep value is provided.
- Multiple seeds but one parameter combination.
- Candidate classifier is not enabled in the base config.
- Reference classifier is not enabled in the base config.
- `tiny_snn_v2` is disabled.
- Sweep produces zero runs due to empty values.
- Output directory already exists.
- Temporary generated data already exists.
- One run fails halfway through.
- Metrics contain zero precision or zero recall.
- Two classifiers tie on F1.
- Activity proxy fields are missing for a classifier.
- The sweep is large and produces many run directories.

## 12. Testing plan

### Unit tests

Add tests for:

- Loading a valid sweep config.
- Rejecting missing base config path.
- Rejecting empty seed list.
- Rejecting unsupported sweep key.
- Rejecting probability outside `[0, 1]`.
- Generating the correct Cartesian product of sweep points.
- Applying sweep overrides to a deep-copied base config.
- Creating stable run ids.
- Aggregating classifier metrics.
- Comparing `tiny_snn_v2` against `fsm`.

### Integration tests

Add a small end-to-end sweep test that uses:

```json
{
  "seeds": [1],
  "sweep": {
    "dataset.noise_probability": [0.0, 0.1],
    "dataset.jitter_probability": [0.0],
    "dataset.dropout_probability": [0.0]
  }
}
```

The test should assert:

- JSON output exists.
- CSV output exists.
- Markdown output exists.
- There are 2 sweep runs.
- Each enabled classifier appears in each run.
- `tiny_snn_v2` appears in aggregate summary.
- Markdown includes `tiny_snn_v2 vs fsm`.

### Manual checks

Run:

```bash
pip install -r requirements.txt
make test
make sweep
```

Inspect:

```text
results/sweeps/sweep_results.json
results/sweeps/sweep_summary.csv
results/sweeps/sweep_report.md
```

Confirm:

- Results include all enabled classifiers.
- Sweep report includes aggregate summary.
- Sweep report includes `tiny_snn_v2 vs fsm` section.
- Activity proxy warning is present.
- Generated sweep files are not tracked by git.

## 13. Definition of done

The task is complete only when:

- `configs/sweep_default.json` exists.
- `PYTHONPATH=python python -m tinysnnrfid.run_sweep --config configs/sweep_default.json` works.
- `make sweep` works.
- Sweep output JSON, CSV, and Markdown files are generated.
- Sweep results include all enabled classifiers.
- Aggregate summary is computed.
- `tiny_snn_v2` is compared against `fsm`.
- Tests cover config validation, sweep point generation, aggregation, and end-to-end sweep execution.
- `make test` passes.
- Existing benchmark commands still work.
- No generated sweep artifacts are committed.
- No hardware power claims are introduced.

## 14. Codex implementation instructions

Implement this spec.

Do not change unrelated files.

Do not implement RTL.

Do not implement training.

Do not add pandas, PyTorch, TensorFlow, JAX, or other heavyweight dependencies.

Use only the standard library and existing dependencies where possible.

Reuse the existing benchmark pipeline instead of duplicating classifier logic.

Keep outputs clearly labeled as software benchmark results.

Keep activity proxy warnings clear. Do not call activity proxy hardware power.

Add `make sweep`.

Add tests.

Run the relevant tests before finishing.

Run `make sweep` after tests pass.

Summarize changed files, tests, and tradeoffs.
