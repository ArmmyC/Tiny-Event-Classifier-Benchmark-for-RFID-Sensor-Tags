# Feature Spec: Harder Temporal Scenario Suite

## 1. Goal

Expand the benchmark dataset beyond the current simple noisy ordered motif so the project can test whether `tiny_snn_v2` has any real advantage on temporal, sparse, ambiguous RFID-style event streams.

The current task is useful, but it is likely too friendly to an FSM. A valid sequence is mostly:

```text
channel 0 -> channel 1 -> channel 2
```

with noise, jitter, and dropout. That is exactly the kind of pattern a small FSM should solve well.

This feature adds harder temporal scenarios that stress:

- long gaps,
- repeated distractors,
- reversed or partially ordered motifs,
- burst noise,
- temporal ambiguity,
- sparse positives hidden inside longer streams,
- negatives that look locally valid but fail globally.

The goal is not to make SNN win artificially. The goal is to create a fairer benchmark that can answer:

```text
Does tiny_snn_v2 help on sparse temporal ambiguity, or do FSM/LUT baselines still dominate?
```

## 2. Non-goals

Do not implement:

- RTL.
- Training.
- New ML frameworks.
- PyTorch, TensorFlow, JAX, pandas, or heavyweight dependencies.
- Hardware power claims.
- A web dashboard.
- Dataset downloads.
- Random, untraceable scenario generation.

This is a deterministic synthetic dataset and reporting improvement.

## 3. Assumptions

- The repo already has dataset generation.
- The repo already has scenario tags.
- The repo already has benchmark, sweep, and SNN search flows.
- Generated outputs are ignored by git.
- Existing commands must keep working.
- All scenarios must be reproducible from config and seed.

## 4. User stories

- As a researcher, I want harder temporal cases, so that the benchmark is not just an FSM toy problem.
- As a benchmark user, I want each sample tagged by scenario, so that I can see which cases each classifier wins or loses.
- As a future RTL implementer, I want synthetic scenarios that map to small input vectors and short sequences, so that later RTL tests are realistic.
- As a project maintainer, I want scenario proportions controlled by config, so that experiments remain reproducible.
- As a reviewer, I want the report to explain the scenario suite, so that results are interpretable.

## 5. UX / CLI requirements

Existing commands must continue working:

```bash
make data
make benchmark
make sweep
make snn-search
make test
```

Add or update config so users can enable the harder suite without editing code.

Preferred config section:

```json
"scenario_suite": {
  "mode": "temporal_hard",
  "mix": {
    "clean_positive": 0.15,
    "long_gap_positive": 0.10,
    "distractor_positive": 0.10,
    "dropout_positive": 0.10,
    "reversed_negative": 0.15,
    "partial_order_negative": 0.15,
    "burst_noise_negative": 0.15,
    "near_miss_negative": 0.10
  },
  "max_long_gap": 10,
  "burst_length": 4,
  "distractor_count": 2,
  "allow_legacy_tags": true
}
```

Default behavior should remain backward compatible. If no `scenario_suite` is provided, existing dataset generation should behave as before.

## 6. Functional requirements

1. Add support for a configurable `scenario_suite` section.
2. Keep existing scenario behavior as the default or as `mode: legacy`.
3. Add a new mode: `temporal_hard`.
4. The `temporal_hard` mode must generate a controlled mix of positive and negative temporal scenarios.
5. Add scenario tags for at least:

```text
clean_positive
long_gap_positive
distractor_positive
dropout_positive
reversed_negative
partial_order_negative
burst_noise_negative
near_miss_negative
```

6. Existing scenario tags may remain supported.
7. Scenario counts must be included in metadata.
8. Scenario tags must be written to `scenario_tags.json`.
9. Benchmark reports must include the new scenario names automatically through existing per-scenario reporting.
10. Sweep and SNN search must work with the harder scenario suite.
11. Add `configs/temporal_hard.json` as a ready-to-run config.
12. Add a Makefile target:

```makefile
temporal-benchmark:
	python python/generate_dataset.py --config configs/temporal_hard.json
	python python/evaluate_python.py --config configs/temporal_hard.json
```

13. Optional: add `configs/snn_search_temporal_hard.json` if small enough to maintain.
14. The dataset generator must preserve binary labels.
15. The dataset generator must avoid label/tag mismatches.
16. Positive scenarios must contain the ordered valid motif according to the configured pattern, except dropout cases where the tag explicitly means the observed input is incomplete.
17. Negative scenarios must not contain a valid ordered motif unless they are explicitly tagged as near-miss or accidental-pattern style negatives and are documented clearly.
18. Add tests for each new scenario type.
19. Add tests that labels and tags are consistent.
20. Add tests that scenario mix counts approximately follow the configured mix for deterministic seeds.
21. Add tests that generated arrays keep shape `[samples, sequence_length, input_width]`.
22. Add tests that `make benchmark` equivalent flow works with temporal hard config.

