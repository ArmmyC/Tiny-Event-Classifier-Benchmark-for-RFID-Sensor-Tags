# Reproducibility

## Current Checkpoint

Use `docs/final-evidence-milestone.md` as the current checkpoint for evidence values and recommendations.

Current milestone values:

- Sparse SNN RTL baseline: `tiny_snn_v2_sparse_activity`.
- Simulation status: pass.
- Synthesis status: available.
- Cell-count proxy: 610 cells.
- Cell ratio vs FSM: 3.961x.
- Toggle-count proxy: 73189 toggles.
- Toggle ratio vs FSM: 1.117x.
- RTL recommendation: `optimize_snn_rtl_before_more_features`.
- Research recommendation: `continue_snn_optimization`.
- Evidence manifest: complete with 0 missing outputs.

## Full Evidence Regeneration

From the repository root:

```powershell
python -m pytest
make clean
make rtl-doctor
make evidence
```

`make evidence` runs software evidence, RTL evidence, the research report, the evidence manifest, the artifact card, and the research writeup.

For a more explicit step-by-step RTL flow:

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

## Software Evidence

The software evidence can be regenerated independently:

```powershell
make software-evidence
make research-report
```

This flow covers the benchmark, sweeps, SNN searches, temporal-hard benchmark, temporal-hard sweep, and temporal-hard SNN search.

Software evidence is necessary for the research recommendation, but it does not replace RTL simulation, synthesis, or activity evidence.

## RTL Evidence

The RTL evidence can be regenerated independently:

```powershell
make rtl-doctor
make rtl-vectors
make rtl-sim
make rtl-synth
make rtl-activity
make rtl-report
make rtl-compare
```

`make rtl-doctor` should find the required local tools before RTL metrics are claimed. On Windows with OSS CAD Suite, load the suite environment before running RTL commands. For example:

```powershell
$root = "D:\ArmmyWorkspace\SiliconCraft\tools\oss-cad-suite"
. "$root\environment.ps1"
make rtl-doctor
```

If the tools are missing, do not claim fresh RTL metrics. Regenerate software evidence and the research report, then report that RTL evidence is incomplete because local RTL tools are unavailable.

## Freshness And Stale Artifact Protection

The pipeline writes current-run status files for simulation, synthesis, and activity evidence. Downstream summaries use those status files to decide whether outputs are fresh.

The important status files are:

- `results/rtl/sim_status.json`
- `results/rtl/synth_status.json`
- `results/rtl/activity_status.json`

If current-run evidence is missing or incomplete, stale RTL outputs are ignored. This prevents old simulation logs, synthesis JSON files, or VCD activity summaries from being mistaken for fresh evidence.

## Portable Clean

`make clean` uses the repository's Python cleaner:

```powershell
make clean
```

The clean flow is designed to be portable on Windows and does not depend on Unix `rm`, Bash, or PowerShell-specific delete commands. After cleaning, rerun the evidence pipeline before interpreting generated results.

## Main Generated Evidence To Inspect

After a full evidence run, inspect:

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

The evidence manifest should report completion with 0 missing outputs for the current full milestone.

## Next Architecture-Level Questions

The next useful SNN research branch should answer one of these questions:

- Can membrane state be reduced or shared without losing the behavior found by software search?
- Can sparse update logic be made more direct so inactive channels create less fixed overhead?
- Can the temporal motif be represented by a hybrid FSM plus sparse scoring path?
- Can the SNN preserve its low toggle-ratio proxy while reducing the cell-count proxy below the current 3.961x FSM ratio?
- Can a more constrained SNN architecture beat the LUT-like baseline on a scenario where temporal noise is harder?

Branches that only rearrange local RTL without a clear cost hypothesis are not yet strongly justified.
