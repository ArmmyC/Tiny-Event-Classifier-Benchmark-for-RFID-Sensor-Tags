# Codex Prompt: Fix SNN RTL Yosys Latch Inference

Implement:

```text
docs/specs/fix-snn-rtl-yosys-latch-inference.md
```

Goal: fix Yosys latch inference in the SNN RTL modules so the sparse-activity candidate can produce synthesis evidence.

Context:
- `tiny_snn_v2_sparse_activity` simulation now passes.
- VCD toggles are available.
- Synthesis for `tiny_snn_v2_sparse_activity_detector.sv` fails because Yosys reports latch inference.
- RTL comparison remains `insufficient_rtl_data` because sparse SNN cell-count proxy is missing.

Required:
1. Update both:
   - `rtl/snn/tiny_snn_v2_detector.sv`
   - `rtl/snn/tiny_snn_v2_sparse_activity_detector.sv`
2. Remove latch inference from SNN `always_comb` logic.
3. Keep detector interfaces unchanged.
4. Keep all fixed weights unchanged.
5. Keep inference semantics unchanged:
   - leak and clip before drive
   - clip after drive
   - reset hidden membrane on spike
   - same-sample hidden spike drives output membrane
   - sticky prediction after output threshold crossing
6. Do not change Python classifiers, vector export, or RTL comparison decision semantics.
7. Add tests that do not require Yosys:
   - both SNN RTL modules initialize combinational temporaries before conditional use
   - no latch-intended constructs are introduced
   - existing RTL runner/vector tests continue to pass

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

Expected:
- sparse SNN simulation passes
- `results/rtl/synth_tiny_snn_v2_sparse_activity.json` exists
- sparse SNN synth log has no latch inference error
- RTL comparison has non-null sparse cell and toggle ratios vs FSM

Constraints:
- Do not add dependencies.
- Do not commit generated outputs.
- Do not claim silicon area or measured power.

Final response:
Summarize changed files, tests run, whether Yosys synthesis now succeeds for the sparse SNN, and the updated RTL comparison recommendation.
