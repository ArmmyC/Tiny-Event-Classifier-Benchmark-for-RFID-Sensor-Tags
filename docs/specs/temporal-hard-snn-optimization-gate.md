# Feature Spec: Temporal-Hard SNN Optimization Gate

## Goal

Add a focused software-side SNN optimization workflow that tries to improve `tiny_snn_v2` on temporal-hard scenarios while preventing premature RTL investment.

The current generated evidence says:

- overall recommendation: `continue_snn_optimization`,
- legacy SNN search found competitive candidates,
- temporal-hard SNN search found zero competitive candidates,
- RTL comparison is missing useful local-tool data.

Therefore the next research branch should improve `tiny_snn_v2` only at the software/search level and gate future RTL work on temporal-hard competitiveness.

## Research question

Can small fixed-weight `tiny_snn_v2` variants become competitive against FSM/LUT-like baselines on temporal-hard event streams?

## Non-goals

Do not add:

- new RTL,
- training,
- heavyweight ML dependencies,
- runtime-programmable weights,
- silicon power or silicon area claims.

## Required command

Add:

```text
configs/snn_search_temporal_hard_optimized.json
make temporal-snn-optimize
```

The command should run a larger but still bounded temporal-hard SNN search using the existing `run_snn_search.py` flow.

Suggested target:

```makefile
temporal-snn-optimize:
	python python/run_snn_search.py --config configs/snn_search_temporal_hard_optimized.json
```

## Search scope

The optimized config should focus on temporal-hard cases and include more candidate diversity than `configs/snn_search_temporal_hard.json`.

Include:

- multiple seeds,
- balanced candidate selection,
- temporal-hard base config,
- output directory `results/temporal_snn_optimized/`,
- dataset output root `results/temporal_snn_optimized/generated/`,
- strict FSM reference comparison,
- `comparison.f1_tolerance`,
- existing weight variants,
- at least two new hand-defined weight variants designed for temporal-hard ambiguity.

New variants should remain fixed small integers. At least one new variant should be ternary-only `-1, 0, +1`; another may use small signed integers limited to `[-2, 2]`.

## Classifier/search changes

If needed, update the existing SNN search variant registry to support the new variants.

Do not change `tiny_snn_v2` default behavior.

Do not replace existing variants.

Possible variant names:

```text
temporal_gap_guard
reversal_inhibitory_guard
```

## Gate report

Add a small report builder or extend search reporting so the optimized temporal search clearly states whether future RTL work is justified.

Write:

```text
results/temporal_snn_optimized/optimization_gate.json
results/temporal_snn_optimized/optimization_gate.md
```

Gate recommendation enum:

```text
continue_to_snn_rtl_candidate
continue_software_snn_search
prioritize_fsm_or_lut_baseline
insufficient_data
```

Suggested logic:

- `continue_to_snn_rtl_candidate` if at least one temporal-hard candidate beats FSM F1 or has lower software activity within F1 tolerance.
- `continue_software_snn_search` if candidates improve versus previous temporal-hard SNN search but are still not competitive against FSM.
- `prioritize_fsm_or_lut_baseline` if no temporal-hard improvement or competitiveness is found.
- `insufficient_data` if required search outputs are missing.

The report must state that software activity is a proxy, not hardware power.

## Makefile integration

Add `temporal-snn-optimize` to `.PHONY`.

Do not add it to `make evidence` yet. This should be an explicit research branch command, not part of the default full evidence pipeline.

Update `clean` to remove:

```text
results/temporal_snn_optimized/search_results.json
results/temporal_snn_optimized/search_summary.csv
results/temporal_snn_optimized/search_report.md
results/temporal_snn_optimized/optimization_gate.json
results/temporal_snn_optimized/optimization_gate.md
results/temporal_snn_optimized/generated/
results/temporal_snn_optimized/runs/
```

## README updates

Document:

```text
make temporal-snn-optimize
```

Explain that this command is for deciding whether SNN deserves more work after the initial evidence pipeline.

## Tests

Add tests that do not run the full optimized search:

1. Optimized temporal config loads successfully.
2. Optimized config uses temporal-hard base config.
3. Optimized config writes under `results/temporal_snn_optimized/`.
4. New weight variants are available in the SNN search registry.
5. At least one new variant is ternary-only.
6. At least one new variant uses weights limited to `[-2, 2]`.
7. Gate logic returns `continue_to_snn_rtl_candidate` for competitive candidate input.
8. Gate logic returns `continue_software_snn_search` for improvement without competitiveness.
9. Gate logic returns `prioritize_fsm_or_lut_baseline` when no improvement or competitiveness exists.
10. Gate Markdown contains the proxy limitation text.
11. Makefile contains `temporal-snn-optimize` and does not add it to `evidence`.
12. Clean removes optimized temporal output paths.

## Constraints

- Do not add RTL.
- Do not add training.
- Do not add heavy dependencies.
- Do not make hardware power claims.
- Do not commit generated outputs.
- Keep existing benchmark, evidence, smoke, and writeup flows working.

## Manual workflow

Run:

```bash
python -m pytest
make temporal-snn-optimize
```

Then inspect:

```text
results/temporal_snn_optimized/optimization_gate.md
results/temporal_snn_optimized/search_report.md
```

## Definition of done

- `make temporal-snn-optimize` exists.
- Optimized temporal-hard SNN search config exists.
- New fixed-weight variants are available.
- Optimization gate JSON and Markdown are generated.
- Tests cover config, variants, gate logic, Makefile integration, and cleanup.
- No generated outputs are committed.
