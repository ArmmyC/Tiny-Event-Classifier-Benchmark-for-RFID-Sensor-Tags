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
```

Or run directly:

```bash
PYTHONPATH=python python -m tinysnnrfid.generate_dataset --config configs/default.json
PYTHONPATH=python python -m tinysnnrfid.run_benchmark --config configs/default.json
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

The text-vector format is:

```text
# sample_index label sequence_length input_width
0 1 32 4 0000 0001 0010 0100 ...
```

Run the test suite with `make test` or `PYTHONPATH=python python -m pytest`.

## Optional RTL flow

The RTL files are starter implementations. They are meant to be refined after the Python benchmark is stable.

```bash
bash scripts/run_iverilog.sh
bash scripts/run_yosys.sh threshold_detector
```

Tool availability depends on your machine.

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
