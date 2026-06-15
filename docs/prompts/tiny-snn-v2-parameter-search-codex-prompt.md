# Codex Prompt: Tiny SNN v2 Parameter and Precision Search

You are working in the repository `Tiny-Event-Classifier-Benchmark-for-RFID-Sensor-Tags`.

Implement the feature spec at:

```text
docs/specs/tiny-snn-v2-parameter-search.md
```

## Goal

Use the completed sweep infrastructure to search small, RTL-plausible `tiny_snn_v2` configurations.

The goal is to answer:

```text
Can tiny_snn_v2 become competitive with FSM under any small integer parameter or weight-precision setting?
```

This is not training. It is deterministic evaluation of small hand-defined or generated low-precision SNN configurations.

## Required work

1. Add `configs/snn_search_default.json`.
2. Add `python/tinysnnrfid/run_snn_search.py`.
3. Add wrapper `python/run_snn_search.py` if useful.
4. Add `make snn-search`.
5. Evaluate multiple `tiny_snn_v2` configurations using the existing benchmark pipeline.
6. Compare each SNN candidate against `fsm` using strict competitive-case logic:

```text
competitive if candidate F1 > reference F1
or candidate activity < reference activity and candidate F1 >= reference F1 - f1_tolerance
```

7. Add predefined weight variants:

```text
current_default
ternary_event_order
ternary_noise_guard
low_activity_sparse
balanced_small_int
```

8. At least one variant must be ternary-only: `-1`, `0`, `+1`.
9. At least one variant must use small signed integer weights limited to `[-2, 2]`.
10. Search thresholds, leak, reset behavior, seeds, and optional dataset noise/jitter/dropout values.
11. Generate outputs:

```text
results/snn_search/search_results.json
results/snn_search/search_summary.csv
results/snn_search/search_report.md
```

12. Add tests in `tests/test_snn_search.py`.
13. Update README.
14. Update Makefile clean target for search outputs.

## Output requirements

`search_summary.csv` must include at least:

```text
candidate_id
seed
weight_variant
hidden_threshold
output_threshold
leak
reset_on_spike
noise_probability
jitter_probability
dropout_probability
candidate_f1
reference_f1
f1_delta
candidate_accuracy
reference_accuracy
candidate_activity
reference_activity
activity_delta
competitive_reason
recommendation
```

`search_report.md` must include:

```text
# Tiny SNN v2 Parameter Search Report
## Search Setup
## Top Candidates By F1
## Lower-Activity Competitive Candidates
## Best Candidate By Scenario
## Weight Variant Summary
## Decision Summary
## Notes and Limitations
```

## Constraints

- Do not implement RTL.
- Do not implement training.
- Do not add pandas, PyTorch, TensorFlow, JAX, or heavyweight dependencies.
- Do not use random search unless deterministic seeds make it fully reproducible.
- Do not use floating-point inference.
- Do not make hardware power claims.
- Keep activity proxy clearly labeled as software proxy, not hardware power.
- Do not commit generated outputs.
- Keep existing commands working:

```bash
make test
make benchmark
make sweep
```

## Tests to run

Run:

```bash
make test
make snn-search
```

Optionally run:

```bash
make sweep
```

## Definition of done

The task is complete only when:

- `make snn-search` works.
- `configs/snn_search_default.json` exists.
- Search outputs JSON, CSV, and Markdown.
- Multiple weight variants are evaluated.
- At least one ternary variant is included.
- Strict competitive-case semantics are used.
- Tests cover config loading, candidate grid expansion, weight variants, output generation, and decision behavior.
- No generated outputs are committed.

## Final response format

After implementation, summarize:

1. Files changed.
2. Weight variants added.
3. Search dimensions.
4. Output files generated.
5. Tests added or updated.
6. Results of `make test` and `make snn-search`.
7. Any tradeoffs or limitations.
