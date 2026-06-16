# Codex Prompt: Optimize Sparse SNN RTL Cell-Count Proxy

Implement:

```text
docs/specs/optimize-sparse-snn-rtl-cell-count.md
```

Goal: reduce the Yosys cell-count proxy of `tiny_snn_v2_sparse_activity` while preserving behavior.

Current evidence:
- sparse SNN simulation passes: 320 passed / 0 failed
- sparse SNN synthesis succeeds
- sparse SNN cell count proxy: 5082
- FSM cell count proxy: 154
- sparse cell ratio vs FSM: 33.000
- sparse toggle ratio vs FSM: 0.967
- RTL recommendation: `optimize_snn_rtl_before_more_features`

Required:
1. Optimize `rtl/snn/tiny_snn_v2_sparse_activity_detector.sv` for lower Yosys cell count.
2. Keep detector interface unchanged.
3. Keep all fixed sparse weights unchanged.
4. Keep inference semantics unchanged:
   - leak and clip before drive
   - clip after drive
   - reset hidden membrane on spike
   - same-sample hidden spike drives output membrane
   - sticky prediction after output threshold crossing
5. Prefer narrow explicit signed logic types instead of broad `int` datapath temporaries/functions.
6. Avoid unnecessary 32-bit adders/comparators.
7. Avoid latch inference.
8. Do not change Python classifiers, vector export, or RTL comparison decision semantics.
9. Add tests that do not require Yosys:
   - sparse RTL no longer uses broad `int` datapath temporaries in the main combinational datapath
   - sparse weights are unchanged
   - interface is unchanged
   - no latch-intended constructs are introduced
10. Optional: if Yosys is available, add a skipped integration test that checks sparse synthesis JSON can be produced.

Target:
- Simulation still passes.
- Synthesis still succeeds.
- No latch inference errors.
- Cell count is materially lower than 5082, preferably at least 30% lower if practical.
- Toggle ratio should not become much worse than 0.967 unless cell-count reduction is very large.

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
Summarize changed files, tests run, sparse simulation result, sparse synthesis result, new sparse cell count, cell ratio vs FSM, toggle ratio vs FSM, and updated RTL recommendation.

Constraints:
- Do not add dependencies.
- Do not commit generated outputs.
- Do not claim silicon area or measured power.
