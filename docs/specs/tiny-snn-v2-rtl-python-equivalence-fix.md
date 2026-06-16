# Feature Spec: Tiny SNN v2 RTL Python Equivalence Fix

## Goal

Fix and test the `tiny_snn_v2_detector.sv` RTL prototype so its prediction behavior matches the Python `TinySNNV2Classifier` default inference as closely as possible.

The first RTL prototype exists, but the arithmetic ordering may not match Python. In particular, Python clips membrane values after leak before adding input or hidden-spike drive. The current RTL subtracts leak and then adds drive before clipping, which can change spike timing and final predictions.

This task is a correctness patch, not a new feature.

## Required behavior

Match Python ordering from `TinySNNV2Classifier._run_sequence`:

1. For every cycle, if `leak` is nonzero:
   - hidden membranes become `max(membrane_min, hidden_membrane - leak)`.
   - output membrane becomes `max(membrane_min, output_membrane - leak)`.
2. If the row has input spikes:
   - add weighted input drive to hidden membranes.
   - clip hidden membranes to `[membrane_min, membrane_max]`.
3. Detect hidden spikes from the clipped hidden membrane.
4. Reset spiking hidden neurons when `reset_on_spike` is true.
5. If any hidden spike exists:
   - add weighted hidden-spike output drive to output membrane.
   - clip output membrane to `[membrane_min, membrane_max]`.
6. Latch prediction high if output membrane reaches output threshold.
7. The final RTL `prediction` at `done` must match Python golden predictions from `expected_tiny_snn_v2`.

## Required RTL fix

Update:

```text
rtl/snn/tiny_snn_v2_detector.sv
```

Fix arithmetic ordering so leak is clipped before drive is added.

Be careful with signed integer temporaries.

Do not change the streaming interface.

## Required tests without RTL tools

Add Python-level reference tests that exercise the exact RTL arithmetic model without requiring Icarus Verilog.

Preferred approach:

1. Add a small pure-Python RTL-model helper if useful, for example:

```text
python/tinysnnrfid/rtl_model.py
```

or a test-local helper.

2. The helper should simulate the intended RTL arithmetic ordering for `tiny_snn_v2`.
3. Compare it against `TinySNNV2Classifier.predict_one` on targeted sequences.
4. Include edge cases that would fail if leak is applied before clipping:
   - membrane starts at zero,
   - one input spike with positive drive exactly at threshold,
   - sparse rows with no inputs,
   - repeated motif-like spikes,
   - noisy channel-3 inhibition.

These tests should prove the intended RTL arithmetic order matches Python even when external RTL tools are missing.

## Optional tests with RTL tools

If `iverilog` and `vvp` are available, optionally run a tiny simulation and compare `tiny_snn_v2_detector` against `expected_tiny_snn_v2`.

This optional test must skip cleanly when tools are missing.

## Script and report behavior

Keep existing scripts working:

```text
make rtl-vectors
make rtl-sim
make rtl-synth
make rtl-activity
make rtl-report
make research-report
```

Do not change report semantics except if needed to mention that `tiny_snn_v2` RTL is now intended to match the Python default arithmetic order.

## Constraints

- Do not add training.
- Do not add runtime-programmable weights.
- Do not add heavy dependencies.
- Do not require RTL tools for normal tests.
- Do not claim measured silicon power or energy.
- Do not commit generated outputs.
- Keep existing baseline RTL flow working.

## Manual checks

Run:

```bash
make test
make rtl-vectors
make rtl-sim
make rtl-activity
make rtl-report
make research-report
```

If RTL tools are missing, `make test`, `make rtl-vectors`, `make rtl-activity`, `make rtl-report`, and `make research-report` should still work.

## Definition of done

This task is complete when:

- `tiny_snn_v2_detector.sv` leak/clip/drive ordering matches Python default inference.
- Tests cover the leak-ordering edge case without requiring RTL tools.
- Existing RTL summary and activity workflows still include `tiny_snn_v2`.
- Existing baseline RTL tests still pass.
- No generated outputs are committed.
