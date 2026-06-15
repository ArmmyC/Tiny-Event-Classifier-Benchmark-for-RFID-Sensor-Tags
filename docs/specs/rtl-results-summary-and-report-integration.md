# Feature Spec: RTL Results Summary and Research Report Integration

## Goal

Add a small reporting layer for the RTL baseline flow and include that evidence in the consolidated research report.

The repo now has RTL baseline modules, vector export, and optional simulation/synthesis scripts. The next step is to summarize whatever RTL outputs are available under `results/rtl/` into stable JSON and Markdown files.

Do not implement `tiny_snn_v2` RTL in this task.

## Required work

1. Add module:

```text
python/tinysnnrfid/summarize_rtl_results.py
```

2. Add wrapper:

```text
python/summarize_rtl_results.py
```

3. Add Makefile target:

```makefile
rtl-report:
	python python/summarize_rtl_results.py
```

4. Read available files under:

```text
results/rtl/
```

Expected possible inputs:

```text
sim_threshold.log
sim_fsm.log
sim_lut_like.log
synth_threshold.json
synth_fsm.json
synth_lut_like.json
synth_threshold.log
synth_fsm.log
synth_lut_like.log
vectors.svh
```

5. Missing inputs must be allowed by default.

6. Write:

```text
results/rtl/rtl_summary.json
results/rtl/rtl_report.md
```

7. Update `python/tinysnnrfid/build_research_report.py` so `make research-report` also reads:

```text
results/rtl/rtl_summary.json
```

8. Add research report input key:

```text
rtl_baselines
```

9. Add Markdown section:

```text
## RTL Baseline Evidence
```

10. Keep generated outputs out of git.

## Summary behavior

The RTL summary should report:

- which simulation logs are present,
- baseline simulation status when parseable,
- which synthesis JSON files are present,
- simple synthesis proxy metrics when parseable,
- lowest cell-count baseline when available,
- clear notes when tool outputs are missing.

For synthesis JSON, parse defensively because Yosys output shape may vary.

## Output JSON shape

Suggested shape:

```json
{
  "simulations": {
    "threshold": {"found": true, "passed": 10, "failed": 0, "status": "pass"},
    "fsm": {"found": false, "status": "missing"},
    "lut_like": {"found": false, "status": "missing"}
  },
  "synthesis": {
    "threshold": {"found": true, "cell_count": 100, "status": "available"},
    "fsm": {"found": false, "status": "missing"},
    "lut_like": {"found": false, "status": "missing"}
  },
  "recommendation_context": {
    "baseline_rtl_available": true,
    "all_available_sims_pass": true,
    "lowest_cell_count_baseline": "threshold"
  },
  "note": "RTL simulation and synthesis depend on local tools and are not silicon signoff."
}
```

## Markdown report sections

```text
# RTL Baseline Results Report
## Inputs Found
## Simulation Summary
## Synthesis Summary
## Baseline Comparison
## Notes and Limitations
```

The report must state that open-source RTL results are not silicon signoff and must not claim measured silicon power.

## Tests

Add tests that do not require RTL tools:

1. Missing RTL inputs produce missing statuses.
2. Synthetic simulation logs are parsed correctly.
3. Synthetic Yosys-style JSON is parsed for simple cell counts.
4. Markdown RTL report is written.
5. Research report loads `rtl_summary.json` when present.
6. Research report includes `RTL Baseline Evidence`.
7. `make research-report` still works when RTL summary is missing.
8. `make test` passes without Icarus Verilog or Yosys installed.

## Manual workflow

Run:

```bash
make rtl-vectors
make rtl-sim
make rtl-synth
make rtl-report
make research-report
```

If tools are missing, `make rtl-report` should still write a report that explains missing inputs.

## Definition of done

This task is complete when:

- `make rtl-report` works.
- `results/rtl/rtl_summary.json` is generated.
- `results/rtl/rtl_report.md` is generated.
- Research report includes RTL baseline evidence.
- Tests cover missing inputs, parsing, and research-report integration.
- Existing workflows remain usable.
- No generated outputs are committed.
