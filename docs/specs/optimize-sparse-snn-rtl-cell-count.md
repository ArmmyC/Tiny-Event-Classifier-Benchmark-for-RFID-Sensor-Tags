# Feature Spec: Optimize Sparse SNN RTL Cell-Count Proxy

## Goal

Optimize the synthesizable RTL implementation of the sparse-activity SNN candidate before adding any more features.

The latest complete RTL evidence shows:

```text
candidate: tiny_snn_v2_sparse_activity
simulation: pass, 320 passed / 0 failed
synthesis: pass
cell count proxy: 5082
FSM cell count proxy: 154
cell ratio vs FSM: 33.000
toggle ratio vs FSM: 0.967
recommendation: optimize_snn_rtl_before_more_features
```

This is the first complete hardware-proxy result for the sparse SNN. It is promising on toggle proxy but far too large on cell-count proxy. The next branch should reduce RTL cell count while preserving behavior.

## Non-goals

Do not add:

- new SNN variants,
- training,
- runtime-programmable weights,
- new software search,
- new benchmark scenarios,
- silicon area claims,
- measured power claims,
- signoff claims.

This is a bounded RTL implementation optimization branch only.

## Required behavior

Keep the externally visible behavior of:

```text
rtl/snn/tiny_snn_v2_sparse_activity_detector.sv
```

unchanged.

It must still match Python-golden vectors exported by:

```text
python/tinysnnrfid/export_rtl_vectors.py
```

The following must remain unchanged:

- detector ports,
- fixed weights,
- hidden threshold,
- output threshold,
- leak value,
- membrane min/max semantics,
- reset-on-spike behavior,
- same-sample hidden spike to output drive behavior,
- sticky prediction behavior.

## Optimization direction

The current SNN RTL likely synthesizes large because it uses broad `int` arithmetic and `int`-returning weight functions. Optimize for local open-source synthesis proxy size by making the datapath explicit and narrow.

Recommended techniques:

1. Replace `int` datapath temporaries with narrow signed logic types sized from the actual value ranges.
2. Replace `input_weight()` and `output_weight()` `int` functions with narrower signed constants/functions or static combinational tables.
3. Avoid unnecessary 32-bit adders/comparators.
4. Keep membrane registers narrow, but large enough for `MEMBRANE_MIN..MEMBRANE_MAX` and intermediate drive before clipping.
5. Keep loops only if Yosys synthesizes them compactly; otherwise unroll or restructure carefully.
6. Avoid introducing latches.
7. Avoid increasing toggle count substantially while reducing cell count.

Do not optimize by changing the classifier behavior.

## Evidence target

This is a first optimization pass. The goal is not to beat FSM cell count yet.

Target outcome:

- `tiny_snn_v2_sparse_activity` simulation still passes.
- Yosys synthesis still succeeds.
- No latch inference errors.
- Sparse SNN cell count proxy is materially lower than 5082.
- Prefer at least 30% cell-count reduction versus the current sparse SNN RTL, if practical.
- Toggle ratio versus FSM should not become much worse than the current 0.967 unless cell-count reduction is very large.

If the target is not reached, still report the best achieved result honestly.

## Reporting

Existing reports should continue to work:

```text
results/rtl/rtl_summary.json
results/rtl/rtl_activity_summary.json
results/rtl/rtl_comparison_summary.json
results/rtl/rtl_comparison_report.md
results/research_decision_report.md
```

Do not change RTL comparison decision semantics unless required by a bug.

## Tests

Add tests that do not require Yosys:

1. Sparse SNN RTL uses narrow explicit logic types for core datapath temporaries instead of broad `int` temporaries.
2. Fixed sparse SNN weights are unchanged.
3. Detector interface is unchanged.
4. No latch-intended constructs are introduced.
5. Existing vector/export/equivalence tests continue to pass.
6. Existing RTL runner tests continue to pass.

Optional integration test:

- If Yosys is available, run synthesis for `tiny_snn_v2_sparse_activity` and assert JSON output exists. This must be skipped when Yosys is unavailable.

## Manual workflow

Run:

```bash
python -m pytest
make rtl-doctor
make rtl-vectors
make rtl-sim
make rtl-synth
make rtl-activity
make rtl-report
make rtl-compare
make research-report
```

Then inspect:

```text
results/rtl/rtl_comparison_summary.json
results/rtl/rtl_comparison_report.md
results/research_decision_report.md
```

## Definition of done

- Sparse SNN RTL behavior is preserved.
- Sparse SNN simulation passes.
- Sparse SNN synthesis succeeds.
- Sparse SNN cell-count proxy is reduced from the current 5082 baseline, ideally by at least 30%.
- RTL comparison report is regenerated and still includes sparse cell/toggle ratios versus FSM.
- No generated outputs are committed.
