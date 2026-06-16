# Feature Spec: End-to-End Evidence Pipeline

## Goal

Add one reproducible command that runs the project evidence pipeline in the correct order and produces the final research report.

The repo now has many useful commands:

```text
make benchmark
make sweep
make snn-search
make temporal-benchmark
make temporal-sweep
make temporal-snn-search
make rtl-vectors
make rtl-sim
make rtl-synth
make rtl-activity
make rtl-report
make rtl-compare
make research-report
```

The problem is that users must remember the correct order. This task adds a high-level pipeline target and a lightweight status/manifest report so the project is easier to reproduce and present.

## Required Makefile targets

Add:

```makefile
evidence:
	# run the full evidence pipeline in order

software-evidence:
	# run software benchmark, sweep, SNN search, temporal benchmark, temporal sweep, temporal SNN search

rtl-evidence:
	# run RTL vector export, optional simulation, optional synthesis, VCD activity summary, RTL summary, RTL comparison
```

Recommended order for `evidence`:

```text
make software-evidence
make rtl-evidence
make research-report
```

`rtl-evidence` should work even when Icarus Verilog or Yosys is missing because existing scripts skip by default.

## Required pipeline manifest

Add module:

```text
python/tinysnnrfid/build_evidence_manifest.py
```

Add wrapper:

```text
python/build_evidence_manifest.py
```

Add Makefile target:

```makefile
evidence-manifest:
	python python/build_evidence_manifest.py
```

The manifest should inspect expected generated outputs and write:

```text
results/evidence_manifest.json
results/evidence_manifest.md
```

Generated manifest outputs must not be committed.

## Expected outputs to track

Track at least:

```text
results/benchmark_results.json
results/benchmark_report.md
results/sweeps/sweep_results.json
results/sweeps/sweep_summary.csv
results/sweeps/sweep_report.md
results/snn_search/search_results.json
results/snn_search/search_summary.csv
results/snn_search/search_report.md
results/temporal_sweeps/sweep_results.json
results/temporal_sweeps/sweep_summary.csv
results/temporal_sweeps/sweep_report.md
results/temporal_snn_search/search_results.json
results/temporal_snn_search/search_summary.csv
results/temporal_snn_search/search_report.md
results/rtl/rtl_summary.json
results/rtl/rtl_report.md
results/rtl/rtl_activity_summary.json
results/rtl/rtl_activity_report.md
results/rtl/rtl_comparison_summary.json
results/rtl/rtl_comparison_report.md
results/research_decision_summary.json
results/research_decision_report.md
```

For each output, record:

```json
{
  "path": "...",
  "found": true,
  "size_bytes": 1234
}
```

If found, include `modified_at` if easy to implement.

## Report contents

`results/evidence_manifest.md` should include:

```text
# Evidence Pipeline Manifest
## Generated Outputs
## Missing Outputs
## Notes and Limitations
```

The report must state that RTL simulation/synthesis/toggle evidence depends on local tool availability and is not silicon signoff.

## Integration with evidence target

The `evidence` target should run:

```text
software-evidence
rtl-evidence
research-report
evidence-manifest
```

This means after:

```bash
make evidence
```

users should know where to inspect:

```text
results/research_decision_report.md
results/evidence_manifest.md
```

## Optional smoke target

Add a faster target if useful:

```makefile
evidence-smoke:
	# run a reduced or manifest-only flow for quick checks
```

This is optional. Do not add complex config duplication unless necessary.

## README updates

Add a short section explaining:

```text
make evidence
make software-evidence
make rtl-evidence
make evidence-manifest
```

Explain that full evidence generation may take longer than unit tests and that RTL tool outputs are optional depending on local tool availability.

## Tests

Add tests that do not require external RTL tools:

1. Makefile contains `evidence`, `software-evidence`, `rtl-evidence`, and `evidence-manifest` targets.
2. Manifest builder writes JSON and Markdown outputs with all expected paths.
3. Manifest marks missing outputs correctly.
4. Manifest records size for synthetic existing files.
5. Manifest Markdown includes missing outputs and limitation note.
6. `make test` passes without running the full evidence pipeline.

Do not run `make evidence` inside normal tests.

## Constraints

- Do not implement new classifiers.
- Do not implement new RTL.
- Do not add heavy dependencies.
- Do not require RTL tools for tests.
- Do not commit generated outputs.
- Keep existing commands working.

## Manual workflow

Run:

```bash
make test
make evidence-manifest
make evidence
```

If tools are missing, RTL sim/synth should be skipped by existing scripts, and the manifest should show which outputs are missing.

## Definition of done

This task is complete when:

- `make evidence` exists and runs the full pipeline in order.
- `make software-evidence` exists.
- `make rtl-evidence` exists.
- `make evidence-manifest` exists.
- Manifest JSON and Markdown are generated.
- README documents the high-level workflow.
- Tests cover target presence and manifest behavior.
- Existing tests pass.
- No generated outputs are committed.
