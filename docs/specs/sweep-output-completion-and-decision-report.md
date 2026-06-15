# Feature Spec: Sweep Output Completion and Decision Report

## 1. Goal

Complete the experiment sweep feature so it becomes a useful research decision tool.

The current sweep runner can execute a grid of benchmark configurations and write JSON plus Markdown reports. However, it is missing the required CSV summary and the comparison logic is still too shallow. This feature finishes the sweep workflow by adding CSV output, F1-tolerance activity comparison, better competitive-case ranking, and a clear decision section that says whether `tiny_snn_v2` currently deserves further optimization or RTL work.

The goal is to make each sweep answer:

```text
Is tiny_snn_v2 ever better than FSM, and if not, what evidence tells us what to improve next?
```

## 2. Non-goals

Do not build:

- RTL.
- Training.
- Grid search for weights.
- New classifier architecture.
- Hardware power claims.
- Plots or a web dashboard.
- Pandas dependency.
- Heavy ML dependencies.

This task only completes and improves the sweep output/reporting layer.

## 3. Assumptions

- `python/tinysnnrfid/run_sweep.py` already exists.
- `configs/sweep_default.json` already exists.
- `make sweep` already runs the sweep.
- `tiny_snn_v2` and `fsm` both exist as benchmark classifiers.
- Existing generated sweep outputs live under `results/sweeps/` and are ignored by git.
- The repository uses only standard library plus NumPy and pytest.
- The sweep report must continue warning that activity proxy is not hardware power.

## 4. User stories

- As a researcher, I want a CSV sweep summary, so that I can inspect or process results outside the Python script.
- As a researcher, I want `tiny_snn_v2` compared to `fsm` using both F1 and activity proxy, so that I can tell whether the SNN has any practical advantage.
- As a digital design intern, I want the report to recommend next action, so that I know whether to tune the SNN, add harder scenarios, or stop and move to RTL baselines.
- As a project maintainer, I want tests for the CSV and decision report, so that the sweep output does not regress.

## 5. UX / UI requirements

Keep the existing commands working:

```bash
make sweep
PYTHONPATH=python python -m tinysnnrfid.run_sweep --config configs/sweep_default.json
```

After running, print all output paths:

```text
Sweep results written: results/sweeps/sweep_results.json
Sweep CSV written: results/sweeps/sweep_summary.csv
Sweep report written: results/sweeps/sweep_report.md
```

The Markdown report must include these sections:

```text
# Experiment Sweep Report: [name]
## Sweep Setup
## Best Classifier By Sweep Point
## Aggregate Classifier Summary
## Best Classifier By Scenario
## tiny_snn_v2 vs fsm
## Competitive Cases
## Decision Summary
## Notes and Limitations
```

No browser UI is needed.

## 6. Functional requirements

1. Update the sweep runner to write `results/sweeps/sweep_summary.csv`.
2. CSV writing must use Python standard library `csv`, not pandas.
3. CSV must contain one row per run per classifier.
4. CSV must include at least these columns:
   - `run_id`
   - `seed`
   - `noise_probability`
   - `jitter_probability`
   - `dropout_probability`
   - `dense_noise_spike_threshold`
   - `classifier`
   - `accuracy`
   - `precision`
   - `recall`
   - `f1`
   - `tp`
   - `tn`
   - `fp`
   - `fn`
   - `mean_activity_proxy`
   - `max_activity_proxy`
5. If a parameter is not explicitly swept, CSV must still use the effective value from the run config or parameter record where possible.
6. Add `comparison.f1_tolerance` support in `configs/sweep_default.json`.
7. Validate `comparison.f1_tolerance` as a non-negative number.
8. Update `compare_candidate_to_reference` to compute:
   - `candidate_f1_wins`
   - `candidate_f1_losses`
   - `candidate_f1_ties_within_tolerance`
   - `candidate_activity_wins`
   - `candidate_activity_wins_within_f1_tolerance`
   - `candidate_competitive_runs`
9. A competitive run is any run where candidate F1 is greater than reference F1, or where candidate activity is lower and candidate F1 is within tolerance of reference F1.
10. Sort competitive runs by F1 delta first, then lower candidate activity.
11. Add these comparison fields to `sweep_results.json`.
12. Add a `Competitive Cases` section to the Markdown report.
13. The `Competitive Cases` section must show up to 10 rows with:
    - run id
    - seed
    - parameters
    - candidate F1
    - reference F1
    - F1 delta
    - candidate activity
    - reference activity
    - reason
14. Add a `Decision Summary` section to the Markdown report.
15. The decision summary must produce one of these recommendations:
    - `continue_snn_optimization`
    - `add_harder_temporal_scenarios`
    - `prioritize_fsm_or_lut_rtl_baseline`
16. Use simple deterministic rules for the decision:
    - If candidate has at least one F1 win or at least one activity win within F1 tolerance, recommend `continue_snn_optimization`.
    - Else if no classifier clearly dominates across scenarios, recommend `add_harder_temporal_scenarios`.
    - Else recommend `prioritize_fsm_or_lut_rtl_baseline`.
