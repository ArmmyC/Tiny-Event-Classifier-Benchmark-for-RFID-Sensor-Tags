# Feature Spec: Evidence Smoke, CI, and Cleanup

## Goal

Add a fast end-to-end smoke workflow that validates the evidence pipeline wiring without running the full benchmark/search workload.

The repo now has `make evidence`, but that target may be too heavy for frequent checks. The project needs a lightweight smoke command that proves the major pieces still connect:

```text
small dataset -> benchmark -> small sweep/search -> RTL vector/export summaries -> comparison/report/manifest
```

This task also fixes cleanup for generated evidence manifest files.

## Required Makefile updates

Add:

```makefile
evidence-smoke:
	python python/run_evidence_smoke.py
```

Update `.PHONY` accordingly.

Update `make clean` to remove:

```text
results/evidence_manifest.json
results/evidence_manifest.md
results/smoke/
```

Keep existing targets working.

## Required smoke runner

Add module:

```text
python/tinysnnrfid/run_evidence_smoke.py
```

Add wrapper:

```text
python/run_evidence_smoke.py
```

The smoke runner should write under:

```text
results/smoke/
```

It should use tiny sample counts and tiny search/sweep grids so it runs quickly.

Suggested behavior:

1. Create tiny legacy and temporal-hard configs under `results/smoke/configs/`.
2. Run a tiny benchmark or direct `run_benchmark` call.
3. Run a tiny sweep with one seed and one parameter point.
4. Run a tiny SNN search with at most two candidates.
5. Export RTL vectors with a tiny limit.
6. Run RTL summary/activity/comparison commands in missing-tool-safe mode.
7. Build a smoke research report using the smoke outputs.
8. Build a smoke evidence manifest using the smoke expected outputs.

It is acceptable for RTL simulation/synthesis outputs to be missing in smoke mode. The smoke runner should still produce summary/report files that clearly say data is missing.

## Required smoke outputs

Write at least:

```text
results/smoke/smoke_summary.json
results/smoke/smoke_report.md
```

The smoke summary should include:

```json
{
  "status": "pass",
  "outputs": [],
  "missing_optional_outputs": [],
  "note": "Smoke evidence uses tiny configs and is not a final benchmark result."
}
```

If a required smoke step fails, the smoke runner should exit nonzero.

## Research report support

If needed, extend `build_research_report.py` CLI to accept custom input paths or an input root so the smoke runner can build a research report from `results/smoke/` outputs.

Keep default `make research-report` behavior unchanged.

## Manifest support

If needed, extend `build_evidence_manifest.py` CLI so the smoke runner can pass a custom expected-output list or call the Python function directly.

Keep default `make evidence-manifest` behavior unchanged.

## CI update

If `.github/workflows/test.yml` exists, update it to run:

```bash
make test
make evidence-smoke
```

The smoke workflow must not require Icarus Verilog or Yosys.

If CI does not exist, add a simple workflow that installs requirements and runs those commands.

## README updates

Document:

```text
make evidence-smoke
make evidence
```

Explain:

- `evidence-smoke` is a fast wiring check with tiny configs.
- `evidence` is the full reproducible evidence pipeline.
- Smoke outputs are not final benchmark results.
- RTL tool outputs may be missing depending on local tools.

## Tests

Add tests that do not require RTL tools:

1. Makefile contains `evidence-smoke`.
2. `make clean` removes evidence manifest and smoke outputs.
3. Smoke runner can run into a temporary output directory.
4. Smoke runner writes `smoke_summary.json` and `smoke_report.md`.
5. Smoke summary status is `pass` for the tiny workflow.
6. Smoke report states that smoke outputs are not final benchmark results.
7. CI workflow includes `make evidence-smoke` if workflow exists.

Do not run the full `make evidence` target in tests.

## Constraints

- Do not add new classifiers.
- Do not add new RTL.
- Do not add heavy dependencies.
- Do not require external RTL tools for smoke or tests.
- Do not commit generated outputs.
- Keep full evidence pipeline behavior unchanged.

## Manual workflow

Run:

```bash
make test
make evidence-smoke
make evidence-manifest
```

Optionally run:

```bash
make evidence
```

## Definition of done

This task is complete when:

- `make evidence-smoke` exists and runs quickly.
- Smoke outputs are generated under `results/smoke/`.
- Smoke mode produces a summary and report.
- `make clean` removes smoke and evidence manifest outputs.
- README documents smoke vs full evidence.
- CI runs smoke if CI exists.
- Tests cover smoke behavior without RTL tools.
- Existing full evidence workflow remains unchanged.
