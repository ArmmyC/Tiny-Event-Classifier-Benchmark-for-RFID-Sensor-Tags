# Codex Prompt: Fix Sweep Decision Semantics

You are working in the repository `Tiny-Event-Classifier-Benchmark-for-RFID-Sensor-Tags`.

Implement the feature spec at:

```text
docs/specs/sweep-decision-semantics-fix.md
```

## Goal

Fix the sweep comparison and decision-report semantics so the benchmark does not overstate `tiny_snn_v2` competitiveness.

Right now a run can be treated as competitive just because `tiny_snn_v2` F1 is within tolerance of `fsm`, even if its software activity proxy is not lower. That is too permissive for research decision-making.

## Required behavior

A run is competitive only if either:

```text
tiny_snn_v2 F1 > fsm F1
```

or:

```text
tiny_snn_v2 activity proxy < fsm activity proxy
and tiny_snn_v2 F1 >= fsm F1 - f1_tolerance
```

A tolerance-only run with equal or worse activity must not be competitive.

## Required changes

1. Update `compare_candidate_to_reference` in `python/tinysnnrfid/run_sweep.py`.
2. Keep existing comparison count fields.
3. Add row field `competitive_reason`.
4. Allowed `competitive_reason` values:

```text
f1_win
activity_win_within_f1_tolerance
not_competitive
missing_classifier
```

5. Ensure `competitive_runs` contains only true competitive cases.
6. Update the `Competitive Cases` Markdown table to show the reason.
7. Update the top-level `decision` object so `decision.recommendation` is a stable enum.
8. Allowed `decision.recommendation` values:

```text
continue_snn_optimization
add_harder_temporal_scenarios
prioritize_fsm_or_lut_rtl_baseline
```

9. Add `decision.reason` as a plain-language explanation.
10. Update `Decision Summary` in the Markdown report to show both the enum and reason.
11. Keep activity proxy warnings clear. Do not call software activity proxy hardware power.

## Decision rules

Use:

```text
If candidate_f1_wins > 0 or candidate_activity_wins_within_f1_tolerance > 0:
    recommendation = continue_snn_optimization
Else if no single classifier is best in every scenario:
    recommendation = add_harder_temporal_scenarios
Else:
    recommendation = prioritize_fsm_or_lut_rtl_baseline
```

A single classifier is best in every scenario if all entries in `aggregate.best_by_scenario` have the same classifier name.

## Tests

Update `tests/test_sweep.py` to cover:

1. F1 win is competitive with reason `f1_win`.
2. Activity lower plus F1 within tolerance is competitive with reason `activity_win_within_f1_tolerance`.
3. F1 within tolerance but activity equal or worse is not competitive.
4. F1 loss outside tolerance is not competitive.
5. `competitive_runs` excludes tolerance-only non-activity-win rows.
6. Decision object has enum `recommendation` and string `reason`.
7. Markdown report includes the enum recommendation and reason.
8. Existing CSV output tests still pass.

## Constraints

- Do not implement RTL.
- Do not implement training.
- Do not add pandas or heavyweight dependencies.
- Keep `make test` and `make sweep` working.
- Do not commit generated outputs.

## Run

```bash
make test
make sweep
```

## Final response format

After implementation, summarize:

1. Files changed.
2. Corrected competitive-case logic.
3. Decision enum behavior.
4. Tests added or updated.
5. Results of `make test` and `make sweep`.
6. Any tradeoffs or limitations.
