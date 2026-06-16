# Codex Prompt: Windows Recursive Make Fix

Implement:

```text
docs/specs/windows-recursive-make-fix.md
```

Goal: fix `make evidence` on Windows by replacing recursive literal `make` calls with `$(MAKE)`.

Required:

1. Update `Makefile`.
2. In recursive high-level targets, replace nested commands like `make benchmark` with `$(MAKE) benchmark`.
3. Apply this to:
   - `software-evidence`
   - `rtl-evidence`
   - `evidence`
4. Do not change non-recursive Python or bash commands.
5. Add or update tests so high-level recursive targets use `$(MAKE)` and do not start recipe lines with literal `make `.
6. Keep existing Makefile order tests passing.

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

- Do not add new classifiers.
- Do not add new RTL.
- Do not change benchmark logic.
- Do not commit generated outputs.

Final response: summarize changed files, tests run, and whether `make evidence` now works or why it could not be fully run.
