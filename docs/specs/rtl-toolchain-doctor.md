# Feature Spec: RTL Toolchain Doctor

## Goal

Add a small local toolchain diagnostic command that tells users whether the optional RTL evidence flow can actually produce simulation, synthesis, and VCD activity data.

The current RTL flow is source-correct, but local evidence is incomplete when these tools are missing:

```text
iverilog
vvp
yosys
bash
```

The existing scripts skip cleanly, which is good for tests, but users need a clearer preflight check before interpreting `insufficient_rtl_data`.

## Required command

Add:

```text
make rtl-doctor
```

The command should run a Python module:

```text
python/tinysnnrfid/check_rtl_toolchain.py
```

with wrapper:

```text
python/check_rtl_toolchain.py
```

## Required outputs

Write:

```text
results/rtl/toolchain_status.json
results/rtl/toolchain_status.md
```

The JSON should include one entry per tool:

```text
bash
iverilog
vvp
yosys
```

Each entry should report:

```text
found
path
version_available
version
role
required_for
```

If version detection fails, keep `found: true` and report the version error clearly.

## Required behavior

- Missing tools should not fail by default.
- Add `--strict` mode that exits nonzero if any required RTL tool is missing.
- Add `--output-dir`, defaulting to `results/rtl`.
- Clearly state that RTL simulation/synthesis results are local-tool proxies, not silicon signoff, silicon area, or measured power.
- Do not install tools automatically.
- Do not modify PATH.
- Do not make network calls.

## Makefile integration

Add `rtl-doctor` to `.PHONY`.

Do not add `rtl-doctor` to `make evidence` yet.

Update `clean` to remove:

```text
results/rtl/toolchain_status.json
results/rtl/toolchain_status.md
```

Because `clean` already removes `results/rtl`, this may already be covered, but include explicit paths if consistent with the Makefile style.

## README updates

Document:

```bash
make rtl-doctor
```

Explain that users should run it before expecting `make rtl-sim`, `make rtl-synth`, or `make rtl-activity` to produce real data.

Mention that if tools are missing, `make rtl-sim` and `make rtl-synth` may skip by design.

## Tests

Add tests that do not require the actual RTL tools to be installed:

1. Tool checking function handles found and missing tools using mocked `shutil.which` / subprocess calls.
2. JSON and Markdown outputs are written.
3. Missing tools produce a clear Markdown section.
4. `--strict` returns nonzero when required tools are missing.
5. Makefile contains `rtl-doctor` and does not add it to `evidence`.
6. README mentions `make rtl-doctor`.
7. Output text includes the proxy/signoff limitation.

## Constraints

- Do not add new RTL.
- Do not change detector weights.
- Do not change comparison semantics.
- Do not add dependencies.
- Do not require RTL tools for tests.
- Do not install tools automatically.
- Do not commit generated outputs.

## Manual workflow

Run:

```bash
python -m pytest
make rtl-doctor
```

Then, if the doctor reports all tools available, run:

```bash
make rtl-vectors
make rtl-sim
make rtl-synth
make rtl-activity
make rtl-report
make rtl-compare
make research-report
```

## Definition of done

- `make rtl-doctor` exists.
- It writes JSON and Markdown status reports.
- It detects `bash`, `iverilog`, `vvp`, and `yosys` without installing anything.
- Strict mode fails when required tools are missing.
- Tests pass without requiring RTL tools.
