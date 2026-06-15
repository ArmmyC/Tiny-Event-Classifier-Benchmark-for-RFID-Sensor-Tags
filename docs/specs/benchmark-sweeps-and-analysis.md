# Feature Spec: Benchmark Sweeps and Analysis

## 1. Goal

Build a reproducible experiment-sweep layer on top of the existing Python benchmark.

The current benchmark can generate one dataset and compare threshold, FSM, LUT-like, legacy `tiny_snn`, and `tiny_snn_v2` on one default configuration. That is useful, but it is not enough for research. A single run cannot show whether the SNN is useful under specific conditions such as higher noise, timing jitter, dropout, dense negative activity, or smaller weight precision.

This feature adds sweep execution and analysis so the project can answer:

- Which classifier is best as noise increases?
- Which classifier is most robust to jitter?
- Which classifier fails under dropout?
- Does `tiny_snn_v2` become useful in any specific scenario?
- How much does `tiny_snn_v2` degrade when weights are quantized to stricter precision?
- Is any SNN variant near the accuracy, F1, and activity proxy Pareto frontier?

The output should be machine-readable JSON plus human-readable Markdown and CSV-style summary files. No plots are required in this task.

## 2. Non-goals

Do not build:

- RTL.
- Training or learned weights.
- A web dashboard.
- Post-synthesis area or power analysis.
- Hardware power claims.
- External experiment tracking services.
- Heavy ML dependencies.
- Pandas-only reporting.
- Matplotlib charts unless already present and easy to support without adding complexity.

This task is about reproducible software experiment sweeps and analysis.

## 3. Assumptions

- The repo already contains the Python benchmark MVP.
- The repo already contains scenario tags and per-scenario metrics.
- The repo already contains `tiny_snn_v2` as a hidden-layer integer IF/LIF classifier.
- Generated outputs under `data/generated/` and `results/` are ignored by git.
- The existing benchmark commands must keep working.
- Sweep results should be written under `results/sweeps/` by default.
- A sweep may generate temporary datasets in memory or under a temporary output directory.
- Sweep execution should be deterministic when seeds are fixed.
- JSON config is preferred to avoid requiring PyYAML.
- No database is required.

## 4. User stories

- As a researcher, I want to sweep noise probability, so that I can see when each classifier breaks.
- As a researcher, I want to sweep jitter and dropout, so that I can measure temporal robustness.
- As a researcher, I want multiple seeds per sweep point, so that I can avoid overclaiming from one lucky dataset.
- As a future RTL implementer, I want SNN v2 weight precision variants, so that I can estimate whether low-bit weights remain useful before writing RTL.
- As a maintainer, I want JSON and Markdown sweep summaries, so that results can be reviewed and compared over time.
- As a benchmark user, I want a simple command such as `make sweep`, so that I can run the full sweep without manually editing configs.

## 5. UX / UI requirements

This feature has a command-line UX only.

Add a command like:

```bash
PYTHONPATH=python python -m tinysnnrfid.run_sweep --config configs/sweeps/default.json
```

Add a Makefile target:

```bash
make sweep
```

The CLI should print concise progress messages:

```text
Sweep configuration loaded: configs/sweeps/default.json
Running sweep point 1/24: noise_probability=0.00, jitter_probability=0.20, dropout_probability=0.10, seed=1234
Running sweep point 2/24: ...
Sweep results written: results/sweeps/default_sweep_results.json
Sweep summary written: results/sweeps/default_sweep_summary.md
```

Error states:

- Missing sweep config.
- Invalid sweep parameter name.
- Invalid parameter values.
- Empty sweep grid.
- Unknown classifier name.
- Invalid SNN v2 quantization mode.
- Failure to write result files.

Empty states:

- If `results/sweeps/` does not exist, create it.
- If a sweep dimension has an empty list, reject the config with a clear message.

## 6. Functional requirements

