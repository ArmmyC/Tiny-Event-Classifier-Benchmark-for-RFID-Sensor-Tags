# Codex Prompt: Harder Temporal Scenario Suite

You are working in the repository `Tiny-Event-Classifier-Benchmark-for-RFID-Sensor-Tags`.

Implement this spec:

```text
docs/specs/harder-temporal-scenario-suite.md
```

## Goal

Add a configurable `temporal_hard` dataset mode so the benchmark tests harder temporal event streams, not only the simple ordered motif.

The research question is:

```text
Does tiny_snn_v2 help on sparse temporal ambiguity, or do FSM/LUT baselines still dominate?
```

## Required work

1. Add `scenario_suite` config support.
2. Support modes:
   - `legacy`
   - `temporal_hard`
3. Keep default behavior backward compatible.
4. Add `configs/temporal_hard.json`.
5. Add scenario tags:
   - `clean_positive`
   - `long_gap_positive`
   - `distractor_positive`
   - `dropout_positive`
   - `reversed_negative`
   - `partial_order_negative`
   - `burst_noise_negative`
   - `near_miss_negative`
6. Generate labels and tags together so they stay consistent.
7. Include scenario counts in metadata.
8. Keep writing `scenario_tags.json`.
9. Ensure benchmark reports include new scenario tags through existing per-scenario metrics.
10. Add Makefile target `temporal-benchmark`.
11. Add tests for config validation, scenario generation, label/tag consistency, and benchmark flow.

## Constraints

- Do not implement RTL.
- Do not implement training.
- Do not add pandas or ML frameworks.
- Do not change classifier math unless required for compatibility.
- Do not commit generated outputs.
- Keep existing commands working: `make data`, `make benchmark`, `make sweep`, `make snn-search`, `make test`.

## Run

```bash
make test
make temporal-benchmark
```

Optionally run:

```bash
make sweep
make snn-search
```

## Final response

Summarize files changed, scenario tags added, label/tag rules, tests, command results, and limitations.
