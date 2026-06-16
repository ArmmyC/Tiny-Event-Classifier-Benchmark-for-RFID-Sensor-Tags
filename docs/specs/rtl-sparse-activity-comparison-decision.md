# Bugfix Spec: RTL Sparse-Activity Comparison Decision

## Goal

Fix the RTL comparison decision logic so the newly added `tiny_snn_v2_sparse_activity` candidate is the candidate being judged for RTL feasibility.

The current implementation adds the sparse-activity RTL design to simulation, synthesis, activity summaries, and reports. However, the top-level RTL comparison recommendation still appears to be based on the older `tiny_snn_v2` design rather than the new sparse-activity candidate.

This can produce a misleading product decision: the report lists sparse-activity ratios, but the recommendation is still about the old default SNN RTL.

## Required behavior

Use FSM as the reference baseline, as before.

Use this as the primary SNN candidate for the top-level RTL comparison recommendation:

```text
tiny_snn_v2_sparse_activity
```

Keep reporting the older default design as context:

```text
tiny_snn_v2
```

## Required changes

Update:

```text
python/tinysnnrfid/compare_rtl_designs.py
```

Required fields in `rtl_comparison_summary.json`:

```text
reference_design: fsm
candidate_design: tiny_snn_v2_sparse_activity
legacy_snn_design: tiny_snn_v2
```

The top-level fields:

```text
recommendation
reason
```

must be based on `tiny_snn_v2_sparse_activity` vs `fsm`, not the older `tiny_snn_v2`.

Keep both contexts:

```text
tiny_snn_v2_context
tiny_snn_v2_sparse_activity_context
```

Add or update Markdown report wording so it is obvious that:

- the primary candidate is `tiny_snn_v2_sparse_activity`,
- `tiny_snn_v2` is shown only as legacy/default SNN context,
- cell counts and toggle counts are local-tool proxies, not silicon area or measured power.

## Recommendation logic

Use the existing threshold logic, but apply it to `tiny_snn_v2_sparse_activity`:

- If sparse candidate simulation is missing/not passing: `insufficient_rtl_data`.
- If FSM simulation is missing/not passing: `insufficient_rtl_data`.
- If sparse candidate cell/toggle ratios are both present and both <= 2.0: `continue_snn_rtl_optimization`.
- If at least one sparse candidate ratio is <= 4.0: `optimize_snn_rtl_before_more_features`.
- Otherwise: `prioritize_fsm_or_lut_rtl_baseline`.

Do not require the older `tiny_snn_v2` simulation to pass in order to judge the sparse candidate.

## Research report integration

Update:

```text
python/tinysnnrfid/build_research_report.py
```

if needed so the RTL SNN-vs-Baseline section reports:

```text
Candidate design: tiny_snn_v2_sparse_activity
Legacy/default SNN context: tiny_snn_v2
```

The main recommendation displayed there should match the sparse-candidate decision.

## Tests

Update tests so they verify:

1. `rtl_comparison_summary.json` includes `candidate_design: tiny_snn_v2_sparse_activity`.
2. Top-level recommendation is based on sparse candidate ratios, not default `tiny_snn_v2` ratios.
3. If default `tiny_snn_v2` fails simulation but sparse candidate and FSM pass, the sparse-candidate comparison can still proceed.
4. If sparse candidate fails simulation, recommendation is `insufficient_rtl_data`.
5. Markdown report states the primary candidate is `tiny_snn_v2_sparse_activity`.
6. Research report shows the sparse candidate as the candidate design when RTL comparison is available.
7. Existing rows for threshold, fsm, lut_like, tiny_snn_v2, and tiny_snn_v2_sparse_activity remain present.

Do not require Icarus Verilog or Yosys for tests.

## Constraints

- Do not add new RTL.
- Do not change detector weights.
- Do not change vector export.
- Do not add training.
- Do not add heavy dependencies.
- Do not claim measured silicon power or silicon area.
- Do not commit generated outputs.

## Manual verification

Run:

```bash
python -m pytest
make rtl-report
make rtl-compare
make research-report
```

If local RTL tools are available, also run:

```bash
make rtl-vectors
make rtl-sim
make rtl-synth
make rtl-activity
make rtl-report
make rtl-compare
```

## Definition of done

- Sparse-activity candidate drives the top-level RTL recommendation.
- Legacy/default tiny_snn_v2 remains visible only as context.
- Tests cover sparse-candidate decision semantics.
- Existing RTL flow remains working.
