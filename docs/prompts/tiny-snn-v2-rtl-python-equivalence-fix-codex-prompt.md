# Codex Prompt: Tiny SNN v2 RTL Python Equivalence Fix

You are working in the repository `Tiny-Event-Classifier-Benchmark-for-RFID-Sensor-Tags`.

Implement this spec:

```text
docs/specs/tiny-snn-v2-rtl-python-equivalence-fix.md
```

## Goal

Fix and test `tiny_snn_v2_detector.sv` so its prediction behavior matches Python `TinySNNV2Classifier` default inference as closely as possible.

This is a correctness patch, not a new feature.

## Issue to fix

Python clips membrane values after leak before adding drive:

```text
hidden_membrane = max(membrane_min, hidden_membrane - leak)
output_membrane = max(membrane_min, output_membrane - leak)
then add weighted input/output drive
then clip again
```

The current RTL subtracts leak and adds drive before clipping, which can change spike timing and predictions.

## Required work

1. Update `rtl/snn/tiny_snn_v2_detector.sv`.
2. Fix leak/clip/drive ordering to match Python default inference.
3. Keep the existing streaming interface unchanged.
4. Keep fixed default weights unchanged.
5. Add tests that do not require Icarus Verilog or Yosys.
6. Add targeted edge cases that would fail if leak is applied before clipping.
7. Keep `rtl-vectors`, `rtl-sim`, `rtl-synth`, `rtl-activity`, `rtl-report`, and `research-report` working.

## Suggested tests

Add a small pure-Python RTL arithmetic model in tests or helper code and compare it against `TinySNNV2Classifier.predict_one`.

Include cases for:

- membrane starts at zero,
- one input spike with positive drive exactly at threshold,
- sparse rows with no inputs,
- repeated motif-like spikes,
- noisy channel-3 inhibition.

Optional: if `iverilog` and `vvp` are available, run a tiny RTL simulation. Skip cleanly if tools are missing.

## Constraints

- Do not add training.
- Do not add runtime-programmable weights.
- Do not add heavy dependencies.
- Do not require RTL tools for normal tests.
- Do not claim measured silicon power or energy.
- Do not commit generated outputs.
- Keep baseline RTL flow working.

## Run

```bash
make test
make rtl-vectors
make rtl-sim
make rtl-activity
make rtl-report
make research-report
```

If RTL tools are missing, normal tests and non-tool report commands should still work.

## Final response

Summarize files changed, arithmetic fix, tests, command results, and limitations.
