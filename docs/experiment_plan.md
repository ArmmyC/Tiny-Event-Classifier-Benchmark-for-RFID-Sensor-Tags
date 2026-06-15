# Experiment Plan

## Phase 1: Python benchmark

1. Generate synthetic noisy event sequences.
2. Evaluate threshold, FSM, LUT-like, and tiny SNN classifiers.
3. Sweep noise probability, event sparsity, and sequence length.
4. Keep the SNN only if it shows a measurable algorithmic reason to exist.

## Phase 2: RTL baseline implementation

Implement:

- `threshold_detector.sv`
- `fsm_detector.sv`
- `lut_detector.sv`

All designs should share the same interface:

```systemverilog
input  logic       clk;
input  logic       rst_n;
input  logic       event_valid;
input  logic [3:0] event_in;
output logic       detected;
```

## Phase 3: Tiny SNN RTL

Start with a small integrate-and-fire design:

- 4 input channels
- 4 hidden neurons
- 1 output decision
- binary or ternary weights
- 4-bit to 6-bit membrane state
- event-enable updates only

Avoid:

- floating point
- multipliers
- large matrices
- large SRAM
- asynchronous handshake logic in the first version

## Phase 4: Synthesis and switching comparison

Use the same test vectors for all RTL designs.

Collect:

- waveform VCD
- toggle counts
- Yosys synthesis report
- timing estimate if a standard-cell library is available

## Phase 5: Conclusion

Possible outcomes:

1. SNN loses clearly. Conclusion: conventional logic is better for this task.
2. SNN ties accuracy but uses much more area. Conclusion: not justified.
3. SNN improves noise robustness with acceptable area overhead. Conclusion: interesting for semi-passive or near-tag use.
4. SNN reduces switching activity under sparse inputs. Conclusion: worth deeper study with gate-level power.
