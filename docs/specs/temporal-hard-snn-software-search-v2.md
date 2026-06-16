# Feature Spec: Temporal-Hard SNN Software Search v2

## Goal

Continue SNN work at the software-search level only, based on the optimization gate result:

```text
continue_software_snn_search
```

The previous optimized temporal-hard search improved best F1 only slightly, from about `0.6167` to `0.6207`, and found:

```text
F1 wins: 0
activity wins within F1 tolerance: 0
competitive candidates: 0
best variant: current_default
```

This means future SNN RTL is not justified yet. The next branch should focus on better temporal-hard software evidence.

## Research question

Can a fixed-weight `tiny_snn_v2` variant near the current default improve temporal-hard F1 enough to become competitive with the FSM reference?

## Non-goals

Do not add:

- RTL,
- training,
- learned weights,
- heavyweight dependencies,
- hardware power or silicon area claims.

## Required command

Add:

```text
configs/snn_search_temporal_hard_v2.json
make temporal-snn-v2-search
```

Suggested Makefile target:

```makefile
temporal-snn-v2-search:
	python python/run_snn_search.py --config configs/snn_search_temporal_hard_v2.json
	python python/build_temporal_snn_optimization_gate.py --search-results results/temporal_snn_v2_search/search_results.json --previous-search-results results/temporal_snn_optimized/search_results.json --output-dir results/temporal_snn_v2_search
```

Do not add this to `make evidence`.

## Search direction

Since `current_default` remains the best temporal-hard variant, v2 should search near `current_default`, not mainly around unrelated variants.

Add several new fixed-weight variants derived from `current_default`. Suggested names:

```text
current_default_gap_tuned
current_default_output_rebalanced
current_default_noise_inhibited
current_default_sparse_activity
```

These should remain hand-defined, deterministic, fixed integer variants.

At least two variants should preserve the same hidden neuron count as `current_default`.

At least one variant should reduce software activity proxy intent by using sparser or lower-magnitude output weights.

At least one variant should target temporal-hard negatives such as reversed order, partial order, or burst noise.

Do not change `tiny_snn_v2` default behavior.

Do not remove existing variants.

## Config requirements

The new config should:

- use `configs/temporal_hard.json` as base config,
- write to `results/temporal_snn_v2_search/`,
- use `results/temporal_snn_v2_search/generated/` as dataset output root,
- use multiple seeds,
- use balanced candidate selection,
- use FSM as the reference classifier,
- use `tiny_snn_v2` as the candidate classifier,
- include `comparison.f1_tolerance`,
- focus weight variants on `current_default` plus the new current-default-derived variants,
- use a bounded candidate count larger than the previous optimized search if practical.

## Gate behavior

Reuse `build_temporal_snn_optimization_gate.py` for the v2 gate.

The v2 gate should compare against:

```text
results/temporal_snn_optimized/search_results.json
```

and write:

```text
results/temporal_snn_v2_search/optimization_gate.json
results/temporal_snn_v2_search/optimization_gate.md
```

The existing gate recommendation enum remains:

```text
continue_to_snn_rtl_candidate
continue_software_snn_search
prioritize_fsm_or_lut_baseline
insufficient_data
```

## Optional but useful report improvement

If simple to implement, include the previous and current best candidate IDs and variants in the gate JSON/Markdown.

For example:

```json
{
  "optimized": {
    "best_candidate_id": "candidate_...",
    "best_weight_variant": "current_default_gap_tuned"
  },
  "previous": {
    "best_candidate_id": "candidate_...",
    "best_weight_variant": "current_default"
  }
}
```

This should not require rerunning experiments inside the gate builder; use fields already present in search outputs.

## Makefile integration

Add `temporal-snn-v2-search` to `.PHONY`.

Do not add it to `evidence`.

Update `clean` to remove:

```text
results/temporal_snn_v2_search/search_results.json
results/temporal_snn_v2_search/search_summary.csv
results/temporal_snn_v2_search/search_report.md
results/temporal_snn_v2_search/optimization_gate.json
results/temporal_snn_v2_search/optimization_gate.md
results/temporal_snn_v2_search/generated/
results/temporal_snn_v2_search/runs/
```

## README updates

Document:

```text
make temporal-snn-v2-search
```

Explain that this is a second software-only temporal-hard search branch. It should be run only after `make temporal-snn-optimize` or after full evidence plus optimized search outputs exist.

## Tests

Add tests that do not run the full v2 search:

1. v2 config loads successfully.
2. v2 config uses temporal-hard base config.
3. v2 config writes under `results/temporal_snn_v2_search/`.
4. New current-default-derived variants exist in the SNN search registry.
5. New variants do not change `current_default`.
6. At least two new variants preserve current_default hidden neuron count.
7. At least one new variant has lower output-weight absolute sum than current_default.
8. Gate builder can include best candidate ID and best weight variant when available, if implemented.
9. Makefile includes `temporal-snn-v2-search` and does not add it to `evidence`.
10. Clean removes v2 output paths.

## Constraints

- Do not add RTL.
- Do not add training.
- Do not add heavy dependencies.
- Do not make hardware power claims.
- Do not commit generated outputs.
- Keep existing evidence, smoke, optimized search, and writeup flows working.

## Manual workflow

Run:

```bash
python -m pytest
make temporal-snn-optimize
make temporal-snn-v2-search
```

Then inspect:

```text
results/temporal_snn_v2_search/optimization_gate.md
results/temporal_snn_v2_search/search_report.md
results/temporal_snn_v2_search/search_summary.csv
```

## Definition of done

- `make temporal-snn-v2-search` exists.
- v2 temporal-hard SNN search config exists.
- New current-default-derived fixed-weight variants are available.
- v2 gate outputs are generated.
- Tests cover config, variants, gate behavior if changed, Makefile integration, and cleanup.
- No generated outputs are committed.
