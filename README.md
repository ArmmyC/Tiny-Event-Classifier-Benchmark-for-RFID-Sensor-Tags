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
```

Or run directly:

```bash
python python/generate_dataset.py --num-sequences 1000 --seq-len 32 --noise-prob 0.03 --out-dir data/generated
python python/evaluate_python.py --dataset data/generated/noisy_event_dataset.npz --out results/accuracy/python_metrics.json
```

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
