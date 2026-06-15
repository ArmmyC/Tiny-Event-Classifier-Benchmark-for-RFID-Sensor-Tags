# Feature Spec: Tiny SNN v2 Parameter and Precision Search

## 1. Goal

Use the completed sweep infrastructure to search small, RTL-plausible `tiny_snn_v2` configurations.

The project now has:

- baseline classifiers,
- scenario-tagged metrics,
- `tiny_snn_v2`,
- sweep outputs,
- CSV summaries,
- stricter decision logic.

The next research question is:

```text
Can tiny_snn_v2 become competitive with FSM under any small integer parameter or weight-precision setting?
```

This feature adds a lightweight, deterministic search over `tiny_snn_v2` thresholds, leak, reset behavior, and predefined weight variants. It does not train the model. It only evaluates hand-defined or generated low-precision candidate configurations using the existing benchmark and sweep runner.

## 2. Non-goals

Do not implement:

- RTL.
- Backpropagation.
- Surrogate-gradient training.
- PyTorch, TensorFlow, JAX, pandas, or other heavyweight dependencies.
- Random search without deterministic seeds.
- A large neural architecture.
- Floating-point inference.
- Hardware power claims.
- A web dashboard.

This is a small deterministic configuration search for research evidence.

## 3. Assumptions

- `tiny_snn_v2` already exists.
- `run_sweep.py` already writes JSON, CSV, and Markdown outputs.
- Sweep comparison already has strict competitive-case semantics.
- Generated outputs are ignored by git.
- Existing commands must keep working.
- The search should reuse the existing sweep framework where practical.

## 4. User stories

- As a researcher, I want to test multiple small SNN configurations, so that I can see whether the current weak result is due to architecture or poor hand-tuned parameters.
- As a future RTL implementer, I want to compare integer precision variants, so that I know whether ternary or small signed weights are worth implementing.
- As a project maintainer, I want the search results to use the existing sweep report and decision logic, so that the project does not grow duplicated experiment code.
- As a reviewer, I want to see whether any SNN candidate beats FSM or is lower-activity within F1 tolerance, so that the next research direction is evidence-driven.

## 5. UX / CLI requirements

Add a new command:

```bash
make snn-search
```

Add a module CLI:

```bash
PYTHONPATH=python python -m tinysnnrfid.run_snn_search --config configs/snn_search_default.json
```

The command should print:

```text
SNN search configuration loaded: configs/snn_search_default.json
Running N candidate configurations...
Search results written: results/snn_search/search_results.json
Search CSV written: results/snn_search/search_summary.csv
Search report written: results/snn_search/search_report.md
```

The search outputs must be generated artifacts and must not be committed.

## 6. Functional requirements

1. Add `configs/snn_search_default.json`.
2. Add a search runner, preferably `python/tinysnnrfid/run_snn_search.py`.
3. Add a compatibility wrapper `python/run_snn_search.py` if the repo pattern uses wrappers.
4. Add `make snn-search`.
5. The search must evaluate multiple `tiny_snn_v2` configs using existing dataset generation and benchmark evaluation code.
6. The search must compare all candidates against the reference classifier, default `fsm`.
7. The search must produce JSON, CSV, and Markdown outputs under:

```text
results/snn_search/
```

8. Required generated outputs:

```text
results/snn_search/search_results.json
results/snn_search/search_summary.csv
results/snn_search/search_report.md
```

9. The search config must support sweeping:
   - `classifiers.tiny_snn_v2.hidden_threshold`
   - `classifiers.tiny_snn_v2.output_threshold`
   - `classifiers.tiny_snn_v2.leak`
   - `classifiers.tiny_snn_v2.reset_on_spike`
   - predefined `weight_variant` names
   - seeds
   - optional dataset noise/jitter/dropout values
10. The search must include at least these weight variants:

```text
current_default
ternary_event_order
ternary_noise_guard
low_activity_sparse
balanced_small_int
```

11. Each weight variant must define:

```text
input_weights
output_weights
hidden_neurons
short description
```

12. All weight variants must be integer-only.
13. At least one variant must use ternary weights only: `-1`, `0`, `+1`.
14. At least one variant must use small signed integer weights limited to `[-2, 2]`.
15. The current default v2 weights must be included as a baseline variant.
16. The search must preserve the original `tiny_snn_v2` default classifier in normal `configs/default.json` unless intentionally changed by config.
17. The search must not mutate global default config objects in place.
18. The search must record candidate metadata:

```json
{
  "candidate_id": "candidate_0000",
  "weight_variant": "ternary_event_order",
  "hidden_threshold": 3,
  "output_threshold": 3,
  "leak": 1,
  "reset_on_spike": true,
  "seed": 1234
}
```

19. The search results must include all benchmark metrics for every classifier, not only `tiny_snn_v2`.
20. The search summary must rank candidates by:
   - candidate F1,
   - candidate accuracy,
   - lower candidate activity proxy,
   - competitive reason against reference.
