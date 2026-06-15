# Codex Prompt: Focused Sweep Output Completion Patch

You are working in the repository `Tiny-Event-Classifier-Benchmark-for-RFID-Sensor-Tags`.

Implement the focused patch spec at:

```text
docs/specs/sweep-output-completion-patch.md
```

## Goal

Complete the existing sweep runner so `make sweep` produces a decision-ready research report.

The current repo state still has these gaps:

- `run_sweep.py` writes JSON and Markdown, but not CSV.
- `configs/sweep_default.json` does not include `comparison.f1_tolerance`.
- `compare_candidate_to_reference` only counts F1 wins/losses.
- There is no activity-within-F1-tolerance comparison.
- There is no top-level `decision` object in `sweep_results.json`.
- The Markdown sweep report has no `Competitive Cases` section.
- The Markdown sweep report has no `Decision Summary` section.

## Required files to modify

Modify only these unless a test genuinely requires another file:

```text
python/tinysnnrfid/run_sweep.py
configs/sweep_default.json
README.md
Makefile
tests/test_sweep.py
```

Do not modify classifiers.
Do not modify dataset generation.
Do not modify generated outputs.

## Required implementation

1. Add CSV output:

```text
results/sweeps/sweep_summary.csv
```

CSV must use Python standard library `csv`, not pandas.

2. CSV must contain one row per sweep run per classifier.

Required CSV columns:

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

3. Add `comparison.f1_tolerance` to `configs/sweep_default.json`:

```json
"f1_tolerance": 0.03
```

4. Validate `comparison.f1_tolerance` as a non-negative int or float, not bool.

5. Update comparison logic so each row includes:

```text
f1_delta
activity_delta
within_f1_tolerance
candidate_activity_lower
competitive_reason
```

6. A run is competitive if:

```text
candidate_f1 > reference_f1
or
candidate_activity < reference_activity and abs(candidate_f1 - reference_f1) <= f1_tolerance
```

7. Add comparison fields:

```text
candidate_f1_wins
candidate_f1_losses
candidate_f1_ties_within_tolerance
candidate_activity_wins
candidate_activity_wins_within_f1_tolerance
candidate_competitive_runs
```

8. Add top-level `decision` object to `sweep_results.json`.

Decision rules:

```text
If candidate_f1_wins > 0 or candidate_activity_wins_within_f1_tolerance > 0:
    recommendation = continue_snn_optimization
Else if best_by_scenario contains more than one winning classifier:
    recommendation = add_harder_temporal_scenarios
Else:
    recommendation = prioritize_fsm_or_lut_rtl_baseline
```

9. Add Markdown report sections:

```text
## Competitive Cases
## Decision Summary
```

10. Update README to mention `sweep_summary.csv`.

11. Update `make clean` to clean sweep outputs.

12. Add or update tests for:

- CSV creation.
- CSV columns.
- CSV row count.
- `f1_tolerance` validation.
- activity win within F1 tolerance.
- competitive cases.
- decision object.
- Markdown sections.

## Constraints

- Do not implement RTL.
- Do not implement training.
- Do not add pandas or heavyweight dependencies.
- Do not call activity proxy hardware power.
- Do not commit generated files under `results/sweeps/`.

## Commands to run

Run:

```bash
make test
make sweep
```

## Definition of done

The task is complete only when:

- `make test` passes.
- `make sweep` works.
- `results/sweeps/sweep_results.json` is generated.
- `results/sweeps/sweep_summary.csv` is generated.
- `results/sweeps/sweep_report.md` is generated.
- CSV has one row per run per classifier.
- JSON has top-level `decision`.
- Markdown has `Competitive Cases` and `Decision Summary`.
- No generated sweep outputs are committed.

## Final response format

After implementation, summarize:

1. Files changed.
2. CSV behavior.
3. Comparison behavior.
4. Decision behavior.
5. Tests added or updated.
6. Result of `make test`.
7. Result of `make sweep`.
8. Any tradeoffs.
