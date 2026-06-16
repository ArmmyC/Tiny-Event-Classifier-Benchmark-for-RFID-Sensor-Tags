# Codex Prompt: Second-Pass Sparse SNN RTL Area Optimization

Implement:

```text
docs/specs/second-pass-sparse-snn-rtl-area-optimization.md
```

Goal: further reduce the Yosys cell-count proxy of `tiny_snn_v2_sparse_activity` while preserving behavior.

Current evidence after first optimization:
- sparse SNN simulation passes: 320 passed / 0 failed
- sparse SNN synthesis succeeds
- old sparse cell count before first optimization: 5082
- current sparse cell count: 846
- first-pass reduction: about 83.4%
- current cell ratio vs FSM: 5.494
- current toggle ratio vs FSM: 0.967
- RTL recommendation: `optimize_snn_rtl_before_more_features`

Required:
1. Optimize only `rtl/snn/tiny_snn_v2_sparse_activity_detector.sv` unless tests/docs need updates.
2. Keep detector interface unchanged.
3. Keep all fixed sparse weights unchanged.
4. Keep inference semantics unchanged:
   - leak and clip before drive
   - clip after drive
   - reset hidden membrane on spike
   - same-sample hidden spike drives output membrane
   - sticky prediction after output threshold crossing
5. Do not change Python classifiers, vector export, or RTL comparison semantics.
6. Avoid latch inference.
7. Do not reintroduce broad `int` arithmetic in the sparse RTL datapath.
8. Try to reduce cell count below 616 if practical; stretch target is <=462.
9. Suggested directions:
   - inspect Yosys JSON/log for largest cell contributors
   - simplify hidden spike/update logic into small predicates or case tables
   - replace generic arithmetic with small unsigned/saturating logic where safe
   - avoid duplicated generic helper logic if explicit per-neuron logic is smaller
10. Add/update tests that do not require Yosys:
   - sparse weights unchanged
   - interface unchanged
   - no latch-intended constructs
   - no broad int datapath in sparse RTL
   - if lookup/case tables are used, required cases are covered

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

Final response:
Report old sparse cell count 846, new sparse cell count, absolute reduction, percent reduction, cell ratio vs FSM, toggle ratio vs FSM, and RTL recommendation.

Constraints:
- Do not add dependencies.
- Do not commit generated outputs.
- Do not claim silicon area or measured power.
