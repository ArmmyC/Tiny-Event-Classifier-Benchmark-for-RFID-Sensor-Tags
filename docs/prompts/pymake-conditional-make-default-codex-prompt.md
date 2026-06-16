# Codex Prompt: pymake Conditional MAKE Default

Implement:

```text
docs/specs/pymake-conditional-make-default.md
```

Goal: fix Windows `pymake` recursion by defining `MAKE` conditionally, without forcing GNU Make users to use `pymake`.

Required:

1. Add this near the top of `Makefile`:
   `MAKE ?= python -m pymake`
2. Keep recursive evidence targets using `$(MAKE)`.
3. Do not restore unconditional `MAKE = python -m pymake`.
4. Do not change non-recursive Python or bash recipe lines.
5. Update tests to verify:
   - recursive evidence targets use `$(MAKE)`
   - no recursive recipe starts with literal `make `
   - no unconditional `MAKE = python -m pymake` exists
   - conditional `MAKE ?= python -m pymake` exists

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

Final response: summarize changed files, tests run, and whether the Windows `pymake` failure is fixed.
