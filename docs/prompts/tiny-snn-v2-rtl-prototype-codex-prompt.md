# Codex Prompt: Tiny SNN v2 RTL Prototype

You are working in the repository `Tiny-Event-Classifier-Benchmark-for-RFID-Sensor-Tags`.

Implement this spec:

```text
docs/specs/tiny-snn-v2-rtl-prototype.md
```

## Goal

Add a bounded RTL prototype for fixed-weight `tiny_snn_v2` inference so it can be compared against the existing RTL baselines.

This is a feasibility prototype, not final silicon design.

## Required work

1. Add RTL module:
   - `rtl/snn/tiny_snn_v2_detector.sv`
2. Use the same streaming interface as baseline detectors:
   - `clk`
   - `rst_n`
   - `start`
   - `sample_valid`
   - `sample_bits`
   - `done`
   - `prediction`
3. Implement fixed integer IF/LIF-style inference matching Python `TinySNNV2Classifier` default behavior as closely as practical.
4. Update `python/tinysnnrfid/export_rtl_vectors.py` to emit `expected_tiny_snn_v2` predictions.
5. Update testbench or add an SNN-aware testbench so RTL can compare against `expected_tiny_snn_v2`.
6. Update `scripts/run_rtl_sim.sh` to simulate `tiny_snn_v2_detector` and write:
   - `results/rtl/sim_tiny_snn_v2.log`
   - `results/rtl/vcd_tiny_snn_v2.vcd`
7. Update `scripts/run_rtl_synth.sh` to synthesize `tiny_snn_v2_detector` and write:
   - `results/rtl/synth_tiny_snn_v2.json`
   - `results/rtl/synth_tiny_snn_v2.log`
8. Update RTL summary and VCD activity summary scripts so they include `tiny_snn_v2`.
9. Update research report integration if needed so `tiny_snn_v2` RTL evidence appears when available.
10. Add tests that do not require Icarus Verilog or Yosys.

## Constraints

- Do not implement training.
- Do not implement runtime-programmable weights.
- Do not add heavy dependencies.
- Do not require RTL tools for normal tests.
- Do not claim measured silicon power or energy.
- Keep reports clear that RTL results are local-tool proxies, not silicon signoff.
- Keep generated outputs out of git.
- Keep existing baseline RTL flow working.

## Tests

Add or update tests for:

1. `rtl/snn/tiny_snn_v2_detector.sv` exists.
2. Module contains expected streaming interface ports.
3. Vector exporter writes `expected_tiny_snn_v2`.
4. Simulation script references `tiny_snn_v2_detector.sv` and `vcd_tiny_snn_v2.vcd`.
5. Synthesis script references `tiny_snn_v2_detector.sv`.
6. RTL summary includes `tiny_snn_v2` missing status when outputs are absent.
7. VCD activity summary includes `tiny_snn_v2` missing status when outputs are absent.
8. Existing tests still pass.

## Run

```bash
make test
make rtl-vectors
make rtl-sim
make rtl-synth
make rtl-activity
make rtl-report
make research-report
```

If RTL tools are missing, tests and summary commands should still work.

## Final response

Summarize files changed, RTL design choices, vector export changes, script/report integration, tests, command results, and limitations.
