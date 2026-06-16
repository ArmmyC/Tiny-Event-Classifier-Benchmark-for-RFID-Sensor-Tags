# Refactor Spec: Python RTL Simulation and Synthesis Runners

## Goal

Remove the Bash dependency from the RTL simulation and synthesis evidence flow by
replacing the shell-script Makefile entry points with Python runners.

## Requirements

- Add Python package modules and wrappers for RTL simulation and synthesis:
  - `python/tinysnnrfid/run_rtl_sim.py`
  - `python/run_rtl_sim.py`
  - `python/tinysnnrfid/run_rtl_synth.py`
  - `python/run_rtl_synth.py`
- Update `make rtl-sim` to run `python python/run_rtl_sim.py`.
- Update `make rtl-synth` to run `python python/run_rtl_synth.py`.
- Preserve output paths:
  - `results/rtl/sim_<design>.log`
  - `results/rtl/vcd_<design>.vcd`
  - `results/rtl/synth_<design>.json`
  - `results/rtl/synth_<design>.log`
- Preserve the existing design set:
  - `threshold`
  - `fsm`
  - `lut_like`
  - `tiny_snn_v2`
  - `tiny_snn_v2_sparse_activity`
- Use `shutil.which` to find `iverilog`, `vvp`, and `yosys`.
- Missing tools skip by default.
- `--strict` and `STRICT=1` fail when required tools are missing.
- Do not require Bash for `rtl-sim` or `rtl-synth`.
- Keep old shell scripts only as legacy helpers; Makefile must not depend on them.
- Update `rtl-doctor` so Bash is optional and no longer required for the RTL evidence flow.
- Update README and tests.

## Constraints

- Do not change RTL modules.
- Do not change detector weights.
- Do not change vector export.
- Do not change RTL comparison semantics.
- Do not add dependencies.
- Do not require RTL tools for tests.
- Do not commit generated outputs.

## Verification

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
```