## 7. Scenario definitions

### `clean_positive`

A positive sample containing the valid motif in the correct order with minimal noise.

### `long_gap_positive`

A positive sample where valid motif events occur in order but with longer gaps than the default easy case.

Purpose: tests temporal memory.

### `distractor_positive`

A positive sample with the valid ordered motif plus extra non-motif spikes before, between, or after motif events.

Purpose: tests whether classifiers can ignore irrelevant sparse events.

### `dropout_positive`

A positive intent sample where one motif event may be dropped or weakened according to existing dropout behavior.

Purpose: tests robustness and false negatives.

Important: document whether label remains positive by ground-truth intent or by observed complete motif. Keep it deterministic and consistent.

### `reversed_negative`

A negative sample containing motif channels in reverse order, such as:

```text
channel 2 -> channel 1 -> channel 0
```

Purpose: tests order sensitivity.

### `partial_order_negative`

A negative sample containing only part of the motif or a wrong order, such as:

```text
channel 0 -> channel 2
channel 1 -> channel 0
```

Purpose: tests near matches.

### `burst_noise_negative`

A negative sample with bursts of activity across one or more channels but no valid global motif.

Purpose: tests false positives under dense local activity.

### `near_miss_negative`

A negative sample that locally looks close to the motif but violates timing, order, or completion rules.

Purpose: tests ambiguity.

## 8. Technical requirements

Likely files to modify:

```text
python/tinysnnrfid/config.py
python/tinysnnrfid/dataset.py
python/tinysnnrfid/generate_dataset.py
configs/default.json
configs/temporal_hard.json
Makefile
README.md
tests/test_dataset.py
tests/test_benchmark_flow.py
```

Optional new tests:

```text
tests/test_temporal_hard_scenarios.py
```

Do not duplicate benchmark reporting if existing per-scenario report already handles new tags.

## 9. Config validation

Validate:

- `scenario_suite.mode` is one of:

```text
legacy
temporal_hard
```

- `scenario_suite.mix` is a non-empty object when mode is `temporal_hard`.
- All mix keys are known scenario names.
- Mix weights are non-negative numbers.
- Mix sum is greater than zero.
- `max_long_gap` is a non-negative integer.
- `burst_length` is a positive integer.
- `distractor_count` is a non-negative integer.
- `allow_legacy_tags` is boolean if present.

## 10. Data-generation approach

Use deterministic NumPy RNG seeded from the existing dataset seed.

Suggested flow:

1. Normalize scenario mix weights.
2. Assign each sample a scenario type deterministically from the RNG.
3. Generate sequence according to scenario type.
4. Assign label and tag together.
5. Apply optional noise/jitter/dropout only when scenario definition permits it.
6. Save inputs, labels, metadata, scenario tags, and compatibility artifacts.

Avoid post-hoc tag inference where possible. For hard scenarios, generate from the scenario tag directly so labels are controlled.

## 11. Output expectations

Existing generated files remain:

```text
data/generated/inputs.npy
data/generated/labels.npy
data/generated/metadata.json
data/generated/scenario_tags.json
data/generated/test_vectors.txt
```

Metadata must include:

```json
"scenario_suite": {
  "mode": "temporal_hard",
  "mix": {},
  "effective_counts": {}
}
```

or equivalent.

## 12. Tests

Required tests:

1. `legacy` mode still works.
2. `temporal_hard` mode generates all configured scenario tags when sample count is sufficient.
3. `reversed_negative` labels are zero.
4. `partial_order_negative` labels are zero.
5. `burst_noise_negative` labels are zero.
6. Positive scenario labels are one, according to documented rules.
7. Shapes are correct.
8. Scenario counts are present in metadata.
9. Scenario tags length equals number of samples.
10. Benchmark flow works with `configs/temporal_hard.json`.
11. Invalid mix key is rejected.
12. Invalid mix weights are rejected.
13. Invalid mode is rejected.

## 13. Manual checks

Run:

```bash
make test
make temporal-benchmark
```

Optional:

```bash
PYTHONPATH=python python -m tinysnnrfid.run_snn_search --config configs/snn_search_temporal_hard.json
```

Inspect:

```text
results/benchmark_report.md
```

Confirm the report includes the new scenario tags and activity warnings still avoid hardware power claims.

## 14. Definition of done

This task is complete when:

- `temporal_hard` scenario suite is implemented.
- `configs/temporal_hard.json` exists.
- New scenario tags appear in metadata and reports.
- Labels and scenario tags are deterministic and tested.
- Existing default benchmark still works.
- Sweep and SNN search are not broken.
- `make test` passes.
- `make temporal-benchmark` works.
- No generated outputs are committed.
