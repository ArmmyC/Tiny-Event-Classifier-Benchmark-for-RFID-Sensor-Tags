# Codex Prompt: Research Writeup Generator

Implement:

```text
docs/specs/research-writeup-generator.md
```

Goal: add `make research-writeup` to generate a paper-style Markdown report from existing evidence outputs.

Required:

1. Add `python/tinysnnrfid/build_research_writeup.py`.
2. Add `python/build_research_writeup.py`.
3. Add Makefile target `research-writeup`.
4. Read, when present:
   - `artifact_card.json`
   - `research_decision_summary.json`
   - `research_decision_report.md`
   - `rtl/rtl_comparison_summary.json`
   - `rtl/rtl_comparison_report.md`
   - `evidence_manifest.json`
5. Support `--input-root` and `--output-dir`.
6. Write:
   - `research_writeup.md`
   - `research_writeup_summary.json`
7. Update `evidence` so it runs `research-writeup` after `artifact-card`.
8. Update `clean` for writeup outputs.
9. Update README.
10. Add tests. Do not run the full evidence pipeline in tests.

The writeup must include these sections:

```text
Abstract
Research Question
Methodology
Dataset and Scenario Suites
Classifiers Compared
Software Evidence Summary
RTL Evidence Summary
Decision Summary
Limitations
Reproducibility
Next Steps
```

State clearly that software activity, RTL cell counts, and RTL toggle counts are proxies, not silicon measurements or signoff results.

Constraints:

- Do not add new classifiers.
- Do not add new RTL.
- Do not add heavy dependencies.
- Do not commit generated outputs.
- Keep existing workflows working.

Run:

```bash
make test
make research-writeup
```
