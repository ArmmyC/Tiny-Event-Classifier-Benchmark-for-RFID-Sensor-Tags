# Feature Spec: Tiny SNN v2 Hidden-Layer IF/LIF Classifier

## 1. Goal

Build a more realistic tiny SNN classifier for the existing RFID-style event benchmark.

The current `tiny_snn` classifier behaves too much like an FSM with membrane state because it directly follows the target pattern using a `progress` variable. This feature replaces or extends that classifier with a true small hidden-layer integrate-and-fire or leaky-integrate-and-fire model using integer membrane states, fixed ternary weights, event-driven updates, and one output neuron.

The goal is not to prove the SNN wins yet. The goal is to make the SNN baseline scientifically meaningful enough to compare against threshold logic, FSM, and LUT-like classifiers across existing scenario-tagged benchmark cases.

## 2. Non-goals

Do not build:

- RTL for the SNN.
- On-chip learning.
- Backpropagation, surrogate gradients, or gradient-based training.
- A large neural network.
- A dependency on PyTorch, TensorFlow, JAX, or other heavyweight ML frameworks.
- Hardware power or silicon area claims.
- A web dashboard.
- A new benchmark task unrelated to the existing noisy event detector.
- A full neuromorphic simulator.

This feature is limited to a Python software classifier implementation and benchmark/report integration.

## 3. Assumptions

- The repo already contains the Python benchmark MVP.
- The repo already contains scenario-tagged datasets and per-scenario metrics.
- Existing commands such as `make data`, `make eval`, `make benchmark`, and `make test` must keep working.
- The classifier package lives under `python/tinysnnrfid/classifiers/`.
- The current classifier name `tiny_snn` is already used by the benchmark.
- It is acceptable either to update the existing `tiny_snn` implementation in place or add a new classifier name such as `tiny_snn_v2`, as long as backward compatibility is preserved.
- Inference must use integer arithmetic where practical.
- Weights are manually configured at first.
- The SNN should be small enough to plausibly map to future RTL.

## 4. User stories

- As a researcher, I want the SNN baseline to use hidden neurons and fixed weights, so that it is meaningfully different from an FSM.
- As a benchmark user, I want to compare `tiny_snn_v2` against threshold, FSM, LUT-like, and the old tiny SNN, so that I can see whether the new model improves any scenario.
- As a future RTL implementer, I want the SNN inference path to use integer state updates, so that the design can later be translated to SystemVerilog.
- As a project maintainer, I want tests for the new SNN dynamics, so that future changes do not silently turn it back into FSM logic.
- As a researcher, I want per-scenario report output to include the new SNN, so that I can see whether it helps on jitter, dropout, dense noise, or accidental-pattern cases.

## 5. UX / UI requirements

This feature has no graphical UI.

The command-line UX must remain compatible with the existing workflow:

```bash
make data
make eval
make benchmark
make test
```

The default benchmark should include the new classifier in the results. Preferred classifier name:

```text
tiny_snn_v2
```

If the existing benchmark expects `tiny_snn`, keep `tiny_snn` working. Either:

1. Keep the old implementation as `tiny_snn_legacy` and make `tiny_snn` point to the new v2 implementation, or
2. Keep old `tiny_snn` unchanged and add `tiny_snn_v2` as an additional enabled classifier.

Prefer option 2 for easier before/after comparison.

Benchmark reports should show the new classifier in the overall metrics table, per-scenario metrics table, and activity proxy table.

## 6. Functional requirements

1. Add a hidden-layer SNN classifier implementation with a stable public name, preferably `tiny_snn_v2`.
2. The classifier must implement the existing shared classifier interface.
3. The classifier must accept input arrays shaped `[num_samples, sequence_length, input_width]`.
4. The classifier must return binary predictions shaped `[num_samples]`.
5. The classifier must use at least one hidden layer with configurable hidden neuron count.
6. The default hidden neuron count must be small, between 4 and 8.
7. The classifier must use integer membrane states.
8. The classifier must use fixed integer weights.
9. The default weights must be ternary or small integer values, such as `-1`, `0`, `+1`, or a small bounded integer range.
10. The inference path must not depend on floating-point math.
11. The classifier must support optional leak.
12. The classifier must support membrane clipping with configurable minimum and maximum values.
13. The classifier must support hidden neuron spike thresholds.
14. The classifier must support an output neuron or output accumulator with configurable threshold.
15. The classifier must update state only when there is input activity or when leak is enabled.
16. The classifier must expose an activity proxy compatible with the existing report format.
17. The activity proxy must count or estimate input spike processing, hidden neuron updates, output updates, and emitted spikes where practical.
18. The classifier must not use a `progress` variable that directly indexes the target pattern as the main detection mechanism.
19. The classifier must not call the FSM classifier internally.
20. The classifier must be deterministic for the same input and config.
21. Add config fields for the new classifier under `classifiers.tiny_snn_v2`.
22. Add `tiny_snn_v2` to known classifier validation.
23. Add `tiny_snn_v2` to default enabled classifiers unless this causes unacceptable test breakage.
24. Existing classifiers must still work.
25. Existing benchmark JSON schema must remain backward compatible.
26. Existing Markdown report generation must include the new classifier automatically.
27. Add tests for hidden-layer SNN inference behavior.
28. Add tests that verify the new classifier does not expose or depend on a direct FSM-style `progress` field.
29. Add tests for deterministic predictions.
30. Add tests for activity proxy output.
31. Add or update README documentation to explain the difference between `tiny_snn` and `tiny_snn_v2`.