1. Add a default sweep config at `configs/sweeps/default.json`.
2. The sweep config must reference or embed a base benchmark config.
3. The sweep config must support sweeping at least these dataset fields: `noise_probability`, `jitter_probability`, and `dropout_probability`.
4. The sweep config must support multiple random seeds.
5. The sweep config must support enabling or disabling classifiers for the sweep.
6. The sweep config must support at least one SNN v2 weight precision dimension.
7. The default sweep must include at least 3 noise values, 3 jitter values, 3 dropout values, and 2 seeds, unless runtime concerns justify a smaller default.
8. The sweep runner must generate datasets deterministically for each sweep point.
9. The sweep runner must evaluate all enabled classifiers on each sweep point.
10. The sweep runner must collect overall metrics for each classifier and sweep point.
11. The sweep runner must collect per-scenario metrics for each classifier and sweep point.
12. The sweep runner must collect activity proxy metrics for each classifier and sweep point.
13. The sweep runner must compute aggregate statistics across seeds for each unique non-seed sweep condition.
14. Aggregates must include mean and standard deviation for accuracy, precision, recall, F1, false positives, false negatives, and mean activity proxy.
15. The sweep runner must write a detailed JSON result file.
16. The sweep runner must write a compact JSON summary file.
17. The sweep runner must write a Markdown summary report.
18. The sweep runner must write a CSV-style summary file using the Python standard library, not pandas.
19. The Markdown report must include the best classifier by mean F1 for each sweep condition.
20. The Markdown report must include a section that highlights where `tiny_snn_v2` is best, tied for best, or close to best.
21. The Markdown report must include a section that highlights where `tiny_snn_v2` loses badly.
22. The Markdown report must include a section comparing SNN v2 weight precision modes.
23. The Markdown report must clearly say activity proxy is not hardware power or energy.
24. Existing `make data`, `make eval`, `make benchmark`, and `make test` must still work.
25. The implementation must not commit generated sweep result files.

## 7. Technical requirements

### Architecture

Preferred new files:

```text
configs/sweeps/default.json
python/tinysnnrfid/run_sweep.py
python/tinysnnrfid/sweep.py
python/tinysnnrfid/analysis.py
python/tinysnnrfid/quantization.py
tests/test_sweep.py
tests/test_quantization.py
```

Modify as needed:

```text
Makefile
README.md
python/tinysnnrfid/run_benchmark.py
python/tinysnnrfid/classifiers/tiny_snn_v2.py
```

Do not duplicate large blocks of benchmark logic. Prefer extracting reusable functions if needed.

### Sweep config shape

Use JSON. Suggested default:

```json
{
  "name": "default_sweep",
  "base_config": "configs/default.json",
  "output_dir": "results/sweeps",
  "classifiers": ["threshold", "fsm", "lut_like", "tiny_snn", "tiny_snn_v2"],
  "seeds": [1234, 5678],
  "sweep": {
    "dataset.noise_probability": [0.0, 0.03, 0.08],
    "dataset.jitter_probability": [0.0, 0.2, 0.5],
    "dataset.dropout_probability": [0.0, 0.1, 0.3],
    "classifiers.tiny_snn_v2.weight_precision": ["default", "ternary", "signed_2bit", "signed_3bit"]
  },
  "limits": {
    "max_points": 500
  }
}
```

For runtime safety, it is acceptable to reduce the default grid, but tests must use a tiny grid.

### Sweep point expansion

Implement deterministic Cartesian expansion of sweep dimensions.

Each sweep point should include:

```json
{
  "point_id": "stable-readable-id",
  "seed": 1234,
  "parameters": {
    "dataset.noise_probability": 0.03,
    "dataset.jitter_probability": 0.2,
    "dataset.dropout_probability": 0.1,
    "classifiers.tiny_snn_v2.weight_precision": "ternary"
  }
}
```

### Config patching

Implement a helper to set nested config fields using dotted paths:

```python
def set_dotted_path(config: dict, path: str, value: object) -> None:
    ...
```

Rules:

- Reject unknown top-level sections.
- Reject paths that do not already exist unless explicitly allowed.
- Reject empty path segments.

### Weight precision variants

Add support for SNN v2 weight precision variants.

