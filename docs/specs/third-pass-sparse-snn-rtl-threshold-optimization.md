# Feature Spec: Third-Pass Sparse SNN RTL Threshold Optimization

## Goal

Run one more tightly bounded RTL area-optimization pass for `tiny_snn_v2_sparse_activity` to try to cross the current RTL comparison threshold.

The second-pass optimization result:

```text
tiny_snn_v2_sparse_activity simulation: pass, 320 passed / 0 failed
synthesis: pass
previous sparse cell count: 846
new sparse cell count: 691
reduction: 155 cells, about 18.3% lower
below 616 target: no
cell ratio vs FSM: 4.487
toggle ratio vs FSM: 0.967
recommendation: optimize_snn_rtl_before_more_features
```

The design is now close to the 4.0x FSM proxy threshold. This branch should try to reduce the sparse SNN below that threshold without changing behavior.

## Target

Current sparse SNN cell count proxy:

```text
691
```

Primary target:

```text
cell count < 616
```

This is the current less-than-4.0x-FSM threshold.

Minimum useful improvement:

```text
cell count <= 650
```

Stop after this branch unless a very clear, low-risk optimization remains.

## Required behavior

Preserve behavior of:

```text
rtl/snn/tiny_snn_v2_sparse_activity_detector.sv
```

The following must remain unchanged:

- detector interface,
- fixed sparse weights,
- hidden threshold,
- output threshold,
- leak value,
- membrane min/max behavior,
- reset-on-spike behavior,
- same-sample hidden spike to output drive behavior,
- sticky prediction behavior,
- Python classifier behavior,
- vector export behavior,
- RTL comparison decision semantics.

## Optimization directions

Focus on small structural reductions, not model changes.

Recommended ideas:

1. Inspect the synthesized JSON/log and identify the largest remaining cell contributors.
2. Simplify output-drive logic if possible. The current output weights are:

```text
[-1, 0, 1, -2, 1, 1]
```

This may be reducible to a small signed expression or table over spike bits without a generic signed adder tree.

3. Check whether drive-update helper functions duplicate logic after synthesis. Inline or consolidate only if it reduces cells.
4. Replace repeated constant-return functions, if they synthesize poorly, with direct assignments.
5. Use narrow localparams for thresholds instead of wider `int` params where useful.
6. Preserve case-table coverage and avoid latch inference.
7. Avoid broad `int` arithmetic in the sparse datapath.

## Non-goals

Do not add:

- new SNN variants,
- training,
- runtime-programmable weights,
- new software search,
- new benchmark scenarios,
- new RTL comparison thresholds,
- silicon area claims,
- measured power claims,
- signoff claims.

## Evidence requirements

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

Required outputs:

- sparse SNN simulation passes,
- sparse SNN synthesis succeeds,
- no latch inference errors,
- sparse SNN cell count is reported,
- sparse SNN toggle ratio is reported,
- RTL comparison recommendation is reported.

## Tests

Add or update tests that do not require Yosys:

1. Fixed sparse weights are unchanged.
2. Detector interface is unchanged.
3. Latch-intended constructs are not introduced.
4. Broad `int` datapath arithmetic is not reintroduced.
5. Any new lookup/case logic has covered default paths.
6. Existing vector/export/equivalence tests continue to pass.
7. Existing RTL runner tests continue to pass.

Optional integration test:

- If Yosys is available, synthesize only `tiny_snn_v2_sparse_activity` and assert JSON output exists. Skip if unavailable.

## Final report

Codex should report:

```text
old sparse cell count: 691
new sparse cell count
absolute reduction
percent reduction
below 616 target: yes/no
cell ratio vs FSM
toggle ratio vs FSM
RTL recommendation
whether another optimization branch is justified
```

## Definition of done

- Behavior is preserved.
- Simulation passes.
- Synthesis succeeds.
- Cell count is lower than 691.
- Preferably cell count is below 616.
- If below 616 is not reached, report whether there is a clear next optimization or whether to stop and document the current tradeoff.
- Generated outputs are not committed.
