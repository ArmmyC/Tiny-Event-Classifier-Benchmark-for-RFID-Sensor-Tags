# Tiny SNN RFID: Project Readable Report

## 1. Executive Summary

This repository is a benchmark-first research study about tiny decision logic for RFID-style sensor-tag events. It asks whether a very small spiking-neural-network-inspired classifier can be useful when compared with simpler digital logic such as threshold detectors, finite-state machines, and LUT-like rules.

The current answer is cautious but encouraging. The sparse SNN RTL candidate, `tiny_snn_v2_sparse_activity`, now has fresh evidence from a complete run:

- `python -m pytest` passed: 188 passed.
- `make evidence` completed successfully.
- The evidence manifest is complete with 0 missing outputs.
- `tiny_snn_v2_sparse_activity` simulation passed.
- Synthesis evidence is available.
- Cell-count proxy: 610 cells.
- Cell ratio vs FSM: 3.961x.
- Toggle-count proxy: 73189 toggles.
- Toggle ratio vs FSM: 1.117x.
- RTL recommendation: `optimize_snn_rtl_before_more_features`.
- Research recommendation: `continue_snn_optimization`.

The important interpretation is this: the sparse SNN is much more plausible than the earlier dense SNN direction, but it is still not compact enough to beat the simple FSM/LUT-style baselines as an implementation choice. It should be preserved as the current SNN RTL baseline and studied further, but the next work should simplify the architecture before adding more features.

All hardware-side numbers in this report are local-tool proxy metrics. Cell count is a synthesis proxy, not silicon area. Toggle count is a VCD activity proxy, not measured power or measured energy.

## 2. Project Motivation

RFID sensor tags often operate under strict constraints. They may have limited energy, limited logic budget, and simple event-driven behavior. Many machine-learning or AI approaches for RFID-related sensing run outside the tag, such as on a reader, gateway, phone, or server. This project explores a smaller question: could a tiny SNN-style block be useful inside or near RFID sensor-tag decision logic?

The project does not assume the SNN will win. In fact, it treats the SNN as one candidate among simpler digital classifiers. That benchmark-first attitude is important because many RFID-style decisions are simple enough that conventional logic may be the right answer.

The useful outcome is not necessarily "SNN wins." A negative result is still valuable if it shows that a compact FSM or LUT-like classifier solves the problem more cleanly.

## 3. Main Research Question

The main research question is:

Can a tiny event-driven SNN-style classifier provide useful noise robustness or switching-activity reduction for sparse RFID sensor-tag decisions while remaining competitive against threshold logic, FSMs, and LUT-like digital classifiers?

The current evidence says:

- The SNN path is still worth studying.
- The sparse SNN is not yet a clear hardware winner.
- FSM and LUT-like baselines remain strong.
- The next RTL work should focus on reducing SNN overhead, not adding more features.

## 4. Benchmark Overview

The benchmark task is a noisy temporal event detector.

Each cycle has a 4-bit event vector. The classifier observes a sequence of these event vectors and decides whether the sequence contains a valid event pattern.

The default valid motif is:

```text
channel 0 fires
then channel 1 fires
then channel 2 fires
```

The classifier outputs:

- `0`: ignore or invalid sequence.
- `1`: valid event sequence.

Noise spikes may occur on any channel. The task is intentionally small, but it includes three properties that make SNN-style logic worth testing:

- sparse events
- short temporal memory
- noisy inputs

The benchmark therefore asks a practical question: if an SNN cannot show a useful tradeoff on this kind of small sparse temporal problem, it is unlikely to be attractive for very constrained RFID-style tag logic.

## 5. Classifier Families Compared

### Threshold Logic

Threshold logic is the simplest family. It looks for event conditions using compact combinational or near-stateless logic.

This kind of baseline is important because some sensing tasks do not need temporal memory or learned behavior. If threshold logic performs well enough, the SNN has little reason to exist.

### FSM

The FSM baseline tracks the ordered temporal motif directly. For example, it can move through states such as "waiting for channel 0," "saw channel 0, waiting for channel 1," and "saw channel 1, waiting for channel 2."

FSMs are strong for this benchmark because the valid pattern is short, discrete, and ordered. A small FSM can represent that behavior with predictable control logic and little storage.

### LUT-like Logic

The LUT-like classifier represents a compact rule-table or decision-tree-style baseline. It is useful when the input space and decision boundary are small enough to encode directly.

For fixed event patterns, a LUT-like design can avoid the overhead of membrane state, neuron updates, and weight accumulation.

### tiny_snn_v2

`tiny_snn_v2` is the more general tiny SNN candidate. It is inspired by integrate-and-fire or leaky-integrate-and-fire behavior. It uses small fixed integer weights and local state rather than training at runtime.

This design is useful as a research prototype, but the earlier dense direction carried too much RTL overhead compared with simple baselines.

### tiny_snn_v2_sparse_activity

`tiny_snn_v2_sparse_activity` is the current sparse SNN RTL baseline. It is the candidate preserved by the latest milestone.

