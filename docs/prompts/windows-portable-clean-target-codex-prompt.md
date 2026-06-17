# Codex Prompt: Windows-Portable Clean Target

Implement:

```text
docs/specs/windows-portable-clean-target.md
```

Goal: make `make clean` work on Windows without requiring Unix `rm`.

Context:
A recent validation run failed because the Makefile clean target uses `rm -f`, which is unavailable in the Windows environment. The project already replaced Bash-dependent RTL flow pieces with Python runners, so clean should follow the same pattern.

Required:
1. Add a Python cleanup implementation, for example:
   - `python/tinysnnrfid/clean_outputs.py`
   - `python/clean_outputs.py`
2. Replace the Makefile clean recipe with:
   - `python python/clean_outputs.py`
3. Remove direct use of `rm -f` from the Makefile clean target.
4. Preserve the current clean behavior by deleting the same generated files/directories currently listed in the Makefile.
5. Missing files/directories must not fail the clean command.
6. Print a short summary of removed files/directories.
7. Keep the cleanup list explicit and conservative.
8. Do not remove source files, configs, docs, RTL source, Python source, tests, specs, or prompts.

Add tests that do not require external tools:
- cleanup removes representative generated files
- cleanup removes representative generated directories
- cleanup ignores missing paths
- cleanup does not remove representative source files
- Makefile clean target no longer contains `rm -f`
- Makefile clean target calls the Python cleanup wrapper

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

Expected:
- `make clean` succeeds on Windows and Unix-like systems
- if RTL tools are missing, RTL sim/synth still skip cleanly and stale outputs are not reused
- if RTL tools are available, fresh RTL evidence can be regenerated

Final response:
Summarize changed files, tests run, whether `make clean` succeeds, and whether stale RTL evidence remains blocked when tools are missing.

Constraints:
- Do not add dependencies.
- Do not commit generated outputs.
- Do not change detector RTL behavior, classifier behavior, or evidence thresholds.