## 7. Technical requirements

### Architecture

Add or update files under:

```text
python/tinysnnrfid/classifiers/
```

Preferred new file:

```text
python/tinysnnrfid/classifiers/tiny_snn_v2.py
```

Update:

```text
python/tinysnnrfid/classifiers/__init__.py
python/tinysnnrfid/config.py
python/tinysnnrfid/run_benchmark.py
configs/default.json
README.md
tests/test_classifiers.py
```

Add a focused test file if useful:

```text
tests/test_tiny_snn_v2.py
```

### Suggested model

Implement a small integer IF/LIF network:

```text
input channels -> hidden IF/LIF neurons -> output IF/LIF neuron -> binary class
```

Default shape:

```text
input_width = 4
hidden_neurons = 6
output_neurons = 1
```

State:

```text
hidden_membrane: int array [hidden_neurons]
output_membrane: int
```

Weights:

```text
input_to_hidden: int array [input_width, hidden_neurons]
hidden_to_output: int array [hidden_neurons]
```

Suggested default hand-designed hidden roles:

- Some neurons respond positively to channel 0 then decay slowly.
- Some neurons respond positively to channel 1 while inhibited by excessive noise.
- Some neurons respond positively to channel 2 while inhibited by dense activity.
- Some neurons act as coincidence or temporal-memory units.
- Some neurons inhibit output when too many channels fire at once.

A simple default weight matrix is acceptable as long as it is documented and tested.

### Inference behavior

For each sequence:

1. Reset hidden and output membranes.
2. For each timestep:
   - Read input vector.
   - Compute whether the timestep has any spike.
   - Apply leak if enabled.
   - If input has spikes, update hidden membranes using integer weighted input.
   - Clip hidden membranes to configured min/max.
   - Convert hidden membranes to binary hidden spikes when they cross threshold.
   - Optionally reset hidden neurons that spike.
   - Update output membrane using hidden spikes and hidden-to-output weights.
   - Clip output membrane.
   - If output crosses threshold, return class `1`.
3. If no output spike occurs, return class `0`.

### Config shape

Add config like:

```json
"tiny_snn_v2": {
  "hidden_neurons": 6,
  "hidden_threshold": 3,
  "output_threshold": 3,
  "leak": 1,
  "membrane_min": 0,
  "membrane_max": 7,
  "reset_on_spike": true,
  "input_weights": [
    [1, 0, 0, -1, 1, 0],
    [0, 1, 0, -1, 1, 1],
    [0, 0, 1, -1, 0, 1],
    [-1, -1, -1, 1, 0, 0]
  ],
  "output_weights": [1, 1, 1, -2, 1, 1]
}
```

Validation rules:

- `hidden_neurons` must be a positive integer.
- `hidden_threshold` must be a positive integer.
- `output_threshold` must be a positive integer.
- `leak` must be a non-negative integer.
- `membrane_min` and `membrane_max` must be integers and `membrane_min < membrane_max`.
- `reset_on_spike` must be boolean.
- `input_weights` must have shape `[input_width, hidden_neurons]`.
- `output_weights` must have length `hidden_neurons`.
- All weights must be integers.

If this validation is too large for the first pass, implement the critical shape checks and add TODO comments for stricter validation.

### Data flow

The existing flow should remain:

```text
config -> dataset generation -> benchmark runner -> classifiers -> metrics -> JSON/Markdown report
```

The new classifier should plug into the classifier factory used by the benchmark runner.

### Security

No new security-sensitive features are introduced.

Do not execute arbitrary code from config.

Do not load weights through Python `eval`.

Do not add network access.

## 8. Files likely involved

Likely create:

```text
python/tinysnnrfid/classifiers/tiny_snn_v2.py
tests/test_tiny_snn_v2.py
```

Likely modify:

```text
configs/default.json
python/tinysnnrfid/config.py
python/tinysnnrfid/classifiers/__init__.py
python/tinysnnrfid/run_benchmark.py
README.md
tests/test_classifiers.py
```

Do not modify generated benchmark outputs unless a test fixture requires it.

