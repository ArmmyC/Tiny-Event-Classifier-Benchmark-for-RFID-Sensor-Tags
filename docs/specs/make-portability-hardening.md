# Feature Spec: Make Portability Hardening

## Goal

Make the recursive evidence targets portable across both Windows `pymake` and normal GNU Make environments.

The previous patch correctly replaced nested literal `make` recipe lines with `$(MAKE)`. However, the Makefile now hardcodes:

```makefile
MAKE = python -m pymake
```

That can help on a Windows machine where `pymake` is installed, but it can break normal GNU Make users because recursive targets will require the Python `pymake` module even when GNU Make is already available.

This is a portability patch only.

## Required behavior

1. Recursive recipe lines should keep using `$(MAKE)`.
2. Do not hardcode `MAKE = python -m pymake` in a way that overrides GNU Make's built-in `MAKE` value.
3. If a default is still needed for Python `pymake`, use a conditional assignment such as:

```makefile
MAKE ?= python -m pymake
```

4. Keep the Windows recursive make fix intact.
5. Keep `make evidence`, `make evidence-smoke`, and `make test` working.

## Required tests

Update Makefile tests so they check:

1. Recursive evidence targets use `$(MAKE)`.
2. No recipe line under `software-evidence`, `rtl-evidence`, or `evidence` starts with literal `make `.
3. The Makefile does not contain an unconditional `MAKE = python -m pymake` assignment.
4. If the Makefile defines a default MAKE value, it uses conditional assignment.

## Constraints

- Do not change benchmark logic.
- Do not add new classifiers.
- Do not add new RTL.
- Do not add dependencies unless clearly necessary.
- Do not commit generated outputs.

## Manual verification

Run:

```bash
make test
make evidence-smoke
make evidence
```

If full evidence is too slow, at least run `make test` and `make evidence-smoke`.

## Definition of done

- Recursive targets still use `$(MAKE)`.
- GNU Make users are not forced to have `pymake` installed.
- Windows `pymake` users still avoid literal nested `make` failures.
- Tests cover the Makefile portability behavior.
