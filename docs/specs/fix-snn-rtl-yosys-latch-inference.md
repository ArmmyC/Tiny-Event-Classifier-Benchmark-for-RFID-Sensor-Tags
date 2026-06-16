# Bugfix Spec: Fix SNN RTL Yosys Latch Inference

## Goal

Fix Yosys synthesis failures caused by latch inference in the SNN RTL candidate path.

The sparse-activity RTL candidate now simulates correctly, but synthesis fails for:

```text
rtl/snn/tiny_snn_v2_sparse_activity_detector.sv
```

because Yosys reports latch inference. This leaves the RTL comparison at:

```text
recommendation: insufficient_rtl_data
reason: FSM and tiny_snn_v2_sparse_activity cell/toggle proxy data are required.
```

The next step is a source-level RTL bugfix, not another toolchain change.

## Required behavior

Both SNN RTL modules should synthesize with Yosys without latch inference:

```text
rtl/snn/tiny_snn_v2_detector.sv
rtl/snn/tiny_snn_v2_sparse_activity_detector.sv
```

Do not change the externally visible behavior of either module.

The sparse candidate must still pass simulation against Python-golden vectors.

## Likely issue

The `always_comb` blocks use local temporary variables such as:

```text
hidden_value
output_value
drive
```

These are only assigned inside conditional paths. Even if registered outputs have defaults, Yosys may infer latches for the combinational temporaries.

## Required changes

Update both SNN RTL modules so every combinational variable is assigned on every path.

Acceptable approaches:

1. Initialize all temporary variables at the top of `always_comb`, before conditionals.
2. Split repeated arithmetic into helper functions that always assign return values.
3. Restructure the combinational block so Yosys can prove there is no latch.

Keep the existing inference semantics:

- leak and clip before adding drive,
- clip after adding drive,
- reset hidden membrane on spike,
- output membrane update based on hidden spikes from the same sample,
- prediction is sticky once output membrane crosses threshold,
- fixed integer weights,
- no training,
- no runtime-programmable weights.

Do not change the fixed weights.

## Required validation

Run the full RTL evidence flow:

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

Expected result after the fix:

- `tiny_snn_v2_sparse_activity` simulation passes.
- `results/rtl/synth_tiny_snn_v2_sparse_activity.json` exists.
- `results/rtl/synth_tiny_snn_v2_sparse_activity.log` does not contain latch inference errors.
- FSM synthesis remains available.
- `rtl_comparison_summary.json` has non-null sparse candidate cell and toggle ratios versus FSM.

## Tests

Add tests that do not require Yosys to be installed:

1. Static test that both SNN RTL modules assign combinational temporaries before conditional use.
2. Static test that both SNN RTL modules still contain no `latch` keyword or latch-intended constructs.
3. Existing simulation/vector/export tests continue to pass.
4. Existing RTL runner tests continue to pass.

If Yosys is available in the test environment, an optional integration test may run synthesis for the sparse module, but normal unit tests must not require Yosys.

## Constraints

- Do not change detector interfaces.
- Do not change fixed weights.
- Do not change Python classifier behavior.
- Do not change vector export semantics.
- Do not change RTL comparison decision semantics.
- Do not add dependencies.
- Do not commit generated outputs.
- Do not claim silicon area or measured power.

## Manual inspection

After synthesis succeeds, inspect:

```text
results/rtl/synth_tiny_snn_v2_sparse_activity.log
results/rtl/synth_tiny_snn_v2_sparse_activity.json
results/rtl/rtl_comparison_summary.json
results/rtl/rtl_comparison_report.md
```

## Definition of done

- Sparse SNN RTL still simulates correctly.
- Sparse SNN RTL synthesizes with Yosys.
- Default SNN RTL also remains synthesizable.
- No latch inference errors remain in SNN synthesis logs.
- RTL comparison has both cell and toggle ratios for the sparse candidate versus FSM.
