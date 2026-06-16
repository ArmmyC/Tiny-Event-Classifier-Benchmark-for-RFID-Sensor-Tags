# Feature Spec: RTL SNN-vs-Baseline Comparison Report

## Goal

Add a comparison report that turns RTL simulation, synthesis, and VCD activity summaries into a clear SNN-vs-baseline hardware feasibility decision.

The repo now has:

- baseline RTL detectors,
- `tiny_snn_v2` RTL prototype,
- Python-golden RTL vectors,
- optional RTL simulation,
- optional synthesis cell-count proxy,
- optional VCD toggle-count proxy,
- `rtl-report`,
- consolidated `research-report`.

The missing piece is a direct table answering:

```text
How much larger or more active is tiny_snn_v2 RTL than FSM/LUT/threshold baselines, and is it still worth optimizing?
```

This task does not add new RTL. It only summarizes and compares existing generated RTL evidence.

## Non-goals

Do not implement:

- new RTL modules,
- training,
- new datasets,
- vendor-specific flows,
- physical design,
- silicon power claims.

## Required command

Add module:

```text
python/tinysnnrfid/compare_rtl_designs.py
```

Add wrapper:

```text
python/compare_rtl_designs.py
```

Add Makefile target:

```makefile
rtl-compare:
	python python/compare_rtl_designs.py
```

## Inputs

Read:

```text
results/rtl/rtl_summary.json
results/rtl/rtl_activity_summary.json
```

Missing files must be allowed by default.

## Outputs

Write:

```text
results/rtl/rtl_comparison_summary.json
results/rtl/rtl_comparison_report.md
```

Generated outputs must not be committed.

## Required comparison behavior

Compare these designs when data exists:

```text
threshold
fsm
lut_like
tiny_snn_v2
```

Use `fsm` as the primary baseline reference.

For each design, report:

- simulation status,
- synthesis cell-count proxy if available,
- VCD total-toggle proxy if available,
- cell-count ratio versus FSM if available,
- toggle-count ratio versus FSM if available.

For `tiny_snn_v2`, additionally report:

- whether simulation passed,
- whether cell-count proxy is higher/lower than FSM,
- whether toggle-count proxy is higher/lower than FSM,
- missing evidence warnings.

## Recommendation enum

Use one of:

```text
continue_snn_rtl_optimization
optimize_snn_rtl_before_more_features
prioritize_fsm_or_lut_rtl_baseline
insufficient_rtl_data
```

Suggested rules:

1. If `tiny_snn_v2` simulation is missing or not pass, recommendation is `insufficient_rtl_data`.
2. If FSM simulation is missing or not pass, recommendation is `insufficient_rtl_data`.
3. If cell and toggle data are both missing for either FSM or `tiny_snn_v2`, recommendation is `insufficient_rtl_data`.
4. If `tiny_snn_v2` cell ratio <= 2.0 and toggle ratio <= 2.0, recommendation is `continue_snn_rtl_optimization`.
5. If `tiny_snn_v2` cell ratio <= 4.0 or toggle ratio <= 4.0, recommendation is `optimize_snn_rtl_before_more_features`.
6. Otherwise recommendation is `prioritize_fsm_or_lut_rtl_baseline`.

The thresholds should be configurable constants in code.

## Markdown report sections

```text
# RTL SNN-vs-Baseline Comparison Report
## Inputs Found
## Simulation Status
## Cell Count Proxy Comparison
## Toggle Count Proxy Comparison
## Tiny SNN v2 Decision
## Notes and Limitations
```

The report must clearly say:

```text
Cell counts and toggle counts are local-tool proxies, not silicon area or measured power.
```

## Research report integration

Update `python/tinysnnrfid/build_research_report.py` so it also reads:

```text
results/rtl/rtl_comparison_summary.json
```

Add input key:

```text
rtl_comparison
```

Add a section or subsection:

```text
## RTL SNN-vs-Baseline Comparison
```

Include:

- recommendation enum,
- reason,
- tiny_snn_v2 cell ratio versus FSM if available,
- tiny_snn_v2 toggle ratio versus FSM if available,
- limitation note.

The overall research recommendation may use this as context, but do not let it override software accuracy evidence unless the implementation is already clearly described and tested.

## Tests

Add tests that do not require RTL tools:

1. Missing inputs produce `insufficient_rtl_data`.
2. Synthetic passing simulation plus low cell/toggle ratios recommends `continue_snn_rtl_optimization`.
3. Synthetic medium ratios recommend `optimize_snn_rtl_before_more_features`.
4. Synthetic high ratios recommend `prioritize_fsm_or_lut_rtl_baseline`.
5. Markdown and JSON comparison outputs are written.
6. Research report loads `rtl_comparison_summary.json` when present.
7. Research report includes `RTL SNN-vs-Baseline Comparison`.
8. `make test` passes without RTL tools installed.

## Manual workflow

Run:

```bash
make rtl-vectors
make rtl-sim
make rtl-synth
make rtl-activity
make rtl-report
make rtl-compare
make research-report
```

If RTL tools are missing, `make rtl-compare` should still write a report with missing-data status.

## Definition of done

This task is complete when:

- `make rtl-compare` works.
- JSON and Markdown comparison outputs are generated.
- Missing RTL evidence is handled clearly.
- Tiny SNN vs FSM ratios are reported when available.
- A stable RTL recommendation enum is produced.
- Research report includes the comparison.
- Tests cover recommendation branches.
- Existing workflows remain usable.
- No generated outputs are committed.
