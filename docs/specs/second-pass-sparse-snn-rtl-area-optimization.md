# Feature Spec: Second-Pass Sparse SNN RTL Area Optimization

## Goal

Run a second focused RTL area-optimization pass for the sparse-activity SNN candidate.

The first optimization pass was successful:

```text
tiny_snn_v2_sparse_activity simulation: pass, 320 passed / 0 failed
synthesis: pass
previous sparse cell count: 5082
new sparse cell count: 846
reduction: 4236 cells, about 83.4% lower
FSM cell count proxy: about 154
cell ratio vs FSM: 5.494
toggle ratio vs FSM: 0.967
recommendation: optimize_snn_rtl_before_more_features
```

This is strong progress, but the sparse SNN is still too large versus the FSM reference. The next branch should reduce cell count further before adding features or changing the model.

## Non-goals

Do not add:

- new SNN variants,
- training,
- runtime-programmable weights,
- new benchmark scenarios,
- new software search,
- RTL comparison semantic changes,
- silicon area claims,
- measured power claims,
- signoff claims.

This is still an implementation optimization branch only.

## Required behavior

Keep the behavior of:

```text
rtl/snn/tiny_snn_v2_sparse_activity_detector.sv
```

unchanged.

The module must continue to match Python-golden vectors from:

```text
python/tinysnnrfid/export_rtl_vectors.py
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
- sticky prediction behavior.

## Area target

Current sparse SNN cell count proxy after first optimization:

```text
846
```

Target outcome:

```text
cell count < 616
```

This corresponds to less than 4.0x the current FSM proxy cell count of about 154.

Stretch target:

```text
cell count <= 462
```

This corresponds to 3.0x FSM.

If these targets are not practical without changing behavior, report the best achieved result honestly.

## Recommended optimization directions

Focus on structural simplification, not model changes.

Suggested approaches:

1. Inspect Yosys JSON/log to identify the largest cell contributors in `tiny_snn_v2_sparse_activity`.
2. Replace arithmetic-heavy hidden update logic with simpler threshold predicates where possible.
3. For each hidden neuron, derive whether it can spike from current 3-bit membrane and current 4-bit input sample without building generic signed adders.
4. Consider small case tables or simplified boolean comparators for hidden update and next membrane where this reduces cells.
5. Avoid broad signed arithmetic where a small unsigned/saturating transform is enough.
6. Avoid generic helper functions if Yosys duplicates them into larger logic than explicit per-neuron expressions.
7. Preserve the current 3-bit membrane storage if possible.
8. Avoid latch inference.
9. Do not optimize by changing the classifier weights or thresholds.

## Evidence requirements

Run the full flow:

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
- RTL comparison report is regenerated.

## Reporting

In the final Codex response, report:

```text
old sparse cell count: 846
new sparse cell count
absolute cell reduction
percent cell reduction
cell ratio vs FSM
toggle ratio vs FSM
RTL recommendation
```

Do not claim silicon area or measured power. These are local-tool proxies only.

## Tests

Add or update tests that do not require Yosys:

1. Fixed sparse weights are unchanged.
2. Detector interface is unchanged.
3. Latch-intended constructs are not introduced.
4. Main sparse RTL datapath does not reintroduce broad `int` arithmetic.
5. If using lookup/case tables, tests confirm all required input/membrane cases are covered.
6. Existing vector/export/equivalence tests continue to pass.
7. Existing RTL runner tests continue to pass.

Optional integration test:

- If Yosys is available, synthesize only `tiny_snn_v2_sparse_activity` and assert JSON output exists. Skip if Yosys is unavailable.

## Definition of done

- Sparse SNN behavior is preserved.
- Simulation passes.
- Synthesis succeeds.
- Cell count is lower than 846.
- Preferably cell count is below 616.
- Toggle ratio does not become substantially worse than 0.967 unless cell-count reduction is large.
- Generated outputs are not committed.
