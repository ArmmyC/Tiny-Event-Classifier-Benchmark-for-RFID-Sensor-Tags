# Feature Spec: SNN Search Balanced Candidate Selection

## 1. Goal

Fix candidate selection in the `tiny_snn_v2` parameter search so bounded searches remain scientifically fair.

The current SNN search expands a large Cartesian product, then applies `limits.max_candidates` by taking the first N candidates. This is deterministic, but it can bias the search toward the earliest dataset conditions and parameter combinations. For example, the default search has many combinations but limits evaluation to 60 candidates, so it may not fairly cover all noise, jitter, dropout, seed, and weight-variant cases.

The goal is:

```text
When max_candidates is used, selected candidates should cover weight variants, dataset conditions, and SNN parameter regions as evenly as practical.
```

This makes search results more trustworthy before deciding whether to continue SNN optimization, add harder scenarios, or prioritize FSM/LUT RTL baselines.

## 2. Non-goals

Do not implement:

- RTL.
- Training.
- Random search.
- Bayesian optimization.
- New classifiers.
- New weight-learning logic.
- Heavy dependencies.
- Pandas.
- Plotting.

This is a deterministic candidate-selection and reporting patch.

## 3. Current problem

The search config contains a `limits.max_candidates` field.

The current implementation builds the full candidate grid in nested loop order and then truncates:

```text
candidates = candidates[:max_candidates]
```

This can overrepresent early grid values and underrepresent later values.

Examples of possible bias:

- only early noise/jitter/dropout conditions are evaluated,
- some weight variants appear more often than others,
- one seed dominates,
- reset/leak/threshold combinations near the start of the nested loop dominate,
- search conclusions may be based on incomplete coverage.

## 4. Functional requirements

1. Preserve deterministic behavior.
2. Keep full-grid execution possible when `limits.max_candidates` is omitted.
3. Add a candidate-selection strategy when `limits.max_candidates` is provided.
4. Default strategy should be balanced, not simple prefix truncation.
5. Add config field:

```json
"selection": {
  "strategy": "balanced_round_robin"
}
```

6. Supported strategies:

```text
full_grid
prefix
balanced_round_robin
```

7. `full_grid` ignores `limits.max_candidates` and evaluates all candidates.
8. `prefix` preserves the old behavior for debugging.
9. `balanced_round_robin` should select candidates across groups to improve coverage.
10. Group candidates at least by:

```text
weight_variant
dataset condition tuple
seed
```

11. Dataset condition tuple should include:

```text
dataset.noise_probability
dataset.jitter_probability
dataset.dropout_probability
```

12. If a parameter is missing, use `None` or the effective default value consistently.
13. `balanced_round_robin` should cycle through groups and pick one candidate from each group until the limit is reached.
14. Candidate IDs must remain stable and assigned after selection.
15. Add metadata to search results:

```json
"selection": {
  "strategy": "balanced_round_robin",
  "full_grid_candidate_count": 2880,
  "evaluated_candidate_count": 60,
  "skipped_candidate_count": 2820,
  "coverage": {
    "weight_variants": {},
    "dataset_conditions": {},
    "seeds": {}
  }
}
```

16. Add coverage information to `search_report.md`.
17. Add coverage information to `search_results.json`.
18. Add coverage columns to `search_summary.csv` only if useful; not required.
19. Update README to mention balanced selection.
20. Existing commands must keep working:

```bash
make test
make snn-search
make sweep
make benchmark
```

21. Do not commit generated search outputs.

## 5. Suggested implementation

Refactor candidate generation into two steps:

```python
def expand_full_candidate_grid(config: dict[str, Any]) -> list[dict[str, Any]]:
    ...

def select_candidates(candidates: list[dict[str, Any]], config: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    ...
```

Keep the existing public `expand_candidate_grid` function if tests or callers use it, but update it to call the new functions.

Suggested group key:

```python
def candidate_group_key(candidate: dict[str, Any]) -> tuple[Any, ...]:
    dataset = candidate["dataset_parameters"]
    return (
        candidate["weight_variant"],
        dataset.get("dataset.noise_probability"),
        dataset.get("dataset.jitter_probability"),
        dataset.get("dataset.dropout_probability"),
        candidate["seed"],
    )
```

Balanced round-robin algorithm:

1. Build groups by key.
2. Sort group keys for deterministic order.
3. Within each group, keep candidates in deterministic original order.
4. Repeatedly cycle group keys, taking one candidate from each non-empty group.
5. Stop when `max_candidates` candidates have been selected or all candidates are selected.
6. Assign `candidate_id` after selection.

## 6. Config validation

Validate:

- `selection` is optional.
- `selection.strategy` defaults to `balanced_round_robin` when absent.
- strategy must be one of:

```text
full_grid
prefix
balanced_round_robin
```

- `limits.max_candidates` must still be a positive integer when provided.
- If strategy is `full_grid`, ignore `limits.max_candidates` and report that full grid was used.

## 7. Report requirements

Add a section to `search_report.md`:

```text
## Candidate Selection Coverage
```

Include:

- strategy,
- full grid size,
- evaluated candidate count,
- skipped candidate count,
- count per weight variant,
- count per seed,
- compact count per dataset condition.

Explain that bounded searches are summaries, not exhaustive proof.

## 8. Tests

Add or update `tests/test_snn_search.py`.

Required tests:

1. Full grid count is larger than selected count for a limited config.
2. `prefix` strategy preserves old first-N behavior.
3. `balanced_round_robin` includes every configured weight variant when `max_candidates` is at least the number of variants.
4. `balanced_round_robin` includes multiple dataset conditions when possible.
5. Candidate IDs are stable and assigned after selection.
6. Selection metadata includes full/evaluated/skipped counts.
7. Search JSON includes `selection` metadata.
8. Search report includes `Candidate Selection Coverage`.
9. Invalid selection strategy is rejected.
10. Existing search output tests still pass.

## 9. Manual checks

Run:

```bash
make test
make snn-search
```

Inspect:

```text
results/snn_search/search_results.json
results/snn_search/search_report.md
```

Confirm:

- selection metadata is present,
- evaluated candidate count equals the configured max candidate limit for bounded search,
- all configured weight variants appear in the selected set when possible,
- report still warns activity proxy is not hardware power.

## 10. Definition of done

This task is complete when:

- Candidate selection is deterministic and balanced by default.
- Prefix behavior remains available for debugging.
- Full-grid behavior remains available.
- Search outputs include selection metadata.
- Search report includes candidate selection coverage.
- Tests cover selection behavior.
- `make test` passes.
- `make snn-search` works.
- No generated outputs are committed.
