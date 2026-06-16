# Bugfix Spec: Guard RTL Evidence Against Stale Artifacts

## Goal

Prevent stale RTL simulation, synthesis, and activity artifacts from being reported as fresh evidence when local RTL tools are missing or a flow step is skipped.

A recent run reported:

```text
make rtl-sim skipped because iverilog and vvp are missing
make rtl-synth skipped because yosys is missing
```

but later reports still showed:

```text
tiny_snn_v2_sparse_activity simulation passed
sparse SNN cell count: 610
cell ratio vs FSM: 3.961x
```

This means existing files in `results/rtl/` were reused from a previous run. That is an evidence-integrity bug.

## Problem

The Python RTL runners intentionally skip when tools are missing in non-strict mode. However, they currently do not invalidate stale outputs or write a per-run status manifest that downstream report builders can trust.

Affected commands:

```text
make rtl-sim
make rtl-synth
make rtl-activity
make rtl-report
make rtl-compare
make research-report
```

## Required behavior

If a required tool is missing or a step is skipped, downstream reports must not treat old artifacts as current successful evidence.

The reports should clearly say evidence is incomplete/stale/skipped instead of reporting stale pass/cell/toggle results.

## Required changes

### 1. Add RTL evidence run status files

Add per-step status JSON files under `results/rtl/`, for example:

```text
sim_status.json
synth_status.json
activity_status.json
```

Each should include:

```text
step
started_at
finished_at
status: pass | fail | skipped
missing_tools
outputs_written
return_codes by design if applicable
note
```

### 2. Invalidate stale outputs on skipped steps

When `run_rtl_sim.py` skips because `iverilog` or `vvp` is missing, it must either:

- remove old simulation logs/VCDs for the designs it would have generated, or
- write status metadata that downstream summaries use to mark those outputs stale and ignore them.

When `run_rtl_synth.py` skips because `yosys` is missing, it must either:

- remove old synthesis JSON/logs for the designs it would have generated, or
- write status metadata that downstream summaries use to mark those outputs stale and ignore them.

Prefer status metadata plus explicit stale handling. Removing stale outputs is acceptable if tests cover it.

### 3. Make summaries consume status metadata

Update RTL summary, activity summary, RTL comparison, and research report builders so they do not trust old files unless the matching current status file says the step passed or the relevant design output was produced in the current step.

Affected code likely includes:

```text
python/tinysnnrfid/summarize_rtl_results.py
python/tinysnnrfid/summarize_vcd_activity.py
python/tinysnnrfid/compare_rtl_designs.py
python/tinysnnrfid/build_research_report.py
```

### 4. Preserve non-strict UX

Non-strict missing-tool behavior may still exit 0 so users can run reports without hard failure, but the generated reports must say evidence is incomplete.

Strict mode should still fail nonzero when required tools are missing.

### 5. Make stale state obvious

Markdown reports should include language such as:

```text
RTL simulation was skipped in the current run because iverilog/vvp were missing. Previous sim logs were ignored as stale.
```

or:

```text
RTL synthesis was skipped in the current run because yosys was missing. Previous synth JSON files were ignored as stale.
```

## Tests

Add tests that do not require RTL tools:

1. If simulation tools are missing, `run_rtl_sim.py` writes `sim_status.json` with `status: skipped` and missing tools.
2. If synthesis tool is missing, `run_rtl_synth.py` writes `synth_status.json` with `status: skipped` and missing tools.
3. A stale old `synth_tiny_snn_v2_sparse_activity.json` is ignored when `synth_status.json` says skipped.
4. A stale old `sim_tiny_snn_v2_sparse_activity.log` is ignored when `sim_status.json` says skipped.
5. RTL comparison returns `insufficient_rtl_data` when the current run skipped sim or synth, even if old result files exist.
6. Markdown reports mention skipped/stale evidence clearly.
7. Existing successful-path tests continue to pass.
8. Strict mode still exits nonzero when required tools are missing.

## Manual validation

Run once with tools available:

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

Then simulate missing tools by temporarily removing RTL tools from PATH and rerun:

```bash
make rtl-sim
make rtl-synth
make rtl-activity
make rtl-report
make rtl-compare
make research-report
```

Expected:

- reports do not reuse old sim/synth/activity numbers as current evidence,
- recommendation becomes `insufficient_rtl_data`,
- reports clearly mention skipped/stale evidence.

## Constraints

- Do not change RTL detector behavior.
- Do not change classifier behavior.
- Do not change vector export semantics.
- Do not change comparison thresholds.
- Do not add dependencies.
- Do not commit generated outputs.
- Do not claim silicon area or measured power.

## Definition of done

- Stale generated RTL artifacts cannot be mistaken for current evidence.
- Missing-tool non-strict runs remain user-friendly but clearly incomplete.
- Strict mode still fails when tools are missing.
- Tests cover stale artifact handling without requiring RTL tools.
