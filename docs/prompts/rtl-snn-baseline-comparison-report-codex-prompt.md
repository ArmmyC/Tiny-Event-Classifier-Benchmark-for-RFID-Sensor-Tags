# Codex Prompt: RTL SNN-vs-Baseline Comparison Report

You are working in the repository `Tiny-Event-Classifier-Benchmark-for-RFID-Sensor-Tags`.

Implement this spec:

```text
docs/specs/rtl-snn-baseline-comparison-report.md
```

## Goal

Add a comparison report that turns RTL simulation, synthesis, and VCD activity summaries into a clear `tiny_snn_v2`-vs-baseline hardware feasibility decision.

Do not add new RTL in this task.

## Required work

1. Add module:
   - `python/tinysnnrfid/compare_rtl_designs.py`
2. Add wrapper:
   - `python/compare_rtl_designs.py`
3. Add Makefile target:
   - `rtl-compare`
4. Read:
   - `results/rtl/rtl_summary.json`
   - `results/rtl/rtl_activity_summary.json`
5. Missing inputs must be allowed by default.
6. Write:
   - `results/rtl/rtl_comparison_summary.json`
   - `results/rtl/rtl_comparison_report.md`
7. Compare:
   - `threshold`
   - `fsm`
   - `lut_like`
   - `tiny_snn_v2`
8. Use `fsm` as the primary reference baseline.
9. Report simulation status, cell-count proxy, toggle-count proxy, and ratios versus FSM where available.
10. Produce a stable recommendation enum.
11. Update `build_research_report.py` to read `results/rtl/rtl_comparison_summary.json`.
12. Add research report input key `rtl_comparison`.
13. Add research report section `RTL SNN-vs-Baseline Comparison`.
14. Add tests that do not require RTL tools.

## Recommendation enum

Use one of:

```text
continue_snn_rtl_optimization
optimize_snn_rtl_before_more_features
prioritize_fsm_or_lut_rtl_baseline
insufficient_rtl_data
```

## Constraints

- Do not add new RTL modules.
- Do not add training.
- Do not add heavy dependencies.
- Do not require RTL tools for tests.
- Do not claim measured silicon power or energy.
- State clearly that cell counts and toggle counts are local-tool proxies, not silicon area or measured power.
- Keep generated outputs out of git.
- Keep existing workflows working.

## Tests

Add tests for:

1. Missing inputs produce `insufficient_rtl_data`.
2. Low synthetic cell/toggle ratios recommend `continue_snn_rtl_optimization`.
3. Medium ratios recommend `optimize_snn_rtl_before_more_features`.
4. High ratios recommend `prioritize_fsm_or_lut_rtl_baseline`.
5. Markdown and JSON comparison outputs are written.
6. Research report loads `rtl_comparison_summary.json` when present.
7. Research report includes `RTL SNN-vs-Baseline Comparison`.
8. `make test` passes without RTL tools.

## Run

```bash
make test
make rtl-compare
make research-report
```

Optional full workflow:

```bash
make rtl-vectors
make rtl-sim
make rtl-synth
make rtl-activity
make rtl-report
make rtl-compare
make research-report
```

## Final response

Summarize files changed, comparison logic, recommendation behavior, report integration, tests, command results, and limitations.
