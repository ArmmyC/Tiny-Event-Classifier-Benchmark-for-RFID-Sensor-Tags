# Codex Prompt: RTL Results Summary and Research Report Integration

You are working in the repository `Tiny-Event-Classifier-Benchmark-for-RFID-Sensor-Tags`.

Implement this spec:

```text
docs/specs/rtl-results-summary-and-report-integration.md
```

## Goal

Add a small reporting layer for RTL baseline outputs and include RTL baseline evidence in `make research-report`.

Do not implement `tiny_snn_v2` RTL in this task.

## Required work

1. Add `python/tinysnnrfid/summarize_rtl_results.py`.
2. Add wrapper `python/summarize_rtl_results.py`.
3. Add Makefile target `rtl-report`.
4. Read available outputs under `results/rtl/`:
   - `sim_threshold.log`
   - `sim_fsm.log`
   - `sim_lut_like.log`
   - `synth_threshold.json`
   - `synth_fsm.json`
   - `synth_lut_like.json`
5. Missing files must be allowed by default.
6. Write:
   - `results/rtl/rtl_summary.json`
   - `results/rtl/rtl_report.md`
7. Update `build_research_report.py` to read `results/rtl/rtl_summary.json` when present.
8. Add research report input key `rtl_baselines`.
9. Add Markdown section `RTL Baseline Evidence`.
10. Add tests for missing inputs, parsing, output creation, and research-report integration.

## Constraints

- Do not implement SNN RTL.
- Do not add heavy dependencies.
- Do not require Icarus Verilog or Yosys for tests.
- Do not claim measured silicon power.
- State clearly that open-source RTL results are not silicon signoff.
- Do not commit generated outputs.
- Keep existing workflows working.

## Run

```bash
make test
make rtl-report
make research-report
```

Optionally run first:

```bash
make rtl-vectors
make rtl-sim
make rtl-synth
```

## Final response

Summarize files changed, RTL summary behavior, research-report integration, tests, command results, and limitations.
