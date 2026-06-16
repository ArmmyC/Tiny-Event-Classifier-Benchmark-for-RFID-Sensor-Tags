# Codex Prompt: Evidence Smoke, CI, and Cleanup

You are working in the repository `Tiny-Event-Classifier-Benchmark-for-RFID-Sensor-Tags`.

Implement this spec:

```text
docs/specs/evidence-smoke-ci-and-cleanup.md
```

## Goal

Add a fast end-to-end smoke workflow that validates the evidence pipeline wiring without running the full benchmark/search workload.

Also fix cleanup for generated evidence manifest files.

## Required work

1. Add Makefile target `evidence-smoke`.
2. Add module:
   - `python/tinysnnrfid/run_evidence_smoke.py`
3. Add wrapper:
   - `python/run_evidence_smoke.py`
4. Smoke outputs should go under:
   - `results/smoke/`
5. Smoke runner should write:
   - `results/smoke/smoke_summary.json`
   - `results/smoke/smoke_report.md`
6. Smoke runner should use tiny configs and tiny search/sweep grids.
7. Smoke runner should not require Icarus Verilog or Yosys.
8. Update `make clean` to remove:
   - `results/evidence_manifest.json`
   - `results/evidence_manifest.md`
   - `results/smoke/`
9. Update README to explain `make evidence-smoke` versus `make evidence`.
10. If `.github/workflows/test.yml` exists, update it to run `make evidence-smoke` after `make test`.
11. Add tests that do not require RTL tools and do not run full `make evidence`.

## Smoke workflow expectation

The smoke workflow should prove the major pieces connect:

```text
small dataset -> benchmark -> small sweep/search -> RTL vector export -> RTL summaries/comparison -> research report/manifest
```

It is okay if RTL sim/synth outputs are missing in smoke mode. Missing RTL tool outputs should be reported clearly, not treated as a smoke failure.

## Constraints

- Do not add new classifiers.
- Do not add new RTL.
- Do not add heavy dependencies.
- Do not require external RTL tools for smoke or tests.
- Do not commit generated outputs.
- Keep full `make evidence` behavior unchanged.

## Tests

Add tests for:

1. Makefile contains `evidence-smoke`.
2. `make clean` removes evidence manifest and smoke outputs.
3. Smoke runner can run into a temporary output directory.
4. Smoke runner writes `smoke_summary.json` and `smoke_report.md`.
5. Smoke summary status is `pass` for the tiny workflow.
6. Smoke report says smoke outputs are not final benchmark results.
7. CI workflow includes `make evidence-smoke` if workflow exists.

## Run

```bash
make test
make evidence-smoke
make evidence-manifest
```

## Final response

Summarize files changed, smoke workflow behavior, cleanup changes, CI updates, tests, command results, and limitations.