## 9. Data model

No database changes.

No dataset format changes are required.

No changes are required to:

```text
inputs.npy
labels.npy
metadata.json
scenario_tags.json
test_vectors.txt
```

Benchmark output JSON should naturally include the new classifier under:

```json
"classifiers": {
  "tiny_snn_v2": {
    "accuracy": 0.0,
    "precision": 0.0,
    "recall": 0.0,
    "f1": 0.0,
    "tp": 0,
    "tn": 0,
    "fp": 0,
    "fn": 0,
    "confusion_matrix": [[0, 0], [0, 0]],
    "activity_proxy": {},
    "per_scenario": {}
  }
}
```

## 10. API contract

No HTTP API is required.

The CLI contract remains:

### Generate dataset

```bash
PYTHONPATH=python python -m tinysnnrfid.generate_dataset --config configs/default.json
```

No behavioral change required.

### Run benchmark

```bash
PYTHONPATH=python python -m tinysnnrfid.run_benchmark --config configs/default.json
```

Expected behavior:

- Loads the same generated dataset.
- Evaluates existing classifiers.
- Evaluates `tiny_snn_v2` if enabled in config.
- Writes `results/benchmark_results.json` and `results/benchmark_report.md`.

Error cases:

- Invalid `tiny_snn_v2` config.
- Weight matrix shape mismatch.
- Non-integer weights.
- Classifier returns invalid prediction shape.

## 11. Edge cases

- Input sequence has no spikes.
- Input sequence has dense spikes every cycle.
- Input width does not match weight matrix width.
- Hidden neuron count does not match weight matrix width.
- Output weight count does not match hidden neuron count.
- Leak is greater than membrane max.
- Membrane max is too low to reach threshold.
- Output threshold is unreachable with the configured weights.
- Negative weights dominate and no output spike is possible.
- Multiple hidden neurons spike on the same cycle.
- Reset-on-spike enabled versus disabled.
- The old `tiny_snn` and new `tiny_snn_v2` both appear in enabled classifiers.

## 12. Testing plan

### Unit tests

Add tests for:

- Classifier can be constructed from default config.
- Prediction output shape is correct.
- Predictions are binary.
- Predictions are deterministic.
- Empty/no-spike sequence returns `0`.
- A simple hand-crafted ordered sequence can produce `1` with default or test-specific weights.
- A reversed sequence should not produce the same easy positive behavior unless weights are intentionally order-insensitive.
- Dense noise sequence should not always produce `1`.
- Activity proxy contains total, mean, and max operation fields.
- Invalid weight shapes are rejected.
- Non-integer weights are rejected.
- Config validation rejects invalid hidden neuron count, thresholds, leak, and membrane ranges.

### Integration tests

Update the end-to-end benchmark test to assert:

- `tiny_snn_v2` appears in results when enabled.
- `tiny_snn_v2` has overall metrics.
- `tiny_snn_v2` has per-scenario metrics.
- Markdown report includes a row for `tiny_snn_v2`.

### Manual checks

Run:

```bash
pip install -r requirements.txt
make test
make benchmark
```

Then inspect:

```text
results/benchmark_results.json
results/benchmark_report.md
```

Confirm:

- `tiny_snn_v2` appears in all relevant result tables.
- Activity proxy warning still says values are not hardware power.
- Existing classifiers still appear.
- Existing generated dataset format is unchanged.

## 13. Definition of done

The task is complete only when:

- `tiny_snn_v2` is implemented as a hidden-layer integer IF/LIF classifier.
- The new classifier does not use direct FSM-style progress tracking as its main logic.
- The classifier is configurable from `configs/default.json`.
- Config validation covers the new classifier fields.
- Benchmark runner evaluates the new classifier when enabled.
- JSON and Markdown reports include the new classifier.
- Tests cover construction, inference, invalid config, deterministic behavior, activity proxy, and end-to-end benchmark integration.
- `make test` passes.
- `make benchmark` runs successfully.
- Existing dataset format and existing classifiers are not broken.
- No heavyweight ML dependency is introduced.
- No RTL or hardware power claims are introduced.

## 14. Codex implementation instructions

Implement this spec.

Do not change unrelated files.

Do not introduce heavyweight ML dependencies.

Do not implement training in this task.

Do not implement RTL in this task.

Follow existing project patterns.

Prefer adding `tiny_snn_v2` as a new classifier instead of overwriting the old `tiny_snn`, unless the existing project structure strongly favors replacement.

Keep inference integer-only where practical.

Use explicit fixed weights from config. Do not use `eval` or executable config parsing.

Keep the classifier small enough to be realistic for future RTL translation.

Run the relevant tests before finishing.

Run `make benchmark` after tests pass.

Summarize changed files, tests, and any tradeoffs.
