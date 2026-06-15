# Feature Spec: Tiny SNN v2 RTL Prototype

## Goal

Add a bounded RTL prototype for the fixed-weight `tiny_snn_v2` classifier so it can be compared against the existing RTL baselines.

The repo now has:

- software benchmark flows,
- temporal-hard scenarios,
- SNN parameter search,
- baseline RTL modules,
- simulation/synthesis summary,
- VCD toggle-activity summary,
- consolidated research report.

The next step is to prototype the selected `tiny_snn_v2` inference path in RTL, using the same streaming interface as the baseline detectors.

This is a feasibility prototype, not final silicon design.

## Non-goals

Do not implement:

- training,
- on-chip learning,
- configurable runtime weights,
- floating-point arithmetic,
- a large neuromorphic core,
- vendor-specific synthesis,
- physical design,
- silicon power claims.

Keep the design small, deterministic, and fixed-weight.

## Required RTL

Add:

```text
rtl/snn/tiny_snn_v2_detector.sv
```

Use the same interface as the baseline detectors:

```systemverilog
module tiny_snn_v2_detector #(
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

The module should implement integer fixed-weight IF/LIF-style inference matching the Python `TinySNNV2Classifier` default behavior as closely as practical.

Default parameters should match `configs/default.json` unless overridden by localparams:

```text
hidden_neurons = 6
hidden_threshold = 4
output_threshold = 3
leak = 1
membrane_min = 0
membrane_max = 7
reset_on_spike = true
```

Use fixed integer weights matching the current default `tiny_snn_v2` configuration.

## Behavior requirements

For each input cycle:

1. Apply leak to hidden and output membranes when configured.
2. Add weighted input contribution to hidden membranes.
3. Clip hidden membranes to configured min/max.
4. Generate hidden spikes when hidden membrane crosses threshold.
5. Reset spiking hidden neurons if `reset_on_spike` is true.
6. Add weighted hidden spike contribution to output membrane.
7. Clip output membrane to configured min/max.
8. If output membrane reaches output threshold at any cycle, latch prediction high.
9. After `SEQ_LEN` valid samples, pulse `done` for one cycle.
10. `prediction` is valid when `done` is high.
11. `start` resets per-sample state.

## Golden-vector integration

Update the Python RTL vector exporter:

```text
python/tinysnnrfid/export_rtl_vectors.py
```

Add expected predictions for:

```text
expected_tiny_snn_v2
```

These predictions must come from the Python `TinySNNV2Classifier` using the active config.

Update:

```text
rtl/tb/tb_baseline_detector.sv
```

or add a new SNN-aware testbench if cleaner, so simulation can compare `tiny_snn_v2_detector` against `expected_tiny_snn_v2`.

## Script integration

Update simulation script to include the SNN detector:

```text
scripts/run_rtl_sim.sh
```

It should produce:

```text
results/rtl/sim_tiny_snn_v2.log
results/rtl/vcd_tiny_snn_v2.vcd
```

Update synthesis script:

```text
scripts/run_rtl_synth.sh
```

It should produce:

```text
results/rtl/synth_tiny_snn_v2.json
results/rtl/synth_tiny_snn_v2.log
```

Update RTL summary and VCD activity summary scripts so they include `tiny_snn_v2` alongside:

```text
threshold
fsm
lut_like
```

## Makefile

Existing targets should include the SNN detector automatically:

```text
make rtl-vectors
make rtl-sim
make rtl-synth
make rtl-activity
make rtl-report
make research-report
```

No new target is required unless useful.

## Reports

Update reports so `tiny_snn_v2` appears in:

```text
results/rtl/rtl_summary.json
results/rtl/rtl_report.md
results/rtl/rtl_activity_summary.json
results/rtl/rtl_activity_report.md
results/research_decision_report.md
```

Reports must clearly say:

```text
RTL simulation, synthesis, and toggle counts are local-tool proxies and are not silicon signoff or measured silicon power.
```

## Tests

Add tests that do not require external RTL tools:

1. `rtl/snn/tiny_snn_v2_detector.sv` exists.
2. Module contains the expected streaming interface ports.
3. Vector exporter writes `expected_tiny_snn_v2` values.
4. Simulation script references `tiny_snn_v2_detector.sv` and produces a `vcd_tiny_snn_v2.vcd` path.
5. Synthesis script references `tiny_snn_v2_detector.sv`.
6. RTL summary includes `tiny_snn_v2` missing status when outputs are absent.
7. VCD activity summary includes `tiny_snn_v2` missing status when outputs are absent.
8. Existing baseline RTL tests still pass.
9. `make test` passes without Icarus Verilog or Yosys installed.

Optional tests when tools are available:

1. Simulate `tiny_snn_v2_detector` on a tiny generated vector set.
2. Synthesize `tiny_snn_v2_detector` with Yosys.

Optional tests should skip cleanly if tools are missing.

## Design notes

Keep the RTL intentionally simple:

- fixed weights in localparams or functions,
- signed integer arithmetic,
- small membrane registers,
- no dynamic allocation,
- no memories unless necessary,
- readable implementation over over-optimization.

If exact Python matching is difficult because of arithmetic ordering, document the difference and add a test case showing the intended approximation.

## Manual workflow

Run:

```bash
make test
make rtl-vectors
make rtl-sim
make rtl-synth
make rtl-activity
make rtl-report
make research-report
```

If RTL tools are missing, normal tests and summary commands should still work with missing-output reports.

## Definition of done

This task is complete when:

- `tiny_snn_v2_detector.sv` exists.
- Vector export includes Python-golden `expected_tiny_snn_v2` predictions.
- Simulation/synthesis scripts include the SNN detector.
- RTL summary and activity reports include `tiny_snn_v2`.
- Research report includes `tiny_snn_v2` RTL context when available.
- Tests cover source presence, vector export, script integration, and missing-output summaries.
- No generated outputs are committed.
