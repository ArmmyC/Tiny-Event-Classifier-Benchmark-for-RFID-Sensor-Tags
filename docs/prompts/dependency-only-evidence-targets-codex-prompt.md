# Codex Prompt: Dependency-Only Evidence Targets

Implement:

```text
docs/specs/dependency-only-evidence-targets.md
```

Goal: fix Windows Python `pymake` by removing recursive `$(MAKE)` recipe lines from high-level evidence targets.

Required:

1. Convert `software-evidence` to a dependency-only target:
   `software-evidence: benchmark sweep snn-search temporal-benchmark temporal-sweep temporal-snn-search`
2. Convert `rtl-evidence` to a dependency-only target:
   `rtl-evidence: rtl-vectors rtl-sim rtl-synth rtl-activity rtl-report rtl-compare`
3. Convert `evidence` to a dependency-only target:
   `evidence: software-evidence rtl-evidence research-report evidence-manifest artifact-card research-writeup`
4. Remove `MAKE ?= python -m pymake` if present.
5. Do not add `MAKE = python -m pymake`.
6. Do not change non-recursive Python or bash recipe lines.
7. Update tests to check the dependency-only aggregate target design.
8. Do not run the full evidence pipeline inside tests.

Run:

```bash
python -m pytest
make test
make evidence-smoke
```

If possible, also run:

```bash
make evidence
```

Constraints:

- Do not change benchmark logic.
- Do not add classifiers.
- Do not add RTL.
- Do not add dependencies.
- Do not commit generated outputs.

Final response: summarize changed files, commands run, and whether the `$(MAKE)`/pymake failure is fixed.
