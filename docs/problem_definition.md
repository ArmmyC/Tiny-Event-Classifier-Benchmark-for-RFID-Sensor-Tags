# Problem Definition

## Research question

Can tiny event-driven SNN-style RTL be useful for RFID sensor-tag decision logic under strict area and switching constraints?

The study compares the SNN against simpler digital logic. The SNN is not assumed to win.

## Target task

The first target is a noisy event detector.

Input:

- 4-bit event vector per cycle
- sparse valid temporal motif
- random noise spikes

Output:

- `0`: ignore
- `1`: valid event detected

Default valid motif:

```text
sensor/event channel 0 fires
then channel 1 fires
then channel 2 fires
```

## Why this task

This task is intentionally small, but it includes three properties where SNNs might plausibly help:

1. sparse events
2. short temporal memory
3. noisy inputs

If the SNN cannot show any advantage on this kind of task, it is unlikely to be worth implementing inside RFID-style tag logic.

## Architectures to compare

1. threshold logic
2. FSM with debounce or motif tracking
3. LUT or decision-tree-style classifier
4. tiny SNN classifier

## Early metrics

Functional metrics:

- accuracy
- precision
- recall
- F1
- false-positive rate
- false-negative rate

Hardware metrics:

- synthesized cell count
- estimated area
- register count
- combinational cell count
- critical path estimate
- latency in cycles

Power proxy metrics:

- RTL toggle count from VCD
- gate-level toggle count if available
- toggles per sequence
- idle toggles
- toggles under different sparsity levels

## Scope boundary

This repository does not try to build a full RFID tag chip or a production neuromorphic RFID processor. It is a feasibility benchmark.