21. The search report must include:
   - top candidates by F1,
   - top candidates by lower activity within F1 tolerance,
   - best candidate per scenario,
   - whether any candidate justifies further SNN optimization,
   - whether FSM/LUT RTL should be prioritized instead.
22. The report must keep the warning that software activity proxy is not hardware power.
23. Add tests.
24. Existing `make test`, `make sweep`, and `make benchmark` must keep working.

## 7. Suggested config format

Create `configs/snn_search_default.json`:

```json
{
  "name": "tiny_snn_v2_default_search",
  "base_config": "configs/default.json",
  "output_dir": "results/snn_search",
  "dataset_output_root": "results/snn_search/generated",
  "seeds": [1234, 1235],
  "dataset_overrides": {
    "dataset.num_samples": 300
  },
  "dataset_parameters": {
    "dataset.noise_probability": [0.0, 0.05, 0.1],
    "dataset.jitter_probability": [0.0, 0.2],
    "dataset.dropout_probability": [0.0, 0.1]
  },
  "snn_parameters": {
    "classifiers.tiny_snn_v2.hidden_threshold": [3, 4, 5],
    "classifiers.tiny_snn_v2.output_threshold": [2, 3, 4],
    "classifiers.tiny_snn_v2.leak": [0, 1],
    "classifiers.tiny_snn_v2.reset_on_spike": [true]
  },
  "weight_variants": [
    "current_default",
    "ternary_event_order",
    "ternary_noise_guard",
    "low_activity_sparse",
    "balanced_small_int"
  ],
  "comparison": {
    "reference_classifier": "fsm",
    "candidate_classifier": "tiny_snn_v2",
    "f1_tolerance": 0.03
  },
  "limits": {
    "max_candidates": 200
  }
}
```

## 8. Weight variant guidance

Implement weight variants in code, not by executing config strings.

Suggested structure:

```python
WEIGHT_VARIANTS = {
    "current_default": {
        "description": "Existing small integer v2 weights.",
        "hidden_neurons": 6,
        "input_weights": [...],
        "output_weights": [...],
    },
    "ternary_event_order": {...},
}
```

Do not use `eval`.

Each variant must validate with existing `tiny_snn_v2` config validation.

## 9. Output schema

### `search_results.json`

Suggested shape:

```json
{
  "search": {
    "name": "tiny_snn_v2_default_search",
    "candidate_count": 100,
    "generated_at": "..."
  },
  "runs": [
    {
      "candidate_id": "candidate_0000",
      "seed": 1234,
      "weight_variant": "ternary_event_order",
      "parameters": {},
      "dataset": {},
      "classifiers": {},
      "comparison": {}
    }
  ],
  "aggregate": {},
  "decision": {}
}
```

### `search_summary.csv`

One row per candidate run.

Required columns:

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

### `search_report.md`

Required sections:

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

## 10. Decision rules

Use strict comparison semantics from the sweep runner:

A candidate run is competitive only if:

```text
candidate F1 > reference F1
```

or:

```text
candidate activity proxy < reference activity proxy
and candidate F1 >= reference F1 - f1_tolerance
```

Recommendations:

```text
If any candidate has competitive_reason == f1_win:
    recommendation = continue_snn_optimization
Else if any candidate has competitive_reason == activity_win_within_f1_tolerance:
    recommendation = continue_snn_optimization
Else if best candidate is close to reference but no activity advantage:
    recommendation = add_harder_temporal_scenarios
Else:
    recommendation = prioritize_fsm_or_lut_rtl_baseline
```

## 11. Tests

Add `tests/test_snn_search.py`.

Required tests:

1. Search config loads and validates.
2. Invalid weight variant name is rejected.
3. Candidate grid expansion is deterministic.
4. Candidate limit is respected.
5. Weight variants validate as integer-only.
6. At least one variant is ternary-only.
7. Search writes JSON, CSV, and Markdown outputs on a tiny config.
8. CSV contains required columns.
9. Search results include candidate comparison fields.
10. Decision recommendation is one of:

```text
continue_snn_optimization
add_harder_temporal_scenarios
prioritize_fsm_or_lut_rtl_baseline
```

11. Existing `make test` still passes.

## 12. Manual checks

Run:

```bash
make test
make snn-search
```

Inspect:

```text
results/snn_search/search_results.json
results/snn_search/search_summary.csv
results/snn_search/search_report.md
```

Confirm:

- Search outputs are generated.
- Generated outputs are ignored by git.
- Report clearly says activity proxy is not hardware power.
- The best candidate and decision summary are easy to understand.

## 13. Definition of done

This task is done when:

- `make snn-search` works.
- `configs/snn_search_default.json` exists.
- Search outputs JSON, CSV, and Markdown.
- Multiple weight variants are evaluated.
- At least one ternary variant is included.
- The search uses strict competitive-case semantics.
- Tests cover config, candidates, outputs, and decision behavior.
- Existing benchmark and sweep commands still work.
- No generated outputs are committed.
