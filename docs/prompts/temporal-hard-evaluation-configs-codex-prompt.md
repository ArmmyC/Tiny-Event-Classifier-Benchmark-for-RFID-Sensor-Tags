# Codex Prompt: Temporal-Hard Evaluation Configs

You are working in the repository `Tiny-Event-Classifier-Benchmark-for-RFID-Sensor-Tags`.

Implement this spec:

```text
docs/specs/temporal-hard-evaluation-configs.md
```

## Goal

Add ready-to-run temporal-hard sweep and SNN-search configs so the harder scenario suite is used by normal research workflows.

## Required work

1. Add `configs/sweep_temporal_hard.json`.
2. Add `configs/snn_search_temporal_hard.json`.
3. Add Makefile targets:
   - `temporal-sweep`
   - `temporal-snn-search`
4. Keep `make temporal-benchmark` working.
5. Send temporal sweep outputs to `results/temporal_sweeps/`.
6. Send temporal SNN-search outputs to `results/temporal_snn_search/`.
7. Update `make clean` for these generated outputs.
8. Update README with the temporal benchmark/sweep/search commands.
9. Add tests that load the new configs.
10. Add tiny integration tests for temporal sweep and temporal SNN search using temporary small configs.

## Constraints

- Do not implement RTL.
- Do not implement training.
- Do not add pandas or ML frameworks.
- Do not create new scenario tags in this task.
- Do not change classifier math.
- Do not commit generated outputs.
- Keep existing commands working: `make test`, `make benchmark`, `make sweep`, `make snn-search`, `make temporal-benchmark`.

## Run

```bash
make test
make temporal-benchmark
make temporal-sweep
make temporal-snn-search
```

## Final response

Summarize files changed, configs added, Makefile targets, tests, command results, and limitations.
