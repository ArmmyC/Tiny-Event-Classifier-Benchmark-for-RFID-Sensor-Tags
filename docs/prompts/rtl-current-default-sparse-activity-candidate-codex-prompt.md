# Codex Prompt: RTL Candidate for current_default_sparse_activity

Implement:

```text
docs/specs/rtl-current-default-sparse-activity-candidate.md
```

Goal: add a bounded RTL feasibility prototype for the best v2 temporal-hard software candidate, `current_default_sparse_activity`, without changing the existing default tiny_snn_v2 RTL.

Required:

1. Add `rtl/snn/tiny_snn_v2_sparse_activity_detector.sv`.
2. Use the same streaming interface as existing detectors.
3. Implement fixed weights for `current_default_sparse_activity`:
   - ch0 `[4, 0, 0, -1, 2, 0]`
   - ch1 `[0, 3, 0, -1, 2, 2]`
   - ch2 `[0, 0, 4, -1, 0, 2]`
   - ch3 `[-1, -1, -1, 6, -1, -1]`
   - output `[-1, 0, 1, -2, 1, 1]`
4. Keep existing `rtl/snn/tiny_snn_v2_detector.sv` unchanged.
5. Update `python/tinysnnrfid/export_rtl_vectors.py` to emit `expected_tiny_snn_v2_sparse_activity`.
6. Update testbench and RTL scripts to simulate/synthesize the new design.
7. Add expected outputs:
   - `results/rtl/sim_tiny_snn_v2_sparse_activity.log`
   - `results/rtl/vcd_tiny_snn_v2_sparse_activity.vcd`
   - `results/rtl/synth_tiny_snn_v2_sparse_activity.json`
   - `results/rtl/synth_tiny_snn_v2_sparse_activity.log`
8. Update RTL summary, VCD activity summary, and RTL comparison to include `tiny_snn_v2_sparse_activity`.
9. Add tests that do not require Icarus Verilog or Yosys.

Constraints:

- Do not add training.
- Do not add runtime-programmable weights.
- Do not add heavy dependencies.
- Do not require RTL tools for unit tests.
- Do not claim measured silicon power or silicon area.
- Do not commit generated outputs.
- Keep existing baseline and default SNN RTL flow working.

Run:

```bash
python -m pytest
make rtl-vectors
make rtl-sim
make rtl-synth
make rtl-activity
make rtl-report
make rtl-compare
```

Final response: summarize changed files, tests run, generated outputs, and whether sparse-activity RTL comparison data is available.
