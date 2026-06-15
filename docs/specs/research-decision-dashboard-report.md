# Feature Spec: Consolidated Research Decision Report

## 1. Goal

Add a single command that reads existing benchmark, sweep, and SNN-search outputs and produces a consolidated research decision report.

The repo now supports:

- legacy benchmark,
- legacy sweep,
- legacy SNN search,
- temporal-hard benchmark,
- temporal-hard sweep,
- temporal-hard SNN search.

The next problem is interpretation. The project needs one report that answers:

```text
Across both legacy and temporal-hard scenarios, is tiny_snn_v2 worth further optimization, or should FSM/LUT RTL baselines be prioritized?
```

This feature creates a lightweight Markdown and JSON report that summarizes the current evidence without rerunning experiments.

## 2. Non-goals

Do not implement:

- RTL.
- Training.
- New classifiers.
- New datasets.
- Heavy plotting.
- Pandas.
- Web dashboard.
- Hardware power claims.

This is a report aggregation feature over existing generated outputs.

## 3. Required command

Add Makefile target:

```makefile
research-report:
	python python/build_research_report.py
```

Add CLI wrapper:

```text
python/build_research_report.py
```

Add module:

```text
python/tinysnnrfid/build_research_report.py
```

Default command should read these paths if they exist:

```text
results/benchmark_results.json
results/sweeps/sweep_results.json
results/snn_search/search_results.json
results/temporal_sweeps/sweep_results.json
results/temporal_snn_search/search_results.json
```

It should tolerate missing files and clearly list missing inputs.

## 4. Outputs

Write:

```text
results/research_decision_report.md
results/research_decision_summary.json
```

These are generated outputs and must not be committed.

Update `make clean` to remove them.

## 5. Report contents

Markdown report sections:

```text
# Tiny SNN RFID Research Decision Report
## Inputs Found
## Executive Recommendation
## Legacy Benchmark Evidence
## Legacy Sweep Evidence
## Legacy SNN Search Evidence
## Temporal-Hard Sweep Evidence
## Temporal-Hard SNN Search Evidence
## Scenario-Level Findings
## Decision Matrix
## Notes and Limitations
```

The report must clearly state that software activity proxy is not hardware power.

## 6. Decision logic

Use stable recommendation enum:

```text
continue_snn_optimization
add_harder_temporal_scenarios
prioritize_fsm_or_lut_rtl_baseline
insufficient_data
```

Suggested rules:

1. If no sweep or search outputs are found, recommendation is `insufficient_data`.
2. If any SNN search report has `decision.recommendation == continue_snn_optimization`, recommendation is `continue_snn_optimization`.
3. Else if temporal-hard outputs are missing, recommendation is `add_harder_temporal_scenarios`.
4. Else if all available temporal-hard evidence favors FSM/LUT over SNN, recommendation is `prioritize_fsm_or_lut_rtl_baseline`.
5. Else recommendation is `add_harder_temporal_scenarios`.

Also include a human-readable reason.

## 7. JSON summary shape

Suggested output:

```json
{
  "inputs": {
    "legacy_benchmark": {"path": "results/benchmark_results.json", "found": true},
    "legacy_sweep": {"path": "results/sweeps/sweep_results.json", "found": true},
    "legacy_snn_search": {"path": "results/snn_search/search_results.json", "found": true},
    "temporal_sweep": {"path": "results/temporal_sweeps/sweep_results.json", "found": true},
    "temporal_snn_search": {"path": "results/temporal_snn_search/search_results.json", "found": true}
  },
  "recommendation": "prioritize_fsm_or_lut_rtl_baseline",
  "reason": "...",
  "highlights": [],
  "missing_inputs": []
}
```

## 8. Evidence extraction

For benchmark outputs, extract:

- classifier ranking by F1,
- best classifier,
- `tiny_snn_v2` metrics if present,
- `fsm` metrics if present,
- per-scenario summary if present.

For sweep outputs, extract:

- decision recommendation if present,
- comparison counts,
- competitive run count,
- best overall classifier if present,
- scenario winners if present.

For SNN search outputs, extract:

- decision recommendation,
- best candidate ID,
- best weight variant,
- competitive candidate count,
- F1 win count,
- activity-win-within-tolerance count,
- selection coverage summary if present.

## 9. CLI options

Support:

```text
--output-dir results
--strict
```

Default behavior: missing inputs are allowed.

If `--strict` is passed, exit nonzero when any expected input is missing.

## 10. Tests

Add tests for:

1. Missing inputs produce `insufficient_data` and list missing files.
2. A synthetic SNN-search result with `continue_snn_optimization` drives the final recommendation.
3. Temporal-hard missing but legacy results found recommends `add_harder_temporal_scenarios`.
4. FSM-dominant temporal evidence recommends `prioritize_fsm_or_lut_rtl_baseline`.
5. Markdown and JSON outputs are written.
6. `--strict` behavior returns nonzero or raises clear error on missing files.
7. Activity proxy warning appears in Markdown.

## 11. Manual workflow

Run:

```bash
make benchmark
make sweep
make snn-search
make temporal-benchmark
make temporal-sweep
make temporal-snn-search
make research-report
```

Then inspect:

```text
results/research_decision_report.md
results/research_decision_summary.json
```

## 12. Definition of done

This task is complete when:

- `make research-report` works.
- Markdown and JSON summary outputs are generated.
- Missing inputs are handled clearly.
- Report combines legacy and temporal-hard evidence.
- Stable recommendation enum is produced.
- Tests cover main recommendation branches.
- `make test` passes.
- Generated report outputs are ignored or cleaned and not committed.
