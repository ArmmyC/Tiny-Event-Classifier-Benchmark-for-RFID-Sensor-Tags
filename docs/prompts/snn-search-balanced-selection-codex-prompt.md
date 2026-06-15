# Codex Prompt: SNN Search Balanced Candidate Selection

You are working in the repository `Tiny-Event-Classifier-Benchmark-for-RFID-Sensor-Tags`.

Implement the feature spec at:

```text
docs/specs/snn-search-balanced-selection.md
```

## Goal

Fix candidate selection in the `tiny_snn_v2` parameter search so bounded searches remain scientifically fair.

Right now the search builds a large Cartesian product and applies `limits.max_candidates` by taking the first N candidates. That is deterministic, but biased toward early dataset and parameter combinations.

The goal is:

```text
When max_candidates is used, selected candidates should cover weight variants, dataset conditions, and seeds as evenly as practical.
```

## Required behavior

1. Keep full-grid search possible.
2. Keep prefix truncation available for debugging.
3. Make balanced deterministic selection the default bounded-search behavior.
4. Add config field:

```json
"selection": {
  "strategy": "balanced_round_robin"
}
```

5. Supported strategies:

```text
full_grid
prefix
balanced_round_robin
```

6. `full_grid` evaluates all candidates.
7. `prefix` preserves the current first-N behavior.
8. `balanced_round_robin` cycles across candidate groups until `max_candidates` is reached.
9. Candidate groups must include at least:

```text
weight_variant
dataset noise probability
dataset jitter probability
dataset dropout probability
seed
```

10. Candidate IDs must remain stable and be assigned after selection.

## Required output metadata

Add selection metadata to `search_results.json`:

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

Add a report section:

```text
## Candidate Selection Coverage
```

It should show:

- strategy,
- full grid size,
- evaluated candidate count,
- skipped candidate count,
- count per weight variant,
- count per seed,
- compact count per dataset condition.

## Suggested implementation

Refactor candidate generation into:

```python
def expand_full_candidate_grid(config: dict[str, Any]) -> list[dict[str, Any]]:
    ...

def select_candidates(candidates: list[dict[str, Any]], config: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    ...
```

Keep `expand_candidate_grid` working by making it call the new helpers.

Balanced round-robin algorithm:

1. Build groups by `(weight_variant, noise, jitter, dropout, seed)`.
2. Sort group keys for deterministic order.
3. Keep candidates within each group in deterministic original order.
4. Cycle through groups, taking one candidate from each non-empty group.
5. Stop when `max_candidates` is reached or all candidates are selected.
6. Assign `candidate_id` after selection.

## Tests

Update `tests/test_snn_search.py` to cover:

1. Full grid count is larger than selected count for limited config.
2. `prefix` strategy preserves first-N behavior.
3. `balanced_round_robin` includes every configured weight variant when possible.
4. `balanced_round_robin` includes multiple dataset conditions when possible.
5. Candidate IDs are stable and assigned after selection.
6. Selection metadata includes full/evaluated/skipped counts.
7. Search JSON includes `selection` metadata.
8. Search report includes `Candidate Selection Coverage`.
9. Invalid selection strategy is rejected.
10. Existing search output tests still pass.

## Constraints

- Do not implement RTL.
- Do not implement training.
- Do not add pandas or heavyweight dependencies.
- Do not change classifier math.
- Do not make hardware power claims.
- Keep activity proxy clearly labeled as software proxy, not hardware power.
- Do not commit generated outputs.
- Keep existing commands working:

```bash
make test
make snn-search
make sweep
make benchmark
```

## Run

```bash
make test
make snn-search
```

## Final response format

After implementation, summarize:

1. Files changed.
2. Candidate selection strategies added.
3. Selection metadata behavior.
4. Report coverage behavior.
5. Tests added or updated.
6. Results of `make test` and `make snn-search`.
7. Any tradeoffs or limitations.
