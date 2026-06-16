# Feature Spec: Windows Recursive Make Fix

## Goal

Fix `make evidence` on Windows when the Makefile is run through Python `pymake` or another Make-compatible wrapper.

The current high-level Makefile targets call literal `make` inside recipes. On Windows, the outer `make` command can resolve to a Python entry point, while the nested literal `make` may not exist as an executable. This causes `FileNotFoundError: [WinError 2]` when running `make evidence`.

This is a portability fix, not a benchmark feature.

## Problem

Commands such as:

```makefile
evidence:
	make software-evidence
```

should not hardcode `make`.

Use the standard Make variable:

```makefile
$(MAKE)
```

so recursive targets use the same Make executable that launched the current recipe.

## Required changes

Update `Makefile` recursive invocations in these targets:

```text
software-evidence
rtl-evidence
evidence
```

Replace every nested literal command like:

```text
make benchmark
make rtl-vectors
make software-evidence
```

with:

```text
$(MAKE) benchmark
$(MAKE) rtl-vectors
$(MAKE) software-evidence
```

Do not change non-recursive Python or bash commands.

## Required tests

Add or update tests that do not run the full evidence pipeline:

1. Check that high-level recursive targets use `$(MAKE)`.
2. Check that no recipe line under `software-evidence`, `rtl-evidence`, or `evidence` starts with literal `make `.
3. Keep existing Makefile order tests passing.
4. Keep `make test` passing.

## Manual verification

Run:

```bash
make test
make evidence-smoke
make evidence
```

On systems without Icarus Verilog or Yosys, RTL sim/synth may still skip by design, but `make evidence` should not fail because of nested literal `make` resolution.

## Constraints

- Do not add new classifiers.
- Do not add new RTL.
- Do not change benchmark logic.
- Do not commit generated outputs.
- Keep existing targets and output paths unchanged.

## Definition of done

- `make evidence` no longer fails due to nested `make` not being found on Windows.
- Recursive Makefile calls use `$(MAKE)`.
- Tests cover this behavior.
- Existing tests pass.
