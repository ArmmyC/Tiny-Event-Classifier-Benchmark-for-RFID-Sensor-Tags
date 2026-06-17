# Codex Prompt: Validate RTL Output Freshness on Successful Runs

Implement:

```text
docs/specs/rtl-output-freshness-validation.md
```

Goal: close the remaining stale-artifact edge case in the RTL evidence flow.

Context:
The stale-artifact guard now handles skipped runs, but successful runs still add some outputs to `outputs_written` if the file merely exists after the tool command. That can whitelist stale files if an old VCD/JSON existed before the run and the tool command returned success without regenerating it.

Required:
1. Update `python/tinysnnrfid/run_rtl_sim.py`.
2. Update `python/tinysnnrfid/run_rtl_synth.py`.
3. Before each design run, delete or otherwise invalidate expected generated outputs for that design.
4. For simulation, handle:
   - `sim_<design>.out`
   - `sim_<design>.log`
   - `vcd_<design>.vcd`
5. For synthesis, handle:
   - `synth_<design>.json`
   - `synth_<design>.log`
6. Only list VCD/JSON outputs in `outputs_written` if they were produced in the current command after stale files were removed.
7. Logs written by the Python runner are current outputs.
8. If a successful command does not produce an expected VCD/JSON, do not list the old file as current evidence. Prefer marking the step fail or clearly incomplete if the missing output is required.
9. Keep downstream summaries/comparison behavior using current status metadata.
10. Keep skipped-tool behavior and strict mode unchanged.

Add tests that do not require RTL tools:
- old VCD exists before mocked sim, mocked `vvp` does not recreate it, `sim_status.json` must not list it
- old synth JSON exists before mocked synth, mocked `yosys` does not recreate it, `synth_status.json` must not list it
- summaries do not parse stale VCD/JSON when not regenerated
- regenerated VCD/JSON is parsed normally
- existing skipped-tool stale-artifact tests still pass

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

Final response:
Summarize changed files, tests run, and show how pre-existing stale VCD/JSON files are prevented from being whitelisted on successful runs.

Constraints:
- Do not add dependencies.
- Do not commit generated outputs.
- Do not claim silicon area or measured power.
