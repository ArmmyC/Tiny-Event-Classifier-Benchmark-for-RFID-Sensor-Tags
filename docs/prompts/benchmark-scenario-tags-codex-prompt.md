# Codex Prompt: Add Scenario Tags and Per-Scenario Metrics

You are working in the repository `Tiny-Event-Classifier-Benchmark-for-RFID-Sensor-Tags`.

Implement the next benchmark-validity improvement for the Python MVP.

## Goal

Improve the benchmark so results are easier to interpret scientifically. Right now the dataset only has binary labels, so false positives and false negatives are hard to analyze. Add scenario tags to each generated sequence and report per-scenario metrics for each classifier.

The goal is to answer questions like:

- Does a classifier fail mainly on noisy negatives?
- Does the SNN help on jittered positives?
- Does the FSM fail when the pattern has dropout?
- Are false positives caused by random noise accidentally forming the target pattern?

This is still a Python benchmark task. Do not implement RTL in this task.

## Current context

The current project already includes:

- `configs/default.json`
- `python/tinysnnrfid/config.py`
- `python/tinysnnrfid/dataset.py`
- `python/tinysnnrfid/run_benchmark.py`
- classifiers under `python/tinysnnrfid/classifiers/`
- `python/tinysnnrfid/metrics.py`
- `python/tinysnnrfid/report.py`
- tests under `tests/`

Follow the existing layout and style. Do not rewrite the whole project.

## Requirements

### 1. Add scenario tags to generated samples

Modify dataset generation so each sample gets a scenario tag.

Add at least these scenario tags:

```text
clean_positive
jittered_positive
dropped_positive
noise_negative
accidental_pattern_negative
dense_noise_negative
```

Definitions:

- `clean_positive`: positive sample where the full valid pattern is inserted without dropout and without timing jitter.
- `jittered_positive`: positive sample where the full valid pattern is present but at least one pattern event was timing-jittered.
- `dropped_positive`: positive sample where at least one intended pattern event was dropped.
- `noise_negative`: negative sample with sparse random noise and no valid ordered pattern.
- `accidental_pattern_negative`: negative sample where random noise accidentally forms the valid ordered pattern.
- `dense_noise_negative`: negative sample with unusually high total spike count, controlled by config.

The generator must save these tags to:

```text
data/generated/scenario_tags.json
```

Format:

```json
[
  "clean_positive",
  "noise_negative",
  "jittered_positive"
]
```

The number of tags must equal the number of samples.

Also include scenario counts in `metadata.json`:

```json
"scenario_counts": {
  "clean_positive": 123,
  "jittered_positive": 120,
  "dropped_positive": 80,
  "noise_negative": 400,
  "accidental_pattern_negative": 50,
  "dense_noise_negative": 227
}
```

### 2. Add config options

Extend `configs/default.json` and config validation to support:

```json
"scenario": {
  "dense_noise_spike_threshold": 8,
  "force_minimum_per_scenario": false
}
```

Rules:

- `dense_noise_spike_threshold` must be a non-negative integer.
- `force_minimum_per_scenario` must be a boolean.
- The implementation may use `force_minimum_per_scenario` only as a validation/planning field for now, but it must not break config loading.

### 3. Detect accidental valid patterns

Implement a reusable function that checks whether a sequence contains the ordered valid pattern.

Suggested signature:

```python
def contains_ordered_pattern(sequence: np.ndarray, pattern: tuple[int, ...], max_gap: int | None = None) -> bool:
    ...
```

Behavior:

- The function returns `True` if channels in `pattern` appear in order.
- If `max_gap` is provided, consecutive pattern events must be no more than `max_gap` cycles apart.
- It should work for binary arrays shaped `[sequence_length, input_width]`.
- Use this function to classify `accidental_pattern_negative`.

### 4. Load scenario tags with the dataset

Update dataset loading so benchmark execution can access scenario tags.

Preferred return shape:

```python
inputs, labels, metadata, scenario_tags = load_generated_dataset(data_dir)
```

If changing the return signature creates too much churn, introduce a new function such as:

```python
load_generated_dataset_with_scenarios(data_dir)
```

But keep backward compatibility where practical.

### 5. Add per-scenario metrics

For each classifier, compute metrics per scenario tag.

