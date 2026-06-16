# Codex Prompt: End-to-End Evidence Pipeline

You are working in the repository `Tiny-Event-Classifier-Benchmark-for-RFID-Sensor-Tags`.

Implement this spec:

```text
docs/specs/end-to-end-evidence-pipeline.md
```

## Goal

Add one reproducible command that runs the project evidence pipeline in the correct order and produces the final research report.

## Required work

1. Add Makefile target `software-evidence`.
2. Add Makefile target `rtl-evidence`.
3. Add Makefile target `evidence`.
4. Add Makefile target `evidence-manifest`.
5. Add module:
   - `python/tinysnnrfid/build_evidence_manifest.py`
6. Add wrapper:
   - `python/build_evidence_manifest.py`
7. Manifest should inspect expected generated outputs and write:
   - `results/evidence_manifest.json`
   - `results/evidence_manifest.md`
8. README should document:
   - `make evidence`
   - `make software-evidence`
   - `make rtl-evidence`
   - `make evidence-manifest`
9. Add tests that do not require RTL tools and do not run the full evidence pipeline.

## Pipeline order

`evidence` should run:

```text
software-evidence
rtl-evidence
research-report
evidence-manifest
```

`software-evidence` should run the existing software/temporal commands.

`rtl-evidence` should run:

```text
rtl-vectors
rtl-sim
rtl-synth
rtl-activity
rtl-report
rtl-compare
```

Existing RTL scripts already skip missing external tools by default, so this target should remain usable even without Icarus Verilog or Yosys.

## Manifest behavior

Track expected outputs, including benchmark, sweep, SNN search, temporal sweep/search, RTL reports, RTL comparison, research report, and manifest files.

For each path, record:

```json
{
  "path": "...",
  "found": true,
  "size_bytes": 1234
}
```

Add `modified_at` if easy.

Markdown sections:

```text
# Evidence Pipeline Manifest
## Generated Outputs
## Missing Outputs
## Notes and Limitations
```

## Constraints

- Do not add new classifiers.
- Do not add new RTL.
- Do not add heavy dependencies.
- Do not require RTL tools for normal tests.
- Do not run `make evidence` inside tests.
- Do not commit generated outputs.
- Keep existing commands working.

## Tests

Add tests for:

1. Makefile contains `evidence`, `software-evidence`, `rtl-evidence`, and `evidence-manifest` targets.
2. Manifest builder writes JSON and Markdown outputs.
3. Manifest marks missing outputs correctly.
4. Manifest records size for synthetic existing files.
5. Markdown includes missing outputs and limitation text.
6. `make test` passes without RTL tools.

## Run

```bash
make test
make evidence-manifest
```

Optionally run:

```bash
make evidence
```

## Final response

Summarize files changed, Makefile workflow, manifest behavior, tests, command results, and limitations.
