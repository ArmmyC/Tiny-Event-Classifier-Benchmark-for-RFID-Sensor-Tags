# Tiny SNN RFID

Feasibility-study scaffold for comparing tiny Spiking Neural Network logic against conventional digital classifiers for RFID-style sensor-tag event decisions.

This repository is intentionally benchmark-first. The SNN is treated as one candidate, not as the expected winner.

## Core question

Can a tiny event-driven SNN-style classifier provide useful noise robustness or switching-activity reduction for sparse RFID sensor-tag decisions, while remaining competitive against threshold logic, FSMs, and LUT or decision-tree logic?

## Current benchmark

Minimal task: noisy event detector.

Input per cycle:

- 4-bit event vector
- sparse valid event motif
- random noise spikes

Sequence label:

- `0`: ignore or invalid sequence
- `1`: valid event sequence

Default valid motif:

```text
channel 0 fires, then channel 1 fires, then channel 2 fires
```

Noise spikes may occur on any channel.

Classifier candidates include simple threshold logic, an ordered-pattern FSM,
a LUT-like rule baseline, the legacy `tiny_snn` integer detector, and
`tiny_snn_v2`. The v2 SNN keeps the legacy model available for comparison but
adds a small hidden layer of fixed-weight integer IF/LIF neurons feeding one
output accumulator; it is still hand-configured and does not perform training.

## Repository layout

```text
.
├── docs/                  Research notes and experiment plan
├── python/                Dataset generation and Python classifiers
├── rtl/                   SystemVerilog classifier candidates
├── tb/                    Simple SystemVerilog testbench skeleton
├── scripts/               Utility scripts for simulation and VCD counting
├── synth/                 Yosys synthesis script placeholder
├── data/generated/        Generated datasets and test vectors
└── results/               Evaluation outputs
```

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