Recommended helper:

```python
def quantize_integer_weights(values: np.ndarray, mode: str) -> np.ndarray:
    ...
```

Required modes:

- `default`: leave weights unchanged.
- `ternary`: map negative values to `-1`, zero to `0`, positive values to `1`.
- `signed_2bit`: clip weights to `[-2, 1]` or another clearly documented signed 2-bit range.
- `signed_3bit`: clip weights to `[-4, 3]`.

The chosen ranges must be documented in code and README or report output.

The sweep runner may apply quantization by patching `classifiers.tiny_snn_v2.input_weights` and `classifiers.tiny_snn_v2.output_weights` before building classifiers.

### Data flow

Preferred flow:

1. Load sweep config.
2. Load base benchmark config.
3. Expand sweep grid.
4. For each point:
   - Deep-copy base config.
   - Apply seed.
   - Apply dataset parameter patches.
   - Apply classifier list.
   - Apply SNN v2 weight precision if requested.
   - Generate dataset in memory or into a temporary directory.
   - Evaluate classifiers.
   - Store metrics and metadata.
5. Aggregate results across seeds.
6. Write output files.

If reusing `save_dataset` and `run_benchmark` is simpler, use temporary directories under `results/sweeps/tmp/` and clean them after successful execution.

### Result files

Write:

```text
results/sweeps/default_sweep_results.json
results/sweeps/default_sweep_summary.json
results/sweeps/default_sweep_summary.md
results/sweeps/default_sweep_summary.csv
```

These files should be ignored by git.

### Detailed JSON shape

```json
{
  "name": "default_sweep",
  "generated_at": "ISO-8601 timestamp",
  "base_config": "configs/default.json",
  "points": [
    {
      "point_id": "...",
      "seed": 1234,
      "parameters": {},
      "dataset": {},
      "classifiers": {
        "fsm": {
          "accuracy": 0.0,
          "precision": 0.0,
          "recall": 0.0,
          "f1": 0.0,
          "fp": 0,
          "fn": 0,
          "activity_proxy": {},
          "per_scenario": {}
        }
      }
    }
  ]
}
```

### Summary JSON shape

```json
{
  "name": "default_sweep",
  "grouped_by": [
    "dataset.noise_probability",
    "dataset.jitter_probability",
    "dataset.dropout_probability",
    "classifiers.tiny_snn_v2.weight_precision"
  ],
  "groups": [
    {
      "parameters": {},
      "classifier_summary": {
        "fsm": {
          "accuracy_mean": 0.0,
          "accuracy_std": 0.0,
          "f1_mean": 0.0,
          "f1_std": 0.0,
          "fp_mean": 0.0,
          "fn_mean": 0.0,
          "activity_mean": 0.0
        }
      },
      "best_by_f1": "fsm",
      "tiny_snn_v2_rank_by_f1": 2
    }
  ]
}
```

### CSV columns

At minimum:

```text
sweep_name,group_id,noise_probability,jitter_probability,dropout_probability,weight_precision,classifier,seed_count,accuracy_mean,accuracy_std,precision_mean,precision_std,recall_mean,recall_std,f1_mean,f1_std,fp_mean,fn_mean,activity_mean,rank_by_f1
```

## 8. Files likely involved

Create:

```text
configs/sweeps/default.json
python/tinysnnrfid/run_sweep.py
python/tinysnnrfid/sweep.py
python/tinysnnrfid/analysis.py
python/tinysnnrfid/quantization.py
tests/test_sweep.py
tests/test_quantization.py
```

Modify:

```text
Makefile
README.md
python/tinysnnrfid/classifiers/tiny_snn_v2.py
python/tinysnnrfid/run_benchmark.py
```

Only modify `tiny_snn_v2.py` if needed to expose default weights or support clean quantized construction.

## 9. Data model

No database.

Use file-based outputs under:

```text
results/sweeps/
```

Do not change the dataset artifact format.

Do not change `scenario_tags.json` format.

## 10. API contract

### Command: Run sweep

