# Feature Spec: Experiment Sweeps and Pareto Analysis

## 1. Goal

Build an experiment sweep system for the existing Tiny Event Classifier Benchmark for RFID Sensor Tags.

The current benchmark can compare classifiers on one generated dataset using one configuration. That is useful for a smoke test, but it is not enough for a research conclusion. This feature adds repeatable parameter sweeps across dataset difficulty and SNN configuration variants, then summarizes classifier performance across those sweeps.

The goal is to answer research questions like:

- Which classifier is best as noise increases?
- Does `tiny_snn_v2` help under high jitter or dropout?
- Does the SNN become more useful when the task is sparse and temporal?
- How sensitive is each classifier to random seed?
- What is the tradeoff between accuracy/F1 and software activity proxy?
- Which classifiers are on the Pareto frontier for accuracy versus activity proxy?

This feature should remain Python-only. It should not implement RTL or make hardware power claims.

## 2. Non-goals

Do not build:

- RTL implementations.
- Gate-level synthesis.
- Real silicon area or power estimation.
- A web dashboard.
- Plotly, pandas, seaborn, or heavyweight visualization dependencies.
- Training or automatic optimization of SNN weights.
- A large experiment framework requiring a database.
- A cloud runner.
- A full hyperparameter tuner.

This task is limited to deterministic local sweeps, CSV/JSON/Markdown summaries, and optional simple matplotlib plots only if matplotlib is already acceptable or added with clear justification.

## 3. Assumptions

- The repo already has the benchmark MVP.
- The repo already has scenario-tagged datasets.
- The repo already has `tiny_snn_v2`.
- The existing single-run benchmark must keep working.
- Generated sweep outputs should not be committed.
- The project currently uses NumPy and pytest.
- Avoid adding pandas. Use Python `csv`, `json`, and NumPy.
- Sweep configs should be small and readable.
- The initial sweep should be able to run on a normal laptop in under a few minutes for default settings.
- If runtime is a concern, provide `quick` and `full` sweep configs.

## 4. User stories

- As a researcher, I want to sweep noise probability, so that I can see which classifier breaks first under noisy RFID-like sensor events.
- As a researcher, I want to sweep jitter probability, so that I can evaluate temporal robustness.
- As a researcher, I want to sweep dropout probability, so that I can test partial or missing event patterns.
- As a benchmark user, I want results from multiple random seeds, so that I do not overfit conclusions to one generated dataset.
- As a project maintainer, I want sweep outputs in CSV, JSON, and Markdown, so that results can be inspected manually and processed later.
- As a future hardware implementer, I want Pareto summaries using F1/accuracy versus activity proxy, so that I can identify promising classifiers before writing RTL.
- As a researcher, I want `tiny_snn_v2` variants with different weight precision, so that I can explore how realistic quantization affects performance.

## 5. UX / UI requirements

This feature has command-line UX only.

Add new commands:

```bash
make sweep
make sweep-quick
```

Preferred direct module commands:

```bash
PYTHONPATH=python python -m tinysnnrfid.run_sweep --config configs/sweeps/quick.json
PYTHONPATH=python python -m tinysnnrfid.run_sweep --config configs/sweeps/default.json
```

The CLI should print concise progress:

```text
Sweep configuration loaded: configs/sweeps/quick.json
Running 24 experiment runs...
[1/24] noise_probability=0.00 jitter_probability=0.20 dropout_probability=0.10 seed=100
...
Sweep results written: results/sweeps/quick/sweep_results.json
Sweep summary written: results/sweeps/quick/sweep_summary.md
```

Error behavior:

- Missing sweep config exits non-zero.
- Invalid sweep parameter exits non-zero.
- Unknown classifier exits non-zero.
- Failed run should fail the whole sweep by default.

Optional future behavior may support `--continue-on-error`, but it is not required in this task.

## 6. Functional requirements

1. Add a sweep runner module, preferably `python/tinysnnrfid/run_sweep.py`.
2. Add a default sweep config under `configs/sweeps/default.json`.
3. Add a quick sweep config under `configs/sweeps/quick.json`.
4. Add Makefile target `sweep` that runs the default sweep.
5. Add Makefile target `sweep-quick` that runs the quick sweep.
6. The sweep runner must generate datasets in temporary or sweep-specific output directories, not overwrite normal `data/generated/` unless explicitly configured.
7. The sweep runner must run the existing benchmark logic for each experiment run.
8. The sweep runner must support sweeping at least these dataset fields:
   - `noise_probability`
   - `jitter_probability`
   - `dropout_probability`
   - `random_seed`
