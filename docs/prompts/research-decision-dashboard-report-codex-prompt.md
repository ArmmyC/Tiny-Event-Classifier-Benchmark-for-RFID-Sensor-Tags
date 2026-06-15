# Codex Prompt: Consolidated Research Decision Report

You are working in the repository `Tiny-Event-Classifier-Benchmark-for-RFID-Sensor-Tags`.

Implement this spec:

```text
docs/specs/research-decision-dashboard-report.md
```

## Goal

Add one command that reads existing benchmark, sweep, and SNN-search outputs and produces a consolidated research decision report.

The report should answer:

```text
Across both legacy and temporal-hard scenarios, is tiny_snn_v2 worth further optimization, or should FSM/LUT RTL baselines be prioritized?
```

## Required work

1. Add module `python/tinysnnrfid/build_research_report.py`.
2. Add wrapper `python/build_research_report.py`.
3. Add Makefile target `research-report`.
4. Read these generated outputs when present:
   - `results/benchmark_results.json`
   - `results/sweeps/sweep_results.json`
   - `results/snn_search/search_results.json`
   - `results/temporal_sweeps/sweep_results.json`
   - `results/temporal_snn_search/search_results.json`
5. Tolerate missing files by default and list missing inputs.
6. Add `--strict` mode that fails when expected inputs are missing.
7. Write:
   - `results/research_decision_report.md`
   - `results/research_decision_summary.json`
8. Update Makefile clean target for these generated outputs.
9. Add tests for recommendation logic, missing inputs, strict mode, and output creation.

## Recommendation enum

Use one of:

```text
continue_snn_optimization
add_harder_temporal_scenarios
prioritize_fsm_or_lut_rtl_baseline
insufficient_data
```

## Constraints

- Do not implement RTL.
- Do not implement training.
- Do not add pandas or heavy dependencies.
- Do not rerun experiments inside this command.
- Do not make hardware power claims.
- Keep activity proxy clearly labeled as software proxy, not hardware power.
- Do not commit generated outputs.

## Run

```bash
make test
make research-report
```

Optionally run the full workflow first:

```bash
make benchmark
make sweep
make snn-search
make temporal-benchmark
make temporal-sweep
make temporal-snn-search
make research-report
```

## Final response

Summarize files changed, inputs consumed, outputs generated, recommendation logic, tests, command results, and limitations.