- Name: `run_sweep`
- Method: CLI command
- Path: `PYTHONPATH=python python -m tinysnnrfid.run_sweep --config configs/sweeps/default.json`

Request body: none.

Arguments:

```text
--config: path to sweep JSON config
--output-dir: optional override for sweep output directory
--max-points: optional safety override
```

Outputs:

```text
results/sweeps/<name>_results.json
results/sweeps/<name>_summary.json
results/sweeps/<name>_summary.md
results/sweeps/<name>_summary.csv
```

Error cases:

- Sweep config missing.
- Base config missing.
- Invalid dotted path.
- Invalid sweep value.
- Unknown classifier.
- Empty sweep dimension.
- Expanded point count exceeds max points.
- Invalid weight precision mode.

### Makefile target

Add:

```makefile
sweep:
	PYTHONPATH=python python -m tinysnnrfid.run_sweep --config configs/sweeps/default.json
```

If the current Makefile uses direct script paths, follow existing style while keeping the module command documented.

## 11. Edge cases

- Sweep grid expands to zero points.
- Sweep grid expands to too many points.
- A single classifier is enabled.
- `tiny_snn_v2` is disabled but weight precision is present in sweep config.
- A sweep has only one seed, so standard deviation should be `0.0`.
- Some scenarios do not appear in a dataset.
- All classifiers have identical F1.
- `tiny_snn_v2` is not present in results, so rank should be `null` or omitted.
- Weight precision causes all SNN v2 weights to become zero.
- Dense noise creates many accidental patterns.
- Dataset generation produces no positive labels or no negative labels due to config.

## 12. Testing plan

### Unit tests

Add tests for:

- Loading a valid sweep config.
- Rejecting missing base config.
- Rejecting empty sweep dimensions.
- Dotted path patching.
- Cartesian expansion count.
- Max-points protection.
- Weight quantization modes.
- Invalid weight quantization mode.
- Aggregation mean and standard deviation with one seed and multiple seeds.
- Ranking classifiers by F1.

### Integration tests

Add a tiny sweep test that:

1. Uses a temp sweep config with very small dataset size.
2. Uses 2 parameter points and 1 or 2 seeds.
3. Runs the sweep.
4. Verifies detailed JSON, summary JSON, Markdown, and CSV files exist.
5. Verifies each classifier has aggregate metrics.
6. Verifies `tiny_snn_v2` appears when enabled.
7. Verifies the Markdown report contains the hardware-warning language.

### Manual checks

Run:

```bash
make test
make sweep
```

Then inspect:

```text
results/sweeps/default_sweep_results.json
results/sweeps/default_sweep_summary.json
results/sweeps/default_sweep_summary.md
results/sweeps/default_sweep_summary.csv
```

Confirm:

- The sweep summary is readable.
- The summary clearly shows best classifier per condition.
- `tiny_snn_v2` rank is visible.
- Weight precision comparison is present.
- No generated sweep outputs are committed.

## 13. Definition of done

The task is complete only when:

- A default sweep config exists.
- `make sweep` works.
- The sweep runner expands parameter grids deterministically.
- The sweep runner evaluates all enabled classifiers across all points.
- Multiple seeds are supported.
- Detailed JSON output is written.
- Summary JSON output is written.
- Markdown summary output is written.
- CSV summary output is written.
- Aggregates include mean and standard deviation.
- `tiny_snn_v2` weight precision modes are supported.
- Tests cover config loading, expansion, quantization, aggregation, and an end-to-end tiny sweep.
- Existing commands still work.
- Generated result files are not committed.
- No hardware power or area claims are introduced.

## 14. Codex implementation instructions

Implement this spec.

Do not change unrelated files.

Do not add heavy ML dependencies.

Do not add pandas just for CSV reporting.

Do not implement training.

Do not implement RTL.

Do not make hardware power or area claims.

Keep existing benchmark commands working.

Prefer reusable functions over copying entire benchmark code.

Keep sweep tests small and fast.

Run `make test` before finishing.

Run `make sweep` after tests pass.

Summarize changed files, tests, output files, and any tradeoffs.
