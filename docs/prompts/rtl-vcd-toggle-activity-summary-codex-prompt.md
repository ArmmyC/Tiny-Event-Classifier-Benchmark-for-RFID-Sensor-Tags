# Codex Prompt: RTL VCD Toggle Activity Summary

You are working in the repository `Tiny-Event-Classifier-Benchmark-for-RFID-Sensor-Tags`.

Implement this spec:

```text
docs/specs/rtl-vcd-toggle-activity-summary.md
```

## Goal

Add a VCD-based RTL switching-activity proxy flow for the existing baseline detectors.

This is not silicon power. It is only a simulation toggle-count proxy.

## Required work

1. Update `rtl/tb/tb_baseline_detector.sv` so VCD dumping is optional through a plusarg such as `VCD_FILE=...`.
2. Update `scripts/run_rtl_sim.sh` so each baseline can write:
   - `results/rtl/vcd_threshold.vcd`
   - `results/rtl/vcd_fsm.vcd`
   - `results/rtl/vcd_lut_like.vcd`
3. Keep current simulation pass/fail behavior.
4. Add parser module:
   - `python/tinysnnrfid/summarize_vcd_activity.py`
5. Add wrapper:
   - `python/summarize_vcd_activity.py`
6. Add Makefile target `rtl-activity`.
7. Write:
   - `results/rtl/rtl_activity_summary.json`
   - `results/rtl/rtl_activity_report.md`
8. Missing VCD files must be allowed and reported clearly.
9. Update `summarize_rtl_results.py` so `rtl-report` includes activity summary when available.
10. Update `build_research_report.py` so `research-report` includes RTL activity context when available.
11. Update README.
12. Add tests that do not require RTL tools.

## Parser behavior

The parser should be dependency-free and count value changes per signal where practical.

Minimum per-baseline output:

```json
{
  "found": true,
  "status": "available",
  "signal_count": 42,
  "total_toggles": 1234,
  "top_toggled_signals": [
    {"signal": "sample_bits", "toggles": 120}
  ]
}
```

If missing:

```json
{"found": false, "status": "missing"}
```

## Tests

Add tests for:

1. Missing VCD files produce missing statuses.
2. A tiny synthetic VCD is parsed and toggle counts are nonzero.
3. Activity JSON and Markdown reports are written.
4. `rtl-report` includes activity summary when `rtl_activity_summary.json` exists.
5. Research report includes RTL activity context when present.
6. Normal tests pass without Icarus Verilog or Yosys installed.

## Constraints

- Do not implement `tiny_snn_v2` RTL.
- Do not add heavy dependencies.
- Do not require RTL tools for tests.
- Do not claim measured silicon power or energy.
- Keep generated outputs out of git.
- Keep existing workflows working.

## Run

```bash
make test
make rtl-activity
make rtl-report
make research-report
```

Optionally run first:

```bash
make rtl-vectors
make rtl-sim
```

## Final response

Summarize files changed, VCD behavior, activity parser, report integration, tests, command results, and limitations.
