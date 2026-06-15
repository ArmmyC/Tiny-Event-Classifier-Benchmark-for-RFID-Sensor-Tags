# Codex Prompt: RTL Baseline Flow

You are working in the repository `Tiny-Event-Classifier-Benchmark-for-RFID-Sensor-Tags`.

Implement this spec:

```text
docs/specs/rtl-baseline-flow.md
```

## Goal

Add a lightweight RTL baseline flow for the simple non-SNN classifiers before attempting any SNN RTL.

The goal is:

```text
Create synthesizable RTL and verification scripts for threshold/FSM/LUT-like baselines, with optional simulation and synthesis when local tools are available.
```

## Required work

1. Add RTL modules under `rtl/baselines/`:
   - `threshold_detector.sv`
   - `fsm_detector.sv`
   - `lut_like_detector.sv`
2. Use a simple streaming interface with `clk`, `rst_n`, `start`, `sample_valid`, `sample_bits`, `done`, and `prediction`.
3. Add `rtl/tb/tb_baseline_detector.sv`.
4. Add scripts:
   - `scripts/run_rtl_sim.sh`
   - `scripts/run_rtl_synth.sh`
5. Add vector export helper if needed:
   - `python/tinysnnrfid/export_rtl_vectors.py`
   - `python/export_rtl_vectors.py`
6. Add Makefile targets:
   - `rtl-vectors`
   - `rtl-sim`
   - `rtl-synth`
7. Write generated RTL outputs under `results/rtl/`.
8. Update `make clean` to remove generated RTL outputs.
9. Update README with an `RTL Baseline Flow` section.
10. Add tests that do not require external RTL tools.

## Constraints

- Do not implement `tiny_snn_v2` RTL yet.
- Do not implement training.
- Do not add heavy dependencies.
- Do not require Icarus Verilog or Yosys for normal tests.
- If `iverilog` or `yosys` is missing, scripts should print a clear message and exit 0 by default.
- Support strict mode if useful, such as `STRICT=1`, to fail when tools are missing.
- Do not commit generated outputs.
- Keep existing Python workflows working.

## Tests

Add tests for:

1. RTL source files exist.
2. RTL modules contain expected module names.
3. Makefile targets exist.
4. Scripts exist and handle missing tools gracefully.
5. Vector export helper writes generated vectors for a tiny dataset.
6. Clean target includes RTL generated outputs.

Optional tests may run simulation/synthesis only when tools are available.

## Run

```bash
make test
make rtl-vectors
make rtl-sim
make rtl-synth
```

## Final response

Summarize files changed, RTL modules added, scripts, Makefile targets, test results, and limitations.
