# Bugfix Spec: Windows-Portable Clean Target

## Goal

Make `make clean` portable on Windows and Unix-like systems.

A recent clean evidence run failed on Windows because the Makefile invokes Unix `rm` directly:

```make
clean:
	rm -f ...
```

This is inconsistent with the project direction of avoiding Bash/Unix-only wrappers in favor of Python runners.

## Problem

On Windows environments without Unix coreutils, `make clean` fails before evidence can be regenerated cleanly.

The user had to manually clean generated outputs with PowerShell before continuing.

## Required behavior

`make clean` should work anywhere Python works.

It should remove the same generated outputs currently covered by the Makefile clean target, including:

- generated dataset files,
- benchmark outputs,
- sweep/search outputs,
- temporal-hard outputs,
- RTL generated outputs,
- smoke outputs,
- artifact card outputs,
- evidence manifest outputs,
- research report/writeup outputs,
- temporary simulator outputs such as `sim.out`.

It must not remove source files, configs, docs, RTL source, Python source, tests, or specs/prompts.

## Required changes

1. Add a Python cleanup module, for example:

```text
python/tinysnnrfid/clean_outputs.py
python/clean_outputs.py
```

2. Replace the Makefile `clean` recipe with:

```make
clean:
	python python/clean_outputs.py
```

3. Keep the cleanup list explicit and conservative.

4. Support missing files/directories without failing.

5. Print a short summary of removed files/directories.

6. Do not require Bash, `rm`, PowerShell, or platform-specific shell behavior.

## Tests

Add tests that do not require external tools:

1. The cleanup module removes representative generated files.
2. The cleanup module removes representative generated directories.
3. The cleanup module ignores missing files/directories.
4. The cleanup module does not remove source files in `python/`, `rtl/`, `tests/`, `docs/`, or `configs/`.
5. The Makefile `clean` target no longer contains `rm -f`.
6. The Makefile `clean` target calls the Python cleanup wrapper.

## Manual validation

Run:

```bash
python -m pytest
make clean
make rtl-doctor
make rtl-vectors
make rtl-sim
make rtl-synth
make rtl-activity
make rtl-report
make rtl-compare
make research-report
```

Expected on Windows without RTL tools:

- `make clean` succeeds,
- RTL sim/synth may still skip if tools are missing,
- stale outputs are not reused,
- reports show insufficient RTL data rather than stale metrics.

Expected with RTL tools installed:

- `make clean` succeeds,
- fresh RTL evidence can be regenerated.

## Constraints

- Do not add dependencies.
- Do not remove source files.
- Do not change detector RTL behavior.
- Do not change classifier behavior.
- Do not change evidence decision thresholds.
- Do not commit generated outputs.

## Definition of done

- `make clean` is portable on Windows and Unix-like systems.
- No Unix-only command is required by the clean target.
- Tests cover cleanup behavior and Makefile portability.
