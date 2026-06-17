# Methodology

## Benchmark Goal

This project asks whether a very small event-driven SNN-style classifier can be a credible candidate for RFID sensor-tag decision logic. The target is not a full RFID tag chip and not a production neuromorphic processor. The benchmark is a feasibility study for tiny event filtering under sparse, noisy temporal inputs.

The central question is deliberately comparative: does the SNN provide enough functional or activity-side reason to justify its extra RTL complexity against compact conventional baselines?

The current milestone uses `tiny_snn_v2_sparse_activity` as the sparse SNN RTL baseline. Its generated evidence shows passing simulation, available synthesis, and current activity evidence from a complete evidence run.

## Classifier Families

The benchmark compares four families:

- Threshold logic: a compact stateless or near-stateless detector for simple event conditions.
- FSM logic: a small explicit temporal-state baseline for motif tracking and debounce-like behavior.
- LUT-like logic: a compact decision-table or decision-tree-style baseline.
- Tiny SNN logic: integrate-and-fire-inspired event logic with small fixed weights and local state.

The baselines are intentionally strong. A tiny SNN is useful only if it survives comparison against simple digital designs that are natural fits for fixed RFID sensor-tag control tasks.

## Software Search Flow

The software flow generates synthetic event sequences and evaluates classifier behavior before RTL conclusions are drawn. It covers:

- default benchmark generation and evaluation
- parameter sweeps across noise, sparsity, and sequence conditions
- SNN search over small candidate configurations
- temporal-hard benchmark and sweep evidence
- temporal-hard SNN search evidence

The software flow is used to decide whether the SNN family has algorithmic reason to exist on this benchmark. It does not prove hardware efficiency by itself.

The project-level evidence command runs the software evidence before the RTL evidence:

```powershell
make software-evidence
```

or as part of the full pipeline:

```powershell
make evidence
```

## RTL Evidence Flow

The RTL flow exports shared vectors, simulates RTL designs, runs synthesis where local tools are available, summarizes VCD activity, and compares SNN evidence against the conventional baselines.

The main RTL stages are:

- `make rtl-doctor`: check required local RTL tools.
- `make rtl-vectors`: export shared test vectors.
- `make rtl-sim`: compile and simulate RTL.
- `make rtl-synth`: run Yosys synthesis for cell-count proxy evidence.
- `make rtl-activity`: summarize VCD toggle-count proxy evidence.
- `make rtl-report`: summarize RTL simulation and synthesis outputs.
- `make rtl-compare`: compare RTL baselines and the SNN candidate.

The current complete evidence milestone reports:

- `tiny_snn_v2_sparse_activity` simulation: pass
- synthesis: available
- cell-count proxy: 610 cells
- cell ratio vs FSM: 3.961x
- toggle-count proxy: 73189 toggles
- toggle ratio vs FSM: 1.117x
- RTL recommendation: `optimize_snn_rtl_before_more_features`
- research recommendation: `continue_snn_optimization`
- evidence manifest: complete with 0 missing outputs

## Evidence Hygiene

The evidence pipeline includes stale artifact protection. Current-run status files are used to decide whether simulation, synthesis, and activity outputs are fresh enough to summarize. If current RTL evidence is missing or incomplete, stale outputs are ignored rather than silently reused.

The clean flow is Windows-portable and implemented through the project cleaner rather than shell-specific `rm`, Bash, or PowerShell behavior. This matters because the benchmark is intended to be rerunnable on a normal Windows development machine with local open-source RTL tools installed.

## Metric Semantics

Cell counts are synthesis proxies from local open-source synthesis output. They are useful for relative RTL comparison within this project.

Toggle counts are VCD activity proxies from local simulation traces. They are useful for relative switching-activity comparison under the exported test vectors.

These metrics are not silicon area, measured power, measured energy, timing signoff, physical implementation signoff, or production readiness evidence.
