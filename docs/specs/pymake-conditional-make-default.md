# Bugfix Spec: pymake Conditional MAKE Default

## Goal

Fix recursive `$(MAKE)` targets for Windows users running the Makefile through Python `pymake`, without reintroducing an unconditional `MAKE = python -m pymake` override that can break normal GNU Make users.

## Problem

The Makefile now correctly uses `$(MAKE)` for recursive evidence targets, but local Windows `pymake` fails before running recipes because `$(MAKE)` is not defined unless `MAKE` is assigned inside the Makefile.

The previous unconditional assignment:

```makefile
MAKE = python -m pymake
```

was too aggressive because it forced GNU Make users to use Python `pymake`.

## Required fix

Add a conditional default near the top of `Makefile`:

```makefile
MAKE ?= python -m pymake
```

This should:

- provide a value for Python `pymake` when it does not define `MAKE`,
- avoid overriding GNU Make's built-in `MAKE` value,
- keep recursive recipe lines using `$(MAKE)`.

## Required tests

Update Makefile tests so they verify:

1. Recursive evidence targets use `$(MAKE)`.
2. No recursive recipe under `software-evidence`, `rtl-evidence`, or `evidence` starts with literal `make `.
3. The Makefile does not contain unconditional `MAKE = python -m pymake`.
4. The Makefile contains conditional `MAKE ?= python -m pymake`.
5. Existing Makefile order tests still pass.

## Manual verification

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

On Windows, this should get past the previous `$(MAKE)`/pymake parsing failure.

## Constraints

- Do not change benchmark logic.
- Do not add classifiers.
- Do not add RTL.
- Do not add dependencies.
- Do not commit generated outputs.

## Definition of done

- Windows `pymake` users have a defined `$(MAKE)`.
- GNU Make users are not forced to use Python `pymake`.
- Recursive targets still use `$(MAKE)`.
- Tests cover the conditional assignment.
