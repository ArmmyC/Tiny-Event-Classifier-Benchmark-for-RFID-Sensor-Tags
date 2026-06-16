# Feature Spec: Artifact Card

## Goal

Add a short generated artifact card that summarizes the main evidence after the evidence pipeline runs.

The repo now produces many outputs. The card should be the first file a reviewer opens.

## Command

Add:

```text
python/tinysnnrfid/build_artifact_card.py
python/build_artifact_card.py
make artifact-card
```

Default command:

```bash
python python/build_artifact_card.py --input-root results --output-dir results
```

## Inputs

Read these files when present:

```text
results/research_decision_summary.json
results/rtl/rtl_comparison_summary.json
results/evidence_manifest.json
results/smoke/smoke_summary.json
```

Support custom roots:

```bash
python python/build_artifact_card.py --input-root results/smoke --output-dir results/smoke
```

## Outputs

Write:

```text
artifact_card.json
artifact_card.md
```

under the selected output directory.

Generated outputs must not be committed.

## Markdown sections

```text
# Tiny SNN RFID Artifact Card
## Executive Summary
## Main Recommendation
## Evidence Status
## RTL SNN-vs-Baseline Snapshot
## Key Files
## Commands
## Limitations
```

Include when available:

- research recommendation and reason,
- RTL comparison recommendation and reason,
- tiny_snn_v2 cell ratio versus FSM,
- tiny_snn_v2 toggle ratio versus FSM,
- evidence manifest completeness,
- missing output count,
- smoke status,
- key files to inspect.

State clearly that software activity, RTL cell counts, and RTL toggle counts are proxies, not silicon measurements.

## Makefile

Add `artifact-card` to `.PHONY`.

Update `evidence` so it runs `artifact-card` after `evidence-manifest`.

Update `clean` to remove:

```text
results/artifact_card.json
results/artifact_card.md
```

## README

Document:

```text
make artifact-card
```

Explain that the artifact card is a short entry point, while the research report contains details.

## Tests

Add tests that do not run the full evidence pipeline:

1. Missing inputs still produce card outputs.
2. Synthetic research and RTL comparison summaries are loaded.
3. Evidence manifest completeness and missing count are reflected.
4. Smoke mode is detected when smoke summary exists.
5. Markdown contains required sections and proxy limitation text.
6. Makefile contains artifact-card and evidence runs it after evidence-manifest.
7. Clean target removes artifact card outputs.

## Constraints

- Do not add new classifiers.
- Do not add new RTL.
- Do not add heavy dependencies.
- Do not run the full evidence pipeline inside tests.
- Do not commit generated outputs.

## Definition of done

- `make artifact-card` works.
- JSON and Markdown card outputs are generated.
- Full and smoke input roots are supported.
- README and tests are updated.
- Existing workflows keep working.
