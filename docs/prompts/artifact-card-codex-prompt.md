# Codex Prompt: Artifact Card

Implement:

```text
docs/specs/artifact-card.md
```

Goal: add `make artifact-card` to generate a short summary card for the evidence outputs.

Required:

1. Add `python/tinysnnrfid/build_artifact_card.py`.
2. Add `python/build_artifact_card.py`.
3. Add Makefile target `artifact-card`.
4. Read, when present:
   - `research_decision_summary.json`
   - `rtl/rtl_comparison_summary.json`
   - `evidence_manifest.json`
   - `smoke_summary.json`
5. Support `--input-root` and `--output-dir`.
6. Write `artifact_card.json` and `artifact_card.md`.
7. Update `evidence` so it runs `artifact-card` after `evidence-manifest`.
8. Update `clean` for artifact card outputs.
9. Update README.
10. Add tests. Do not run the full evidence pipeline in tests.

Run:

```bash
make test
make artifact-card
```

Keep existing workflows working and do not commit generated outputs.