17. The decision section must explain the recommendation in plain language.
18. Keep the activity proxy warning in the report.
19. Update README to mention `sweep_summary.csv`.
20. Update `make clean` to remove sweep outputs under `results/sweeps/` without deleting tracked `.gitkeep` files if present.
21. Existing `make data`, `make eval`, `make benchmark`, `make sweep`, and `make test` must continue to work.
22. Do not commit generated sweep outputs.

## 7. Technical requirements

### Files likely to modify

```text
python/tinysnnrfid/run_sweep.py
configs/sweep_default.json
README.md
Makefile
tests/test_sweep.py
```

Optional helper functions in `run_sweep.py`:

```python
def write_sweep_csv(output_dir: Path, results: dict[str, Any]) -> Path:
    ...

def flatten_classifier_rows(results: dict[str, Any]) -> list[dict[str, Any]]:
    ...

def build_decision_summary(results: dict[str, Any]) -> dict[str, Any]:
    ...
```

### CSV output path

```text
results/sweeps/sweep_summary.csv
```

### JSON comparison shape

Update `comparison` in `sweep_results.json` to include:

```json
{
  "candidate_classifier": "tiny_snn_v2",
  "reference_classifier": "fsm",
  "f1_tolerance": 0.03,
  "candidate_f1_wins": 0,
  "candidate_f1_losses": 0,
  "candidate_f1_ties_within_tolerance": 0,
  "candidate_activity_wins": 0,
  "candidate_activity_wins_within_f1_tolerance": 0,
  "candidate_competitive_runs": [],
  "rows": []
}
```

Each row should include:

```json
{
  "run_id": "run_0000",
  "seed": 1234,
  "parameters": {},
  "candidate_f1": 0.0,
  "reference_f1": 0.0,
  "f1_delta": 0.0,
  "candidate_activity": 0.0,
  "reference_activity": 0.0,
  "activity_delta": 0.0,
  "within_f1_tolerance": true,
  "candidate_activity_lower": true,
  "competitive_reason": "activity_win_within_f1_tolerance"
}
```

### Decision summary shape

Add top-level key:

```json
"decision": {
  "recommendation": "continue_snn_optimization",
  "reason": "tiny_snn_v2 had at least one competitive run against fsm.",
  "candidate_classifier": "tiny_snn_v2",
  "reference_classifier": "fsm"
}
```

## 8. Data model

No database changes.

Generated files:

```text
results/sweeps/sweep_results.json
results/sweeps/sweep_summary.csv
results/sweeps/sweep_report.md
```

All remain generated artifacts and should be ignored by git.

## 9. API contract

No HTTP API.

CLI remains:

```bash
PYTHONPATH=python python -m tinysnnrfid.run_sweep --config configs/sweep_default.json
```

Optional arguments should continue to work:

```text
--config
--output-dir
--max-runs
```

Outputs now include JSON, CSV, and Markdown.

## 10. Edge cases

- Candidate classifier missing from one run.
- Reference classifier missing from one run.
- F1 values equal exactly.
- F1 values differ by less than tolerance.
- Candidate activity equals reference activity.
- Activity proxy missing mean/max operation fields.
- CSV output directory does not exist.
- Sweep has only one run.
- Sweep has zero competitive cases.
- All classifiers have very low F1.

## 11. Testing plan

Add or update tests for:

- `f1_tolerance` validation.
- CSV file is written.
- CSV has expected columns.
- CSV has one row per run per classifier.
- Comparison includes tolerance fields.
- Activity win within F1 tolerance is counted.
- Competitive cases are sorted and include a reason.
- Decision summary returns `continue_snn_optimization` when competitive cases exist.
- Decision summary returns a fallback recommendation when no competitive cases exist.
- Markdown report includes `Competitive Cases`.
- Markdown report includes `Decision Summary`.
- README mentions `sweep_summary.csv`.

Manual checks:

```bash
make test
make sweep
```

Inspect:

```text
results/sweeps/sweep_summary.csv
results/sweeps/sweep_results.json
results/sweeps/sweep_report.md
```

## 12. Definition of done

The task is done when:

- Sweep writes JSON, CSV, and Markdown outputs.
- CSV contains one row per run per classifier.
- Comparison includes F1 tolerance and activity-within-tolerance logic.
- Markdown report includes Competitive Cases and Decision Summary.
- README is updated.
- `make clean` handles sweep outputs.
- Tests pass.
- `make sweep` works.
- No generated outputs are committed.
- Activity proxy is still clearly described as not hardware power.

## 13. Codex implementation instructions

Implement this spec.

Do not change unrelated files.

Do not implement RTL.

Do not implement training.

Do not add pandas or heavyweight dependencies.

Use Python standard library `csv` for CSV output.

Keep existing commands working.

Do not commit generated sweep outputs.

Run `make test`.

Run `make sweep`.

Summarize changed files, tests, and tradeoffs.