Example JSON shape:

```json
"classifiers": {
  "fsm": {
    "accuracy": 0.91,
    "precision": 0.88,
    "recall": 0.94,
    "f1": 0.91,
    "tp": 470,
    "tn": 440,
    "fp": 60,
    "fn": 30,
    "confusion_matrix": [[440, 60], [30, 470]],
    "activity_proxy": {},
    "per_scenario": {
      "clean_positive": {
        "count": 100,
        "accuracy": 1.0,
        "precision": 1.0,
        "recall": 1.0,
        "f1": 1.0,
        "tp": 100,
        "tn": 0,
        "fp": 0,
        "fn": 0,
        "confusion_matrix": [[0, 0], [0, 100]]
      }
    }
  }
}
```

For single-class scenarios, precision/recall must not crash. Use the existing zero-safe behavior from `binary_metrics`.

### 6. Update Markdown report

Update `results/benchmark_report.md` to include:

1. Dataset scenario counts.
2. Existing overall classifier metrics table.
3. New per-scenario metrics table.
4. Short interpretation notes that identify:
   - best overall classifier by F1
   - worst scenario for each classifier by F1 or accuracy
   - warning that scenario metrics are benchmark diagnostics, not hardware conclusions

The per-scenario table can be compact. Suggested columns:

```text
Classifier | Scenario | Count | Accuracy | Precision | Recall | F1 | FP | FN
```

### 7. Update test vector or metadata comments only if useful

Do not change the existing `test_vectors.txt` format unless necessary. It is intended for future RTL compatibility.

Scenario tags should be stored separately in `scenario_tags.json`.

### 8. Add tests

Add or update tests for:

- `contains_ordered_pattern` detects ordered motifs.
- `contains_ordered_pattern` rejects reversed motifs.
- `contains_ordered_pattern` respects `max_gap`.
- dataset generation writes `scenario_tags.json`.
- number of scenario tags equals number of samples.
- scenario counts in metadata match the saved scenario tags.
- benchmark JSON contains `per_scenario` for each classifier.
- Markdown report includes a per-scenario metrics section.
- accidental pattern negatives can be detected from synthetic sequences.
- dense noise negatives are tagged when total spike count reaches the configured threshold.

Use small deterministic datasets in tests.

### 9. Backward compatibility

Keep these commands working:

```bash
make data
make eval
make benchmark
python python/generate_dataset.py --config configs/default.json
python python/evaluate_python.py --config configs/default.json
PYTHONPATH=python python -m tinysnnrfid.generate_dataset --config configs/default.json
PYTHONPATH=python python -m tinysnnrfid.run_benchmark --config configs/default.json
```

Keep existing dataset artifacts:

```text
inputs.npy
labels.npy
metadata.json
test_vectors.txt
noisy_event_dataset.npz
vectors.hex
```

Add only:

```text
scenario_tags.json
```

### 10. Constraints

- Do not add heavyweight ML dependencies.
- Do not add pandas just for reporting.
- Do not implement training.
- Do not implement RTL.
- Do not make hardware power claims.
- Keep all random behavior deterministic under `random_seed`.
- Follow existing project patterns.
- Keep code readable for an intern-level research project.

## Manual checks to run

Run:

```bash
pip install -r requirements.txt
make test
make benchmark
```

Then inspect:

```text
data/generated/scenario_tags.json
data/generated/metadata.json
results/benchmark_results.json
results/benchmark_report.md
```

Confirm:

- `scenario_tags.json` exists.
- Scenario tag count equals number of labels.
- `metadata.json` contains `scenario_counts`.
- `benchmark_results.json` contains `per_scenario` for every classifier.
- `benchmark_report.md` has a per-scenario metrics table.
- Activity proxy text still warns that it is not hardware power.

## Definition of done

The task is complete only when:

- Scenario tags are generated and saved.
- Metadata includes scenario counts.
- Benchmark results include per-scenario metrics.
- Markdown report includes per-scenario analysis.
- All existing commands still work.
- Tests pass.
- Existing behavior is not broken.
- No hardware power or area claims are introduced.

## Final response format

After implementation, summarize:

1. Files changed.
2. New scenario-tagging behavior.
3. New report fields.
4. Tests added or updated.
5. Any tradeoffs or limitations.
