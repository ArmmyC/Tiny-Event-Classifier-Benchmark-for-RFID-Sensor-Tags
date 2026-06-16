# Bugfix Spec: Dependency-Only Evidence Targets

## Goal

Fix `make test`, `make evidence-smoke`, and `make evidence` under Windows Python `pymake` while keeping the Makefile portable for normal GNU Make users.

## Problem

The Makefile currently uses recursive recipe lines with `$(MAKE)` for aggregate targets. That is correct GNU Make style, but this specific Python `pymake` implementation fails before running recipes with:

```text
PymakeKeyError: "No substitution for macros: {'$(MAKE)'}"
```

Adding:

```makefile
MAKE = python -m pymake
```

fixes this `pymake` behavior but unconditionally overrides GNU Make's built-in `MAKE`, which is not portable.

Adding:

```makefile
MAKE ?= python -m pymake
```

would be ideal for GNU Make, but this `pymake` parser does not recognize `?=`.

Therefore, the robust fix is to avoid recursive make recipe lines for aggregate targets.

## Required fix

Convert high-level aggregate targets to dependency-only targets.

Replace this style:

```makefile
software-evidence:
	$(MAKE) benchmark
	$(MAKE) sweep
```

with this style:

```makefile
software-evidence: benchmark sweep snn-search temporal-benchmark temporal-sweep temporal-snn-search
```

Apply to:

```text
software-evidence
rtl-evidence
evidence
```

Expected shape:

```makefile
software-evidence: benchmark sweep snn-search temporal-benchmark temporal-sweep temporal-snn-search

rtl-evidence: rtl-vectors rtl-sim rtl-synth rtl-activity rtl-report rtl-compare

evidence: software-evidence rtl-evidence research-report evidence-manifest artifact-card research-writeup
```

Do not add `MAKE = ...` or `MAKE ?= ...`.

Do not change non-recursive Python or bash commands.

## Required behavior

- `make test` should run normally under Windows `pymake`.
- `make evidence-smoke` should run normally under Windows `pymake`.
- `make evidence` should get past the previous `$(MAKE)` substitution failure.
- Normal GNU Make users should not be forced to install or use Python `pymake`.

## Tests

Update Makefile tests so they verify:

1. `software-evidence`, `rtl-evidence`, and `evidence` exist.
2. Those targets are dependency-only aggregate targets with no recipe lines.
3. The dependency lists include the expected subtargets.
4. No line in the Makefile contains `MAKE = python -m pymake`.
5. No line in the Makefile contains `MAKE ?= python -m pymake`.
6. Existing order expectations are updated to dependency-list checks.

Do not require the tests to run the full evidence pipeline.

## Manual verification

Run:

```bash
python -m pytest
make test
make evidence-smoke
```

If possible, run:

```bash
make evidence
```

If full evidence reaches RTL simulation/synthesis and skips due to missing local tools, that is acceptable. It must not fail from `$(MAKE)` substitution.

## Constraints

- Do not change benchmark logic.
- Do not add classifiers.
- Do not add RTL.
- Do not add dependencies.
- Do not commit generated outputs.

## Definition of done

- Aggregate evidence targets are dependency-only.
- The Makefile contains no recursive `make`, no `$(MAKE)`, and no `MAKE` override for these aggregate targets.
- Windows `pymake` can parse and run `make test` and `make evidence-smoke`.
- `make evidence` no longer fails from missing `$(MAKE)` substitution.
- Tests cover the dependency-only design.
