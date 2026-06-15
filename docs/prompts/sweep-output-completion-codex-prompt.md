# Codex Prompt: Complete Sweep Outputs and Decision Report

You are working in the repository `Tiny-Event-Classifier-Benchmark-for-RFID-Sensor-Tags`.

Implement the feature spec at:

```text
docs/specs/sweep-output-completion-and-decision-report.md
```

## Goal

Complete the experiment sweep output layer so the benchmark becomes a research decision tool.

Right now the sweep runner can execute benchmark grids and write JSON plus Markdown, but it still needs CSV output, F1-tolerance comparison, activity-aware competitive cases, and a clear decision summary.

The goal is to answer:

```text
Is tiny_snn_v2 ever better than FSM, and if not, what evidence tells us what to improve next?
```

## Required work

1. Add `results/sweeps/sweep_summary.csv` output.
2. Use Python standard library `csv`; do not add pandas.
3. CSV must have one row per sweep run per classifier.
4. Add `comparison.f1_tolerance` to `configs/sweep_default.json`.
5. Validate `comparison.f1_tolerance` as a non-negative number.
6. Improve `compare_candidate_to_reference` so it computes:
   - `candidate_f1_wins`
   - `candidate_f1_losses`
   - `candidate_f1_ties_within_tolerance`
   - `candidate_activity_wins`
   - `candidate_activity_wins_within_f1_tolerance`
   - `candidate_competitive_runs`
7. Define a competitive run as either:
   - candidate F1 is greater than reference F1, or
   - candidate activity is lower and candidate F1 is within tolerance of reference F1.
8. Add `Competitive Cases` section to `sweep_report.md`.
9. Add `Decision Summary` section to `sweep_report.md`.
10. Add top-level `decision` object to `sweep_results.json`.
11. Update README to mention `sweep_summary.csv`.
12. Update `make clean` to remove sweep outputs without deleting tracked `.gitkeep` files.
13. Add tests for CSV output, tolerance comparison, competitive cases, and decision summary.

## Decision rules

Use simple deterministic rules:

```text
If tiny_snn_v2 has at least one F1 win or at least one activity win within F1 tolerance:
    recommendation = continue_snn_optimization
Else if no classifier clearly dominates across scenarios:
    recommendation = add_harder_temporal_scenarios
Else:
    recommendation = prioritize_fsm_or_lut_rtl_baseline
```

The report must explain the recommendation in plain language.

## Constraints

- Do not implement RTL.
- Do not implement training.
- Do not add pandas, PyTorch, TensorFlow, JAX, or other heavyweight dependencies.
- Do not call activity proxy hardware power.
- Keep existing commands working:

```bash
make data
make eval
make benchmark
make sweep
make test
```

- Do not commit generated outputs under `results/sweeps/`.

## Expected generated outputs

After running `make sweep`, these files should exist locally but should not be committed:

```text
results/sweeps/sweep_results.json
results/sweeps/sweep_summary.csv
results/sweeps/sweep_report.md
```

## Tests to run

Run:

```bash
make test
make sweep
```

## Definition of done

The task is complete only when:

- `make test` passes.
- `make sweep` works.
- Sweep JSON, CSV, and Markdown outputs are generated.
- CSV has one row per run per classifier.
- `sweep_results.json` includes a top-level `decision` object.
- Markdown report includes `Competitive Cases` and `Decision Summary`.
- Activity proxy is still clearly described as software proxy, not hardware power.
- No generated sweep artifacts are committed.

## Final response format

After implementation, summarize:

1. Files changed.
2. CSV output behavior.
3. New comparison fields.
4. Decision summary behavior.
5. Tests added or updated.
6. Result of `make test` and `make sweep`.
7. Any tradeoffs or limitations.
