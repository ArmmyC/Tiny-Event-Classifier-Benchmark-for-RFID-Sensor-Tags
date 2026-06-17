# Bugfix Spec: Validate RTL Output Freshness on Successful Runs

## Goal

Close the remaining stale-artifact edge case in the RTL evidence flow.

The current stale-artifact guard correctly handles skipped runs by writing status files and making downstream reports ignore old artifacts. However, the successful-run path still records some outputs as current if the file merely exists after the tool command.

That can incorrectly whitelist stale files when:

- an old VCD or Yosys JSON exists before the run,
- the tool command returns success,
- but the expected output was not actually rewritten in the current run.

## Current risky behavior

`run_rtl_sim.py` adds a VCD to `outputs_written` if `vcd_path.is_file()` after simulation.

`run_rtl_synth.py` adds a synthesis JSON to `outputs_written` if `json_path.is_file()` after synthesis.

This proves existence, not freshness.

## Required behavior

An output should be listed in `outputs_written` only if it was created or refreshed by the current run.

Downstream summaries should continue to trust only outputs listed in the current status file.

## Required changes

Update:

```text
python/tinysnnrfid/run_rtl_sim.py
python/tinysnnrfid/run_rtl_synth.py
```

Before running each design, either:

1. remove expected generated outputs for that design, then only add them if they exist after the command, or
2. record pre-run modification timestamps and only add outputs whose modification time is newer than the step start time.

Prefer deleting expected generated outputs before running that design because it is simpler and makes stale state impossible.

For simulation, handle:

```text
sim_<design>.out
sim_<design>.log
vcd_<design>.vcd
```

For synthesis, handle:

```text
synth_<design>.json
synth_<design>.log
```

Logs written by the Python runner are current outputs. VCD/JSON outputs should only be listed if produced during the current command.

## Status semantics

If a tool command succeeds but an expected optional output is missing:

- do not list the missing output in `outputs_written`,
- keep the design return code in status,
- downstream summaries should mark the missing output as missing/stale rather than parse an old file.

If a required output for a successful design is missing, consider making the overall step status `fail` with a clear note.

## Tests

Add tests that do not require RTL tools:

1. `run_rtl_sim.py` deletes or invalidates an old `vcd_tiny_snn_v2_sparse_activity.vcd` before running; if mocked `vvp` does not recreate it, `sim_status.json` must not list it.
2. `run_rtl_synth.py` deletes or invalidates an old `synth_tiny_snn_v2_sparse_activity.json` before running; if mocked `yosys` does not recreate it, `synth_status.json` must not list it.
3. With old VCD/JSON present but not regenerated, summaries do not parse stale values.
4. With VCD/JSON regenerated, summaries parse them normally.
5. Existing skipped-tool stale-artifact tests still pass.
6. Strict mode behavior remains unchanged.

## Manual validation

Run:

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

Then rerun targeted tests with mocked successful commands that do not create VCD/JSON outputs and verify stale outputs are ignored.

## Constraints

- Do not change RTL detector behavior.
- Do not change classifier behavior.
- Do not change vector export semantics.
- Do not change comparison thresholds.
- Do not add dependencies.
- Do not commit generated outputs.
- Do not claim silicon area or measured power.

## Definition of done

- Skipped runs cannot reuse stale outputs.
- Successful runs cannot whitelist pre-existing VCD/JSON outputs unless they were refreshed in the current run.
- Status metadata accurately reflects current-run evidence.
- Tests cover stale pre-existing outputs on success paths.
