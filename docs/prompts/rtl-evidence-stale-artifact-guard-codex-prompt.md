# Codex Prompt: Guard RTL Evidence Against Stale Artifacts

Implement:

```text
docs/specs/rtl-evidence-stale-artifact-guard.md
```

Goal: prevent old `results/rtl/*` artifacts from being reported as fresh RTL evidence when sim/synth/activity steps are skipped because local tools are missing.

Context:
A recent run skipped RTL tools:
- `make rtl-sim` skipped because `iverilog` and `vvp` were missing
- `make rtl-synth` skipped because `yosys` was missing

But reports still showed stale prior evidence:
- sparse SNN sim pass
- sparse SNN cell count 610
- cell ratio 3.961x

Required:
1. Add current-run status metadata files under `results/rtl/`, such as:
   - `sim_status.json`
   - `synth_status.json`
   - `activity_status.json`
2. Status should include step, started/finished timestamps, status `pass|fail|skipped`, missing tools, outputs written, return codes by design, and note.
3. Update `python/tinysnnrfid/run_rtl_sim.py` so missing `iverilog`/`vvp` writes skipped status and stale outputs are not later trusted.
4. Update `python/tinysnnrfid/run_rtl_synth.py` so missing `yosys` writes skipped status and stale outputs are not later trusted.
5. Update RTL summary/activity/comparison/research report code so old files are ignored unless current status says the step passed or the design output was produced in the current run.
6. Non-strict missing-tool runs may still exit 0, but reports must say evidence is incomplete/skipped/stale.
7. Strict mode must still exit nonzero when tools are missing.
8. Do not change detector RTL, classifier behavior, vector export, comparison thresholds, or generated-output policy.

Add tests that do not require RTL tools:
- missing sim tools writes `sim_status.json` with `status: skipped`
- missing synth tool writes `synth_status.json` with `status: skipped`
- stale old synth JSON is ignored when synth status is skipped
- stale old sim logs/VCDs are ignored when sim status is skipped
- RTL comparison returns `insufficient_rtl_data` when current sim/synth was skipped even if old files exist
- Markdown reports mention skipped/stale evidence clearly
- strict mode still fails nonzero with missing tools

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
Summarize changed files, tests run, and demonstrate how stale artifacts are blocked when RTL tools are missing.

Constraints:
- Do not add dependencies.
- Do not commit generated outputs.
- Do not claim silicon area or measured power.
