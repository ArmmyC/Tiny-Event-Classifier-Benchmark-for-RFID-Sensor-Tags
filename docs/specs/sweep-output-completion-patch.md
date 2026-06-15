# Patch Spec: Complete Sweep Outputs

## Current status

The sweep runner exists, but the sweep-output completion work has not landed on `main` yet.

Current implementation gaps:

- `python/tinysnnrfid/run_sweep.py` writes only `sweep_results.json` and `sweep_report.md`.
- `sweep_summary.csv` is not written.
- `configs/sweep_default.json` does not contain `comparison.f1_tolerance`.
- `compare_candidate_to_reference` only counts F1 wins and losses.
- There is no activity-within-F1-tolerance comparison.
- There is no top-level `decision` object in `sweep_results.json`.
- The Markdown report has no `Competitive Cases` section.
- The Markdown report has no `Decision Summary` section.

This patch spec narrows the task to only those missing pieces.

## Goal

Finish the existing sweep runner so `make sweep` produces a decision-ready research report.

The completed sweep must answer:

```text
Is tiny_snn_v2 ever competitive with fsm by F1 or by lower activity at similar F1?
```

## Files to modify

Modify only these files unless a test genuinely requires another file:

```text
python/tinysnnrfid/run_sweep.py
configs/sweep_default.json
README.md
Makefile
tests/test_sweep.py
```

Do not modify classifier implementations.

Do not modify dataset generation.

Do not modify generated output files.

## Required changes

### 1. Add CSV output

In `python/tinysnnrfid/run_sweep.py`, add CSV writing using the standard library `csv` module.

`write_sweep_outputs(...)` must write three files:

```text
sweep_results.json
sweep_summary.csv
sweep_report.md
```

It must print all three paths.

CSV path:

```text
results/sweeps/sweep_summary.csv
```

CSV must contain one row per sweep run per classifier.

Required columns:

```text
run_id
seed
noise_probability
jitter_probability
dropout_probability
dense_noise_spike_threshold
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

Use values from each run's `parameters` when available. If a parameter is not present in `parameters`, use an empty string rather than crashing.

### 2. Add F1 tolerance config

Update `configs/sweep_default.json`:

```json
"comparison": {
  "reference_classifier": "fsm",
  "candidate_classifier": "tiny_snn_v2",
  "f1_tolerance": 0.03
}
```

Update sweep config validation:

- `comparison.f1_tolerance` must be an int or float.
- It must not be bool.
- It must be greater than or equal to 0.
- Default to `0.03` if omitted.

### 3. Improve candidate-vs-reference comparison

Update `compare_candidate_to_reference` to accept a `f1_tolerance` argument.

Each comparison row must include:

```text
run_id
seed
parameters
candidate_f1
reference_f1
f1_delta
candidate_activity
reference_activity
activity_delta
within_f1_tolerance
candidate_activity_lower
competitive_reason
```

Definitions:

```text
f1_delta = candidate_f1 - reference_f1
activity_delta = candidate_activity - reference_activity
within_f1_tolerance = abs(f1_delta) <= f1_tolerance
candidate_activity_lower = candidate_activity < reference_activity
```

Competitive reasons:

```text
f1_win
activity_win_within_f1_tolerance
none
```

A run is competitive if:

```text
candidate_f1 > reference_f1
or
candidate_activity_lower and within_f1_tolerance
```

The returned comparison object must include:

```text
candidate_classifier
reference_classifier
f1_tolerance
candidate_f1_wins
candidate_f1_losses
candidate_f1_ties_within_tolerance
candidate_activity_wins
candidate_activity_wins_within_f1_tolerance
candidate_competitive_runs
rows
wins
losses
```

`candidate_competitive_runs` must be sorted by:

1. `f1_delta` descending.
2. `candidate_activity` ascending.

### 4. Add decision summary

Add a helper function:

```python
def build_decision_summary(results: dict[str, Any]) -> dict[str, Any]:
    ...
```

Add top-level key to `sweep_results.json`:

```json
"decision": {
  "recommendation": "continue_snn_optimization",
  "reason": "...",
  "candidate_classifier": "tiny_snn_v2",
  "reference_classifier": "fsm"
}
```

Decision rules:

```text
If candidate_f1_wins > 0 or candidate_activity_wins_within_f1_tolerance > 0:
    recommendation = continue_snn_optimization
Else if best_by_scenario contains more than one winning classifier:
    recommendation = add_harder_temporal_scenarios
Else:
    recommendation = prioritize_fsm_or_lut_rtl_baseline
```

The reason must be a short plain-English sentence.

### 5. Update Markdown report

Add sections:

```text
## Competitive Cases
## Decision Summary
```

`Competitive Cases` must show up to 10 rows:

```text
Run | Seed | Reason | Candidate F1 | Reference F1 | F1 Delta | Candidate Activity | Reference Activity | Parameters
```

If there are no competitive cases, say so clearly.

`Decision Summary` must show:

```text
Recommendation: `...`
Reason: ...
```

Keep the existing hardware caution:

```text
Activity proxy metrics are software operation proxies, not hardware power or energy.
```

### 6. README and Makefile

Update README to mention:

```text
results/sweeps/sweep_summary.csv
```

Update `make clean` to remove sweep generated outputs and run folders under `results/sweeps/`.

Do not delete tracked `.gitkeep` files if present.

### 7. Tests

Update `tests/test_sweep.py` to verify:

- `f1_tolerance` is accepted in valid config.
- Negative `f1_tolerance` is rejected.
- CSV file is written.
- CSV has expected columns.
- CSV row count equals `run_count * classifier_count`.
- Comparison includes tolerance fields.
- Activity win within F1 tolerance is counted.
- Competitive runs include `competitive_reason`.
- Decision object exists in sweep results.
- Markdown report includes `Competitive Cases`.
- Markdown report includes `Decision Summary`.

## Constraints

- Do not implement RTL.
- Do not implement training.
- Do not add pandas.
- Do not add heavyweight dependencies.
- Do not call activity proxy hardware power.
- Do not commit generated files under `results/sweeps/`.

## Manual checks

Run:

```bash
make test
make sweep
```

Inspect local generated files:

```text
results/sweeps/sweep_results.json
results/sweeps/sweep_summary.csv
results/sweeps/sweep_report.md
```

## Definition of done

Done means:

- `make test` passes.
- `make sweep` works.
- JSON, CSV, and Markdown outputs are created.
- CSV has one row per run per classifier.
- JSON has top-level `decision`.
- Markdown has `Competitive Cases` and `Decision Summary`.
- No generated outputs are committed.