The point of the sparse version is to keep the SNN idea alive while reducing unnecessary RTL cost and switching behavior. The current evidence shows that this direction is much more credible than the earlier dense SNN RTL path, but it still has a much higher cell-count proxy than the FSM baseline.

## 6. Software Evidence Summary

The software evidence flow evaluates classifier behavior before drawing RTL conclusions. It includes:

- dataset generation
- benchmark evaluation
- parameter sweeps
- SNN candidate search
- temporal-hard benchmark scenarios
- temporal-hard SNN search

The software flow helps answer whether the SNN family has an algorithmic reason to exist on the benchmark. It compares functional behavior such as accuracy, precision, recall, F1 score, false-positive behavior, and false-negative behavior.

The current research report recommendation is `continue_snn_optimization`. That means the software-side evidence is strong enough to keep studying SNN candidates, but not strong enough to skip hardware discipline.

Software activity figures should also be treated carefully. They are operation or activity proxies inside the software benchmark, not measured hardware power or measured energy.

## 7. RTL Evidence Summary

The RTL evidence flow takes the benchmark into SystemVerilog-level comparison. It uses shared vectors, runs simulation, runs synthesis where tools are available, summarizes VCD activity, and compares the SNN candidate against baseline RTL designs.

The main RTL stages are:

- `make rtl-doctor`: check local RTL tools.
- `make rtl-vectors`: export shared test vectors.
- `make rtl-sim`: run RTL simulation.
- `make rtl-synth`: run Yosys synthesis for cell-count proxy evidence.
- `make rtl-activity`: summarize VCD toggle-count proxy evidence.
- `make rtl-report`: build RTL summaries.
- `make rtl-compare`: compare RTL designs and produce the recommendation.

For the current milestone, the sparse SNN simulation passed and synthesis evidence is available. Its cell-count proxy is 610 cells, and its toggle-count proxy is 73189 toggles.

Compared with the FSM baseline, the sparse SNN has:

- 3.961x the FSM cell-count proxy.
- 1.117x the FSM toggle-count proxy.

This is the core tradeoff. The sparse SNN is still much larger by the local synthesis proxy, but its activity proxy is close to the FSM.

## 8. Final Fresh Evidence Milestone

The current verified milestone is the clean full evidence run captured in `docs/final-evidence-milestone.md`.

That milestone reports:

- Test suite: 188 passed.
- Clean evidence run: completed from a clean generated-output state.
- `make evidence`: completed successfully.
- Evidence manifest: complete with 0 missing outputs.
- RTL simulation: regenerated.
- RTL synthesis: regenerated.
- RTL activity summary: regenerated.
- RTL comparison: regenerated.
- Research report, artifact card, and research writeup: regenerated.
- Stale artifact protection: implemented.
- Portable clean: implemented.

For `tiny_snn_v2_sparse_activity`, the milestone reports:

- Simulation status: pass.
- Synthesis status: available.
- Cell-count proxy: 610 cells.
- Cell ratio vs FSM: 3.961x.
- Toggle-count proxy: 73189 toggles.
- Toggle ratio vs FSM: 1.117x.

The RTL recommendation remains `optimize_snn_rtl_before_more_features`.

The broader research recommendation remains `continue_snn_optimization`.

## 9. What The Results Mean

The results mean that the sparse SNN has become a credible research candidate, not that it is the best implementation today.

The 610-cell proxy is a meaningful improvement for the SNN path, but the 3.961x ratio vs FSM shows that the SNN still carries a large complexity overhead. For a small RFID-style motif detector, that overhead matters.

The 1.117x toggle ratio vs FSM is more encouraging. It means that under the current VCD activity proxy, the sparse SNN is close to the FSM in switching activity. That supports continued study of sparse event-driven architecture.

Together, these numbers point to a clear interpretation:

- The sparse SNN is no longer obviously too wasteful to study.
- The FSM and LUT-like baselines remain more compact.
- The next SNN work should reduce fixed RTL overhead.
- Adding new features before optimizing the architecture would be premature.

## 10. Why FSM/LUT Baselines Are Strong

The FSM and LUT-like baselines are strong because the benchmark task is small, discrete, and structured.

An FSM can directly encode the required event order. It does not need to approximate temporal behavior through neuron state or weighted accumulation. It simply tracks where it is in the expected sequence.

A LUT-like classifier can be strong because the event vector is small and the decision boundary is compact. If the task can be represented as a small set of rules, a table-like or decision-tree-like design avoids the overhead of SNN machinery.

This is why the baselines are fair and important. They are the kinds of designs a digital designer would naturally try first. The SNN must earn its place against them.

## 11. Why Sparse SNN Is Still Worth Studying

The sparse SNN is still worth studying because it targets the part of the problem where SNNs might plausibly help: sparse temporal events under noise.

The current sparse RTL result shows:

- the design simulates correctly on the current vectors
- synthesis evidence is available
- the activity proxy is close to the FSM
- the design is now much more plausible than the earlier dense SNN direction

This does not prove that the SNN is better. It says the idea is still alive. In research terms, the sparse SNN has crossed from "probably too expensive" into "worth one more architecture-level investigation."