9. The sweep runner must support fixed base config plus per-run overrides.
10. The sweep runner must evaluate all classifiers enabled in the base benchmark config unless the sweep config overrides the enabled list.
11. The sweep runner must collect overall metrics for every classifier and every run.
12. The sweep runner must collect per-scenario metrics for every classifier and every run.
13. The sweep runner must collect activity proxy metrics for every classifier and every run.
14. The sweep runner must write machine-readable results to `results/sweeps/<sweep_name>/sweep_results.json`.
15. The sweep runner must write tabular rows to `results/sweeps/<sweep_name>/sweep_results.csv`.
16. The sweep runner must write a human-readable summary to `results/sweeps/<sweep_name>/sweep_summary.md`.
17. The CSV output must have one row per run per classifier.
18. The CSV output must include run id, swept parameter values, classifier name, accuracy, precision, recall, F1, TP, TN, FP, FN, and key activity proxy fields.
19. The JSON output must include the full sweep config, run configs, dataset summaries, classifier metrics, and per-scenario metrics.
20. The Markdown summary must include:
   - sweep name
   - number of runs
   - swept parameter ranges
   - classifiers evaluated
   - best classifier by mean F1
   - best classifier by worst-case F1
   - best classifier by mean activity proxy
   - Pareto frontier summary using mean F1 and mean activity proxy
   - per-scenario highlights
21. The Pareto frontier must identify classifiers that are not dominated by another classifier with both equal-or-better mean F1 and equal-or-lower mean activity proxy, with at least one strict improvement.
22. The implementation must label activity proxy as software proxy, not hardware power.
23. The sweep runner must not require internet access.
24. The sweep runner must be deterministic when the same sweep config is used.
25. The feature must not commit generated sweep outputs.
26. Existing single-run commands must keep working.
27. Existing tests must keep passing.

## 7. Technical requirements

### Architecture

Add modules as needed:

```text
python/tinysnnrfid/run_sweep.py
python/tinysnnrfid/sweep.py
python/tinysnnrfid/pareto.py
python/tinysnnrfid/sweep_report.py
```

A smaller implementation is acceptable if the code remains clean.

Preferred responsibilities:

- `run_sweep.py`: CLI entrypoint.
- `sweep.py`: sweep config loading, run expansion, execution orchestration.
- `pareto.py`: aggregate metrics and Pareto frontier calculation.
- `sweep_report.py`: CSV/JSON/Markdown writing.

Do not duplicate classifier logic. Reuse the existing dataset generation and benchmark functions where practical.

### Sweep config shape

Add config files like:

```json
{
  "name": "quick",
  "base_config": "configs/default.json",
  "output_dir": "results/sweeps/quick",
  "dataset_output_root": "results/sweeps/quick/datasets",
  "parameters": {
    "dataset.noise_probability": [0.0, 0.03, 0.08],
    "dataset.jitter_probability": [0.0, 0.2],
    "dataset.dropout_probability": [0.0, 0.1],
    "dataset.random_seed": [100, 101]
  },
  "overrides": {
    "dataset.num_samples": 300
  }
}
```

Rules:

- `name` must be a non-empty string.
- `base_config` must point to an existing benchmark config.
- `output_dir` must be a non-empty string.
- `dataset_output_root` must be a non-empty string.
- `parameters` must be a non-empty object.
- Parameter keys must use dotted paths into the benchmark config.
- Support at least `dataset.noise_probability`, `dataset.jitter_probability`, `dataset.dropout_probability`, and `dataset.random_seed`.
- `overrides` is optional.
- Every generated run config must pass existing benchmark config validation.

### Data flow

For each expanded run:

1. Load base benchmark config.
2. Apply global overrides.
3. Apply run-specific parameter values.
4. Set run-specific dataset output directory.
5. Set run-specific benchmark output directory.
6. Generate dataset using existing dataset generation logic.
7. Run benchmark using existing benchmark runner.
8. Collect returned result object.
9. Append normalized CSV row(s).
10. After all runs, aggregate metrics and write summary files.

### Output JSON shape

Suggested shape:

```json
{
  "sweep": {
    "name": "quick",
    "run_count": 24,
    "parameters": {}
  },
  "runs": [
    {
      "run_id": "run_0001",
      "parameters": {
        "dataset.noise_probability": 0.03,
        "dataset.jitter_probability": 0.2,
        "dataset.dropout_probability": 0.1,
        "dataset.random_seed": 100
      },
      "dataset": {},
      "classifiers": {}
    }
  ],
  "aggregate": {
    "by_classifier": {
      "fsm": {
        "mean_f1": 0.0,
        "min_f1": 0.0,
        "mean_accuracy": 0.0,
        "mean_activity_proxy": 0.0,
        "pareto_frontier": true
      }
    }
  }
}
```

### CSV columns

Minimum columns:

```text
run_id
classifier
noise_probability
jitter_probability
dropout_probability
random_seed
accuracy
precision
recall
f1
tp
tn
fp
fn
software_proxy_total_operations
software_proxy_mean_operations
software_proxy_max_operations
```

Include extra activity proxy fields when available, such as:

```text
input_spike_processing
hidden_updates
output_updates
hidden_spikes
output_spikes
```

### Markdown summary

The summary should be readable in GitHub Markdown.

Required sections:

```text
# Sweep Summary: <name>

## Sweep Configuration
## Aggregate Classifier Results
## Pareto Frontier
## Per-Scenario Highlights
## Interpretation
## Notes and Limitations
```

The notes must say that activity proxy is not hardware power and that RTL/synthesis is required before hardware conclusions.

