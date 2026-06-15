# Feature Spec: RTL Baseline Flow for Simple Classifiers

## 1. Goal

Add a lightweight RTL baseline flow for the simple non-SNN classifiers before attempting any SNN RTL.

The benchmark now has enough software evidence infrastructure: legacy runs, temporal-hard runs, sweeps, SNN search, and a consolidated research report. The next hardware step should be conservative: implement and verify RTL for simple baselines first, then use those baselines as the area/activity reference for any future SNN RTL.

The goal is:

```text
Create synthesizable RTL and verification scripts for threshold/FSM/LUT-like baselines, with optional simulation and synthesis when local tools are available.
```

This gives the project real hardware-facing evidence for the baselines that `tiny_snn_v2` must beat.

## 2. Non-goals

Do not implement:

- `tiny_snn_v2` RTL yet.
- On-chip training.
- New datasets.
- Heavy dependencies.
- Vendor-specific flows.
- Claims of silicon power from software activity proxy.

This task is only for simple baseline RTL infrastructure.

## 3. Assumptions

- Generated datasets already include `test_vectors.txt` and `vectors.hex`.
- Python benchmark classifiers remain the source of truth for algorithm behavior.
- Icarus Verilog and Yosys may or may not be installed locally.
- Tests should not fail just because RTL tools are missing.
- Generated simulation/synthesis outputs must not be committed.

## 4. Required RTL modules

Create RTL under:

```text
rtl/baselines/
```

Required modules:

```text
threshold_detector.sv
fsm_detector.sv
lut_like_detector.sv
```

Each module should be synthesizable SystemVerilog or Verilog-2005 compatible SystemVerilog.

Use a simple streaming interface:

```systemverilog
module detector_name #(
    parameter int INPUT_WIDTH = 4,
    parameter int SEQ_LEN = 40
) (
    input  logic clk,
    input  logic rst_n,
    input  logic start,
    input  logic sample_valid,
    input  logic [INPUT_WIDTH-1:0] sample_bits,
    output logic done,
    output logic prediction
);
```

Behavior:

- `start` resets per-sample internal state.
- One cycle is consumed whenever `sample_valid` is high.
- After `SEQ_LEN` samples, `done` pulses for one cycle.
- `prediction` is valid when `done` is high.

## 5. Classifier behavior targets

### `threshold_detector`

Approximate the Python threshold classifier:

- count active cycles,
- count total spikes,
- predict positive when both thresholds are met.

Parameters:

```text
MIN_ACTIVE_CYCLES
MIN_TOTAL_SPIKES
```

### `fsm_detector`

Implement ordered motif detection for the default motif:

```text
channel 0 -> channel 1 -> channel 2
```

Parameters:

```text
MAX_GAP
```

This module should be the main hardware baseline.

### `lut_like_detector`

Implement a small combinational/sequential approximation of the Python LUT-like baseline using simple counters/guards.

It does not need to be a literal large LUT. The goal is a small logic baseline that is easy to synthesize and compare.

## 6. Testbench and scripts

Create:

```text
rtl/tb/tb_baseline_detector.sv
scripts/run_rtl_sim.sh
scripts/run_rtl_synth.sh
```

The testbench should:

- run one selected detector module,
- feed samples from generated vector data or a generated testbench include file,
- compare RTL predictions against expected labels or a provided golden file,
- print pass/fail counts,
- exit nonzero on mismatch when simulation tools are available.

If parsing `test_vectors.txt` directly in Verilog is too awkward, add a Python helper:

```text
python/tinysnnrfid/export_rtl_vectors.py
python/export_rtl_vectors.py
```

The helper may convert `data/generated/test_vectors.txt` or NumPy arrays into an RTL-friendly `.svh`, `.mem`, or `.hex` file under generated results.

## 7. Makefile targets

Add:

```makefile
rtl-vectors:
	python python/export_rtl_vectors.py --config configs/temporal_hard.json

rtl-sim:
	bash scripts/run_rtl_sim.sh

rtl-synth:
	bash scripts/run_rtl_synth.sh
```

Tool behavior:

- If `iverilog` is missing, `rtl-sim` should print a clear message and exit 0 by default.
- If `yosys` is missing, `rtl-synth` should print a clear message and exit 0 by default.
- Add a strict mode to scripts if useful, such as `STRICT=1`, to fail when tools are missing.

## 8. Outputs

Generated RTL outputs should go under:

```text
results/rtl/
```

Possible files:

```text
results/rtl/vectors.svh
results/rtl/sim_threshold.log
results/rtl/sim_fsm.log
results/rtl/sim_lut_like.log
results/rtl/synth_threshold.json
results/rtl/synth_fsm.json
results/rtl/synth_lut_like.json
results/rtl/rtl_summary.json
results/rtl/rtl_report.md
```

Do not commit these generated files.

Update `make clean` to remove `results/rtl/` generated outputs.

## 9. Python summary report

Add an optional summary script:

```text
python/tinysnnrfid/summarize_rtl_results.py
python/summarize_rtl_results.py
```

It should read available simulation/synthesis outputs and write:

```text
results/rtl/rtl_report.md
results/rtl/rtl_summary.json
```

The report must clearly say:

```text
Simulation and synthesis results depend on local open-source tool availability and are not silicon signoff.
```

## 10. Tests

Add tests that do not require external RTL tools:

1. RTL source files exist.
2. RTL modules contain expected module names.
3. Makefile targets exist.
4. Scripts exist and are executable or runnable through bash.
5. Vector export helper writes an output file for a tiny generated dataset.
6. RTL tool scripts handle missing tools gracefully.
7. Clean target includes `results/rtl` outputs.

Optional tests when tools are present:

1. Run `rtl-sim` on a tiny vector set.
2. Run `rtl-synth` on each baseline.

These optional tests should skip cleanly if tools are missing.

## 11. README updates

Add a section:

```text
## RTL Baseline Flow
```

Explain:

- RTL is currently only for simple baselines,
- `tiny_snn_v2` RTL is intentionally deferred,
- how to run `make rtl-vectors`, `make rtl-sim`, and `make rtl-synth`,
- tool availability caveats,
- outputs are generated and ignored.

## 12. Definition of done

This task is complete when:

- Baseline RTL modules exist.
- Simulation/synthesis scripts exist and handle missing tools gracefully.
- Makefile targets exist.
- Generated RTL outputs go under `results/rtl/`.
- Tests cover file presence, vector export, script behavior, and Makefile targets.
- README documents the RTL baseline flow.
- Existing Python benchmark, sweep, SNN search, temporal workflows, and research report still work.
- No generated outputs are committed.
