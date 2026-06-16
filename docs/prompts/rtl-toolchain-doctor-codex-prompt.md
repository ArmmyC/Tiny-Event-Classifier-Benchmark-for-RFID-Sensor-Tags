# Codex Prompt: RTL Toolchain Doctor

Implement:

```text
docs/specs/rtl-toolchain-doctor.md
```

Goal: add a local preflight command that tells users whether RTL simulation, synthesis, and VCD activity evidence can be generated on their machine.

Required:

1. Add `python/tinysnnrfid/check_rtl_toolchain.py`.
2. Add wrapper `python/check_rtl_toolchain.py`.
3. Add `make rtl-doctor`.
4. Check these tools:
   - `bash`
   - `iverilog`
   - `vvp`
   - `yosys`
5. Write:
   - `results/rtl/toolchain_status.json`
   - `results/rtl/toolchain_status.md`
6. For each tool, report:
   - `found`
   - `path`
   - `version_available`
   - `version`
   - `role`
   - `required_for`
7. Missing tools should not fail by default.
8. Add `--strict` mode that exits nonzero if required tools are missing.
9. Add `--output-dir`, defaulting to `results/rtl`.
10. Do not install tools, modify PATH, or make network calls.
11. Update README.
12. Update clean target if needed.
13. Add tests that do not require RTL tools to be installed.

Constraints:

- Do not add new RTL.
- Do not change detector weights.
- Do not change comparison semantics.
- Do not add dependencies.
- Do not require RTL tools for tests.
- Do not commit generated outputs.

Run:

```bash
python -m pytest
make rtl-doctor
```

Final response: summarize changed files, tests run, and which RTL tools are reported missing or available.
