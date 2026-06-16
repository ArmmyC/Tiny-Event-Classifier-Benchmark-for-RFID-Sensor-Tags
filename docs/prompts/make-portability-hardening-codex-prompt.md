# Codex Prompt: Make Portability Hardening

Implement:

```text
docs/specs/make-portability-hardening.md
```

Goal: keep the Windows recursive make fix, but avoid forcing GNU Make users to have Python `pymake` installed.

Required:

1. Keep recursive recipe lines using `$(MAKE)`.
2. Remove the unconditional line `MAKE = python -m pymake`.
3. If a default is needed, use conditional assignment, for example:
   `MAKE ?= python -m pymake`
4. Do not change non-recursive Python or bash recipe lines.
5. Update tests so they verify:
   - recursive evidence targets use `$(MAKE)`
   - no recursive recipe starts with literal `make `
   - there is no unconditional `MAKE = python -m pymake`
   - conditional default is accepted if present

Run:

```bash
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
- Do not commit generated outputs.

Final response: summarize changed files and commands run.