The next investigation should not be another small local rewrite. It should test a real architectural simplification, such as reducing membrane state, sharing state, simplifying spike accumulation, or combining a small FSM with sparse scoring.

## 12. Limitations

The most important limitation is that the hardware metrics are proxies.

Cell count is a synthesis proxy generated by local open-source synthesis. It is useful for comparing RTL designs inside this repository, but it is not silicon area.

Toggle count is a VCD activity proxy generated from local RTL simulation traces. It is useful for comparing switching activity under the current vectors, but it is not measured power and not measured energy.

This project does not claim:

- silicon area
- measured power
- measured energy
- gate-level power signoff
- physical design signoff
- timing closure
- production RFID tag integration readiness

The benchmark is also intentionally small. It is useful for feasibility work, but it does not prove broad conclusions about all SNNs or all RFID systems.

Finally, RTL evidence depends on local tool availability. The full evidence run needs tools such as Icarus Verilog and Yosys. If these tools are missing, the pipeline should report incomplete RTL evidence and ignore stale RTL artifacts.

## 13. Reproducibility Guide

The current checkpoint is `docs/final-evidence-milestone.md`.

To regenerate the full evidence from the repository root:

```powershell
python -m pytest
make clean
make rtl-doctor
make evidence
```

`make evidence` runs software evidence, RTL evidence, the research report, the evidence manifest, the artifact card, and the research writeup.

For an explicit RTL-focused sequence:

```powershell
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
make evidence-manifest
make artifact-card
make research-writeup
```

On Windows with OSS CAD Suite, load the suite environment before running RTL commands. For example:

```powershell
$root = "D:\ArmmyWorkspace\SiliconCraft\tools\oss-cad-suite"
. "$root\environment.ps1"
make rtl-doctor
```

After a full evidence run, the main generated outputs to inspect are:

- `results/rtl/sim_status.json`
- `results/rtl/synth_status.json`
- `results/rtl/activity_status.json`
- `results/rtl/rtl_summary.json`
- `results/rtl/rtl_activity_summary.json`
- `results/rtl/rtl_comparison_summary.json`
- `results/rtl/rtl_comparison_report.md`
- `results/research_decision_report.md`
- `results/evidence_manifest.md`
- `results/artifact_card.md`
- `results/research_writeup.md`

The stale artifact protection matters. If current-run simulation, synthesis, or activity status is missing or incomplete, old outputs should be ignored rather than treated as fresh evidence.

The portable clean flow matters too. `make clean` uses the repository's Python cleaner and does not depend on Unix `rm`, Bash, or PowerShell-specific delete commands.

## 14. Next Research Directions

The next research work should focus on architecture-level SNN simplification.

Useful questions include:

- Can membrane state be reduced or shared without losing the useful software-search behavior?
- Can sparse update logic be made more direct so inactive channels create less fixed overhead?
- Can the temporal motif be represented by a hybrid FSM plus sparse scoring path?
- Can the sparse SNN keep its low toggle-count proxy while reducing its cell-count proxy below the current 3.961x FSM ratio?
- Can a more constrained SNN architecture beat the LUT-like baseline on a harder temporal-noise scenario?

The current recommendation is not to add more features to the SNN RTL. The next branch is justified only if it tests a clear cost-reduction hypothesis.

## 15. Glossary of Terms

**Activity proxy**

A generated estimate-like metric used for relative comparison. In this project, toggle counts from VCD files are activity proxies. They are not measured power or measured energy.

**Cell-count proxy**

A local synthesis count used to compare RTL complexity between designs. It is not silicon area.

**FSM**

Finite-state machine. A digital design that tracks progress through a set of states. FSMs are strong for ordered event patterns.

**Icarus Verilog**

An open-source Verilog/SystemVerilog simulation tool used by the RTL simulation flow when available.

**LUT-like logic**

A compact rule-table or decision-tree-style classifier. It is useful for small discrete decision problems.

**RTL**

Register-transfer level. A hardware design abstraction written in languages such as SystemVerilog.

**SNN**

Spiking neural network. In this project, the SNN is a tiny fixed-weight, event-driven classifier inspired by integrate-and-fire behavior.

**Stale artifact protection**

Pipeline logic that prevents old generated outputs from being mistaken for fresh evidence when current-run status is missing or incomplete.

**Synthesis**

The process of translating RTL into a lower-level logic representation. In this project, synthesis provides proxy cell counts for comparison.

**tiny_snn_v2**

The general second-version tiny SNN candidate with fixed integer weights and small local state.

**tiny_snn_v2_sparse_activity**

The current sparse SNN RTL baseline. It is the milestone candidate with passing simulation, available synthesis evidence, 610 cell-count proxy, and 73189 toggle-count proxy.

**Toggle count**

The number of signal transitions observed in simulation traces. In this project, toggle count is a VCD activity proxy, not a measured power or energy value.

**VCD**

Value Change Dump. A waveform trace format used to record signal changes during RTL simulation.

**Yosys**

An open-source synthesis tool used by this project to generate local synthesis proxy evidence.
