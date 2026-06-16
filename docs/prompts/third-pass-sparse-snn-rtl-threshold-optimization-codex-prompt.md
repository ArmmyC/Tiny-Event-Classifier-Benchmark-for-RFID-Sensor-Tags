# Codex Prompt: Third-Pass Sparse SNN RTL Threshold Optimization

Implement:

```text
docs/specs/third-pass-sparse-snn-rtl-threshold-optimization.md
```

Goal: try one more bounded RTL optimization pass to reduce `tiny_snn_v2_sparse_activity` below the current 4.0x-FSM cell-ratio threshold while preserving behavior.

Current evidence:
- sparse SNN simulation passes: 320 passed / 0 failed
- sparse SNN synthesis succeeds
- previous sparse cell count: 846
- current sparse cell count: 691
- second-pass reduction: 155 cells, about 18.3%
- below 616 target: no
- current cell ratio vs FSM: 4.487
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
8. Try to reduce cell count below 616. Minimum useful improvement is <=650.
9. Suggested directions:
   - inspect Yosys JSON/log for largest remaining cell contributors
   - simplify output-drive logic for output weights [-1, 0, 1, -2, 1, 1]
   - avoid generic signed adder trees if a smaller expression/table works
   - inline or consolidate helper logic only if it reduces cells
   - replace constant-return helper functions if they synthesize poorly
   - use narrow localparams for thresholds where useful
10. Add/update tests that do not require Yosys:
   - sparse weights unchanged
   - interface unchanged
   - no latch-intended constructs
   - no broad int datapath in sparse RTL
   - any new lookup/case logic has safe default paths

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
Report old sparse cell count 691, new sparse cell count, absolute reduction, percent reduction, below-616 yes/no, cell ratio vs FSM, toggle ratio vs FSM, RTL recommendation, and whether another optimization branch is justified.

Constraints:
- Do not add dependencies.
- Do not commit generated outputs.
- Do not claim silicon area or measured power.
