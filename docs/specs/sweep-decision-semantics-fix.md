# Feature Spec: Sweep Decision Semantics Fix

## 1. Goal

Fix the sweep comparison and decision-report semantics before using the sweep output to guide research decisions.

The current sweep runner writes JSON, CSV, and Markdown outputs, but the comparison logic is too permissive: a candidate run can be marked competitive just because its F1 is within tolerance, even when its software activity proxy is not better than the reference. That can overstate the usefulness of `tiny_snn_v2`.

This feature makes the decision logic stricter and more research-safe.

The goal is:

```text
Only call tiny_snn_v2 competitive when it either beats FSM on F1, or has lower activity while staying within the configured F1 tolerance.
```

## 2. Non-goals

Do not implement:

- RTL.
- Training.
- New classifiers.
- New benchmark scenarios.
- New sweep dimensions.
- Plotting.
- Pandas or heavyweight dependencies.

This is a small correctness patch for sweep comparison and reporting.

## 3. Current problem

The current comparison logic treats `tie_within_tolerance` as competitive by itself.

That is not strict enough.

A run where:

```text
tiny_snn_v2 F1 is slightly lower than FSM
and tiny_snn_v2 activity is equal or worse than FSM
```

should not be counted as competitive.

It should be counted as:

```text
f1_tie_within_tolerance_only
```

or similar, but not a competitive case.

## 4. Functional requirements

1. Update `compare_candidate_to_reference` in `python/tinysnnrfid/run_sweep.py`.
2. A run is competitive only if:
   - candidate F1 is greater than reference F1, or
   - candidate activity proxy is lower than reference activity proxy and candidate F1 is no worse than reference F1 by more than `f1_tolerance`.
3. A run where candidate F1 is within tolerance but activity is not lower must not be competitive.
4. Keep the existing fields:
   - `candidate_f1_wins`
   - `candidate_f1_losses`
   - `candidate_f1_ties_within_tolerance`
   - `candidate_activity_wins`
   - `candidate_activity_wins_within_f1_tolerance`
   - `competitive_runs`
5. Add an explicit row field:

```json
"competitive_reason": "f1_win"
```

Allowed values:

```text
f1_win
activity_win_within_f1_tolerance
not_competitive
missing_classifier
```

6. The `Competitive Cases` table in the Markdown report must show the competitive reason.
7. The top-level `decision` object in `sweep_results.json` must use a stable recommendation enum, not only a sentence.
8. Allowed `decision.recommendation` values:

```text
continue_snn_optimization
add_harder_temporal_scenarios
prioritize_fsm_or_lut_rtl_baseline
```

9. Add `decision.reason` as a human-readable explanation.
10. Update Markdown `Decision Summary` to show both:
    - the enum recommendation
    - the human-readable reason
11. Keep the activity proxy warning unchanged.
12. Existing outputs must still be generated:

```text
results/sweeps/sweep_results.json
results/sweeps/sweep_summary.csv
results/sweeps/sweep_report.md
```

13. Existing commands must keep working:

```bash
make test
make sweep
```

## 5. Decision rules

Use these deterministic rules:

```text
If candidate_f1_wins > 0 or candidate_activity_wins_within_f1_tolerance > 0:
    recommendation = continue_snn_optimization
Else if no single classifier is best in every scenario:
    recommendation = add_harder_temporal_scenarios
Else:
    recommendation = prioritize_fsm_or_lut_rtl_baseline
```

Definition of "single classifier is best in every scenario":

```text
All entries in aggregate.best_by_scenario have the same classifier name.
```

If the candidate classifier is missing from the sweep results, prefer:

```text
prioritize_fsm_or_lut_rtl_baseline
```

and explain that the candidate was not evaluated.

## 6. Tests to add or update

Update `tests/test_sweep.py`.

Required test cases:

1. Candidate F1 win is competitive with reason `f1_win`.
2. Candidate activity lower and F1 within tolerance is competitive with reason `activity_win_within_f1_tolerance`.
3. Candidate F1 within tolerance but activity equal or worse is not competitive.
4. Candidate F1 loss outside tolerance is not competitive.
5. `competitive_runs` excludes tolerance-only non-activity-win rows.
6. Decision object has `recommendation` enum and `reason` string.
7. Markdown report includes the enum recommendation and reason.
8. Existing CSV output test still passes.

## 7. Files likely to modify

```text
python/tinysnnrfid/run_sweep.py
tests/test_sweep.py
README.md
```

README update is optional unless wording currently implies tolerance-only cases are competitive.

## 8. Manual checks

Run:

```bash
make test
make sweep
```

Inspect:

```text
results/sweeps/sweep_results.json
results/sweeps/sweep_report.md
```

Confirm:

- `comparison.competitive_runs` only contains true F1 wins or activity wins within tolerance.
- `decision.recommendation` is one of the three allowed enum values.
- `decision.reason` explains the recommendation.
- The report still says activity proxy is not hardware power or energy.

## 9. Definition of done

This patch is done when:

- Competitive-case logic is stricter.
- Tolerance-only cases without activity advantage are not marked competitive.
- Decision summary uses stable enum values.
- Tests cover the corrected behavior.
- `make test` passes.
- `make sweep` works.
- No generated sweep outputs are committed.