### Pareto frontier

Implement a reusable function such as:

```python
def pareto_frontier(items: list[dict], score_key: str, cost_key: str) -> list[dict]:
    ...
```

Higher `score_key` is better. Lower `cost_key` is better.

An item is dominated if another item has:

- score >= item score
- cost <= item cost
- and at least one strict improvement

Use mean F1 as score and mean software proxy operations as cost.

## 8. Files likely involved

Create:

```text
configs/sweeps/quick.json
configs/sweeps/default.json
python/tinysnnrfid/run_sweep.py
python/tinysnnrfid/sweep.py
python/tinysnnrfid/pareto.py
python/tinysnnrfid/sweep_report.py
tests/test_sweep.py
tests/test_pareto.py
```

Modify:

```text
Makefile
README.md
.gitignore
```

Do not modify generated sweep outputs except through runtime generation.

## 9. Data model

No database changes.

Generated sweep outputs live under:

```text
results/sweeps/<sweep_name>/
```

Expected generated files:

```text
sweep_results.json
sweep_results.csv
sweep_summary.md
datasets/<run_id>/inputs.npy
datasets/<run_id>/labels.npy
datasets/<run_id>/metadata.json
datasets/<run_id>/scenario_tags.json
runs/<run_id>/benchmark_results.json
runs/<run_id>/benchmark_report.md
```

These files must be ignored by git.

## 10. API contract

No HTTP API is required.

### Command: Run sweep

- Name: `run_sweep`
- Method: CLI command
- Path:

```bash
PYTHONPATH=python python -m tinysnnrfid.run_sweep --config configs/sweeps/quick.json
```

Arguments:

```text
--config: path to sweep JSON config
--output-dir: optional override for sweep output directory
--max-runs: optional integer limit for debugging
```

Outputs:

```text
results/sweeps/<name>/sweep_results.json
results/sweeps/<name>/sweep_results.csv
results/sweeps/<name>/sweep_summary.md
```

Error cases:

- Missing sweep config.
- Invalid sweep config.
- Unsupported parameter path.
- Expanded run config fails validation.
- Dataset generation fails.
- Benchmark run fails.
- Output directory cannot be written.

## 11. Edge cases

- Sweep parameter list is empty.
- Parameter path does not exist in base config.
- Parameter value type is invalid.
- Sweep expands to zero runs.
- Sweep expands to too many runs.
- `max_runs` truncates run list.
- A classifier has missing activity proxy fields.
- A classifier has zero F1 across all runs.
- Multiple classifiers tie on mean F1.
- Multiple classifiers are on the Pareto frontier.
- A run has no positive samples due to config.
- A scenario tag is absent in a run.
- CSV field order must remain stable.

## 12. Testing plan

### Unit tests

Add tests for:

- Sweep config loading.
- Dotted-path override application.
- Run expansion count.
- Invalid dotted path rejection.
- Invalid parameter value rejection through existing benchmark config validation.
- Pareto frontier dominance logic.
- Aggregate mean/min metric calculation.
- CSV row normalization.

### Integration tests

Add a small end-to-end sweep test that:

1. Creates a temporary sweep config.
2. Uses a tiny dataset size such as 12 or 20 samples.
3. Sweeps two noise values and two seeds.
4. Runs the sweep into a temporary output directory.
5. Verifies JSON, CSV, and Markdown files exist.
6. Verifies every enabled classifier appears in aggregate results.
7. Verifies Pareto frontier output is present.
8. Verifies activity proxy warning appears in Markdown.

### Manual checks

Run:

```bash
make test
make sweep-quick
```

Open:

```text
results/sweeps/quick/sweep_summary.md
results/sweeps/quick/sweep_results.csv
results/sweeps/quick/sweep_results.json
```

Confirm:

- Output files are generated.
- Results contain all classifiers.
- `tiny_snn_v2` appears.
- Pareto frontier section is populated.
- Generated outputs are not committed.

## 13. Definition of done

The task is complete only when:

- `make sweep-quick` works.
- `make sweep` works or is documented as the longer sweep.
- Sweep outputs JSON, CSV, and Markdown files.
- Sweep runner uses existing benchmark/dataset logic.
- Results include overall, per-scenario, and activity proxy metrics.
- Pareto frontier summary is implemented and tested.
- Tests pass.
- Existing single-run benchmark commands still work.
- No generated sweep outputs are committed.
- No hardware power or area claims are introduced.

## 14. Codex implementation instructions

Implement this spec.

Do not change unrelated files.

Do not add pandas, seaborn, PyTorch, TensorFlow, JAX, or other heavyweight dependencies.

Prefer Python standard library `csv` and `json` for outputs.

Reuse existing dataset generation and benchmark runner functions.

Keep sweep outputs under `results/sweeps/` and ensure generated outputs are ignored by git.

Keep `make data`, `make eval`, `make benchmark`, and `make test` working.

Add `make sweep-quick` and `make sweep`.

Run the relevant tests before finishing.

Run `make sweep-quick` after tests pass.

Summarize changed files, generated outputs, and tradeoffs.