make data
make eval
make benchmark
make sweep
make snn-search
```

Or run directly:

```bash
PYTHONPATH=python python -m tinysnnrfid.generate_dataset --config configs/default.json
PYTHONPATH=python python -m tinysnnrfid.run_benchmark --config configs/default.json
PYTHONPATH=python python -m tinysnnrfid.run_sweep --config configs/sweep_default.json
PYTHONPATH=python python -m tinysnnrfid.run_snn_search --config configs/snn_search_default.json
```

On PowerShell, set the module path with `$env:PYTHONPATH = "python"` before the two
`python -m` commands. The compatibility entry points `python/generate_dataset.py`
and `python/evaluate_python.py` accept the same config-oriented arguments.

The default JSON config controls dataset size, sequence dimensions, pattern,
noise, jitter, dropout, seed, enabled classifiers, and output paths. JSON is the
dependency-free default; YAML is also accepted when PyYAML is installed.

## Benchmark outputs

Dataset generation writes:

- `data/generated/inputs.npy`: `uint8` inputs shaped `[samples, cycles, channels]`
- `data/generated/labels.npy`: binary labels shaped `[samples]`
- `data/generated/metadata.json`: effective config, timestamp, seed, shape, and label counts
- `data/generated/scenario_tags.json`: one diagnostic scenario tag per sample
- `data/generated/test_vectors.txt`: one RTL-friendly sample per line
- `data/generated/noisy_event_dataset.npz` and `vectors.hex`: compatibility artifacts for the existing flow

Benchmark evaluation writes `results/benchmark_results.json` and
`results/benchmark_report.md`, including per-scenario metrics for clean,
jittered, dropped, accidental-pattern, sparse-noise, and dense-noise cases.
Activity figures are software operation proxies, not measurements of hardware
power or energy.

Generated benchmark artifacts under `data/generated/` and `results/` are
reproducible outputs and are not committed, except for `.gitkeep` placeholders.

The text-vector format is:

```text
# sample_index label sequence_length input_width
0 1 32 4 0000 0001 0010 0100 ...
```

Run the test suite with `make test` or `PYTHONPATH=python python -m pytest`.

## Experiment Sweeps

`configs/sweep_default.json` runs the benchmark across a deterministic grid of
noise, jitter, dropout, dense-noise threshold, and seed values. The sweep writes
`results/sweeps/sweep_results.json`, `results/sweeps/sweep_summary.csv`, and
`results/sweeps/sweep_report.md`, including best classifier by sweep point, best
classifier by scenario, decision-summary guidance, and `tiny_snn_v2` versus
`fsm` comparisons with F1 tolerance and software activity proxy context. Sweep
outputs are generated artifacts and are ignored by git.

## Tiny SNN v2 Parameter Search

`configs/snn_search_default.json` runs a bounded deterministic search over
small, RTL-plausible `tiny_snn_v2` settings. It evaluates predefined fixed
integer weight variants (`current_default`, `ternary_event_order`,
`ternary_noise_guard`, `low_activity_sparse`, and `balanced_small_int`) across
thresholds, leak values, reset behavior, seeds, and optional dataset
noise/jitter/dropout values. This is not training; it only evaluates
hand-defined low-precision configurations through the existing benchmark
pipeline. When `limits.max_candidates` is set, the default
`balanced_round_robin` selection strategy samples across weight variants,
dataset conditions, and seeds; `full_grid` and `prefix` strategies are also
available for exhaustive runs and debugging.

Run:

```bash
make snn-search
```

The command writes `results/snn_search/search_results.json`,
`results/snn_search/search_summary.csv`, and
`results/snn_search/search_report.md`. Competitive cases use the same strict
logic as sweep reports: an SNN candidate must either beat FSM F1 or have lower
software activity while staying within the configured F1 tolerance. Activity
figures remain software operation proxies, not hardware power or energy.

## Temporal-Hard Workflows

The temporal-hard scenario suite adds long-gap positives, distractors,
dropouts, reversed and partial-order negatives, burst noise, and near misses.
Use the ready-to-run commands:

```bash
make temporal-benchmark
make temporal-sweep
make temporal-snn-search
```

`temporal-benchmark` evaluates `configs/temporal_hard.json` once. The temporal
sweep uses `configs/sweep_temporal_hard.json` and writes under
`results/temporal_sweeps/`. The temporal SNN search uses
`configs/snn_search_temporal_hard.json` and writes under
`results/temporal_snn_search/`. These workflows use the harder scenario suite;
the existing `benchmark`, `sweep`, and `snn-search` commands retain the legacy
default dataset behavior.

## RTL Baseline Flow

The hardware flow covers the threshold, ordered-pattern FSM, and LUT-like
baselines under `rtl/baselines/`, plus a bounded fixed-weight
`tiny_snn_v2_detector` feasibility prototype under `rtl/snn/`. The SNN RTL is
not trainable, not runtime-programmable, and not a final silicon design; it is
only a small inference prototype for comparing against the simple references.

```bash
make rtl-vectors
make rtl-sim
make rtl-synth
make rtl-activity
make rtl-report
```

`rtl-vectors` generates `results/rtl/vectors.svh` from the temporal-hard config
and includes Python-golden predictions for `threshold`, `fsm`, `lut_like`, and
`tiny_snn_v2`. Simulation uses Icarus Verilog and synthesis uses Yosys when
those tools are installed. Missing tools print a clear skip message and return
success by default; set `STRICT=1` to make either script fail instead. All
outputs under `results/rtl/` are generated and ignored by Git. Simulation and
synthesis statistics are local open-source tool proxies, not silicon signoff or
hardware power measurements.

`rtl-sim` passes an optional `+VCD_FILE=...` plusarg to the shared RTL
testbench and writes one VCD trace per detector when simulation tools are
available: `vcd_threshold.vcd`, `vcd_fsm.vcd`, `vcd_lut_like.vcd`, and
`vcd_tiny_snn_v2.vcd`.
`rtl-activity` parses any available VCD files without extra dependencies and
writes `results/rtl/rtl_activity_summary.json` plus
`results/rtl/rtl_activity_report.md`. Missing VCDs are reported as missing, not
as failures. Toggle counts are simulation activity proxies only; they are not
measured silicon power or energy.

`rtl-report` writes `results/rtl/rtl_summary.json` and
`results/rtl/rtl_report.md`, including synthesis and simulation evidence and
the VCD toggle summary when `rtl_activity_summary.json` is present. The
consolidated `make research-report` also includes this RTL activity context
when available.

## Initial research stance

The SNN should only be considered interesting if it lands near the Pareto frontier of:

- accuracy
- false-positive rate
- false-negative rate
- synthesized area
- register count
- switching activity from VCD
- latency
- verification complexity

A negative result is still useful if it shows that simple logic is superior for this class of RFID sensor-tag tasks.
