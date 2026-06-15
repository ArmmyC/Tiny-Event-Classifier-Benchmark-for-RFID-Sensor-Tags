# Feature Spec: Benchmark MVP

## 1. Goal

Build the first end-to-end benchmark pipeline for Tiny Event Classifier Benchmark for RFID Sensor Tags.

The goal is to let a researcher generate synthetic RFID-like sparse sensor event sequences, run multiple classifier implementations on the same dataset, compare their correctness metrics, and produce machine-readable plus human-readable reports. This MVP is the foundation for deciding whether a tiny SNN-style classifier is worth implementing in RTL later.

The feature should focus on the algorithmic benchmark first. It should not try to prove silicon power or area yet. It should create a reproducible Python baseline that can later feed RTL testbenches and synthesis flows.

## 2. Non-goals

This task should not build:

- A web dashboard.
- A GUI application.
- A complete RFID tag chip model.
- A full passive RFID energy-harvesting simulator.
- RTL implementations of all classifiers.
- Gate-level synthesis, place and route, or post-layout power analysis.
- On-chip learning for the SNN.
- A large neural network, LLM, or general ML accelerator.
- Mixed-signal neuromorphic circuits.
- Hardware-specific optimization for a particular PDK.

This feature is limited to a reproducible Python benchmark pipeline, documented data format, and report generation.

## 3. Assumptions

- The repository may be mostly empty or contain only the starter scaffold.
- Python is the first implementation language.
- The initial task is binary noisy event detection.
- Input sequences are synthetic and generated locally.
- Each sample is a fixed-length sequence of low-bit event vectors.
- The first benchmark uses 4 input channels and 32 cycles per sequence by default.
- Labels are binary: `0 = ignore/no event`, `1 = valid event`.
- A valid event is represented by an ordered temporal pattern across input channels.
- Noise is represented by random sparse bit spikes, dropped pattern events, or jittered pattern events.
- The SNN in this MVP is a small software model, not RTL.
- SNN weights may be manually configured at first. Training is optional for this feature.
- Results should be deterministic when a random seed is provided.
- No database is needed for this MVP. Files on disk are sufficient.
- The benchmark should be runnable from the command line and through `make` targets if a Makefile exists.

## 4. User stories

- As a researcher, I want to generate a reproducible synthetic event dataset, so that every classifier is tested on the same inputs.
- As a digital design intern, I want a simple benchmark command, so that I can run experiments without manually wiring scripts together.
- As a researcher, I want threshold, FSM, LUT-like, and tiny SNN classifiers compared on the same task, so that I can decide whether the SNN is worth deeper hardware work.
- As a future RTL implementer, I want test vectors exported in a simple text format, so that the same dataset can be reused in SystemVerilog testbenches later.
- As a project maintainer, I want JSON and Markdown reports, so that results can be tracked, reviewed, and committed.
- As a researcher, I want configurable noise, jitter, sequence length, and dataset size, so that I can stress-test classifier behavior.

## 5. UX / UI requirements

This feature has a command-line UX, not a graphical UI.

### CLI commands

The project should expose clear commands through scripts and preferably Makefile targets:

```bash
make data
make eval
make benchmark
```

If a Makefile does not exist, create one.

Required direct Python commands:

```bash
python -m tinysnnrfid.generate_dataset --config configs/default.yaml
python -m tinysnnrfid.run_benchmark --config configs/default.yaml
```

If the package layout does not support module execution yet, implement equivalent script paths under `python/` and document them in `README.md`.

### CLI states

The CLI should print concise progress messages:

- Dataset configuration loaded.
- Dataset generated.
- Classifiers evaluated.
- Reports written.

### Empty states

- If the output directory does not exist, create it automatically.
- If no dataset exists and the user runs evaluation only, show a clear error explaining how to generate the dataset.
- If the config file is missing, show a clear error and exit non-zero.

### Error states

The CLI must exit non-zero for:

- Invalid config values.
- Missing required input files.
- Dataset shape mismatch.
- Unknown classifier name.
- Inconsistent labels and sample counts.

Error messages should include the path or field that caused the failure.

### Responsive behavior

Not applicable. There is no browser UI in this feature.

## 6. Functional requirements

1. The system must provide a default configuration file at `configs/default.yaml` or `configs/default.json`.
2. The default configuration must define dataset size, sequence length, input width, valid pattern, noise probability, jitter probability, dropout probability, train/test split, random seed, and output directories.
3. The dataset generator must create a deterministic dataset when the same seed and config are used.
4. The dataset generator must produce input sequences with shape `[num_samples, sequence_length, input_width]`.
5. The dataset generator must produce binary labels with shape `[num_samples]`.
6. The dataset generator must support at least these event corruption modes: random noise spikes, pattern dropout, and timing jitter.
7. The dataset generator must save outputs under `data/generated/` by default.
8. The dataset generator must save `inputs.npy`, `labels.npy`, `metadata.json`, and `test_vectors.txt`.
9. `metadata.json` must include the full effective configuration, generation timestamp, random seed, input shape, label counts, and valid pattern definition.
10. `test_vectors.txt` must use a simple line-oriented format that can be consumed by RTL testbenches later.
11. The benchmark runner must load the generated dataset and evaluate all enabled classifiers.
12. The benchmark runner must include at least four classifiers: threshold, FSM, LUT-like, and tiny SNN.
13. The threshold classifier must make a binary decision from event counts or channel activation counts over the sequence.
14. The FSM classifier must detect an ordered temporal pattern and tolerate configurable jitter or gaps.
15. The LUT-like classifier must convert a compact feature representation into a deterministic lookup decision.
16. The tiny SNN classifier must implement a minimal integrate-and-fire style temporal accumulator with fixed weights, integer state, thresholding, and reset behavior.
17. The tiny SNN classifier must avoid floating-point operations in its inference path unless the current codebase already uses floats and the implementation clearly documents the limitation.
18. The benchmark runner must compute accuracy, precision, recall, F1 score, false positive count, false negative count, true positive count, true negative count, and confusion matrix.
19. The benchmark runner must compute simple activity proxy metrics for each classifier where practical.
20. Activity proxy metrics must be clearly labeled as software proxy metrics, not real hardware power.
21. The benchmark runner must write `results/benchmark_results.json`.
22. The benchmark runner must write `results/benchmark_report.md`.
23. The Markdown report must include config summary, dataset summary, classifier metrics table, and a short interpretation section.
24. The JSON report must include all metrics in machine-readable form.
25. The benchmark must be repeatable from a clean checkout using documented commands.
26. All Python modules must be importable without executing benchmark code as a side effect.
27. The code must include type hints for public functions where reasonable.
28. The code must include docstrings for dataset generation, classifier interfaces, and metric calculation functions.
29. The implementation must not require internet access at runtime.
30. Existing repository behavior must not be broken.

## 7. Technical requirements

### Architecture

Use a small modular Python architecture:

```text
configs/
  default.yaml or default.json
python/
  tinysnnrfid/
    __init__.py
    config.py
    dataset.py
    classifiers/
      __init__.py
      base.py
      threshold.py
      fsm.py
      lut.py
      tiny_snn.py
    metrics.py
    report.py
    generate_dataset.py
    run_benchmark.py
```

If the existing repository already has a different Python layout, follow the existing pattern while preserving the same logical modules.

### Data flow

1. User runs dataset generation.
2. Config is loaded and validated.
3. Synthetic sequences and labels are generated.
4. Dataset artifacts are saved to disk.
5. User runs benchmark.
6. Dataset and metadata are loaded.
7. Each enabled classifier predicts labels from the same input tensor.
8. Metrics are computed for each classifier.
9. JSON and Markdown reports are written.

### Classifier interface

All classifiers should implement a shared interface similar to:

```python
class Classifier:
    name: str

    def predict(self, inputs: np.ndarray) -> np.ndarray:
        """Return binary predictions with shape [num_samples]."""
```

Optional method:

```python
def activity_proxy(self, inputs: np.ndarray) -> dict[str, int | float]:
    """Return software-estimated operation or state-update counts."""
```

### Configuration validation

The config loader must validate:

- `num_samples > 0`
- `sequence_length > 0`
- `input_width > 0`
- Pattern channel indexes are within `[0, input_width - 1]`
- Probabilities are within `[0.0, 1.0]`
- Train/test split is greater than 0 and less than 1 if used
- Output paths are non-empty strings
- Enabled classifiers are known classifier names

### APIs

No web API is required for this feature.

### Database changes

No database is required.

### Permissions

No authentication or authorization is required.

### Security concerns

- Do not execute arbitrary code from config files.
- If YAML is used, load it with a safe loader.
- Validate output paths to avoid accidental writes outside the repository when relative paths are expected.
- Do not store secrets.
- Do not require network access.

### Reproducibility

- All random generation must use a seed from config.
- Store the seed and effective config in `metadata.json` and `benchmark_results.json`.
- Generated files should be deterministic except for timestamps.

## 8. Files likely involved

Create or modify these files as needed:

```text
README.md
Makefile
configs/default.yaml
configs/default.json
python/tinysnnrfid/__init__.py
python/tinysnnrfid/config.py
python/tinysnnrfid/dataset.py
python/tinysnnrfid/classifiers/__init__.py
python/tinysnnrfid/classifiers/base.py
python/tinysnnrfid/classifiers/threshold.py
python/tinysnnrfid/classifiers/fsm.py
python/tinysnnrfid/classifiers/lut.py
python/tinysnnrfid/classifiers/tiny_snn.py
python/tinysnnrfid/metrics.py
python/tinysnnrfid/report.py
python/tinysnnrfid/generate_dataset.py
python/tinysnnrfid/run_benchmark.py
tests/test_config.py
tests/test_dataset.py
tests/test_classifiers.py
tests/test_metrics.py
tests/test_benchmark_flow.py
results/.gitkeep
data/generated/.gitkeep
docs/specs/benchmark-mvp.md
```

If the repo already has equivalent files under different names, update those instead of duplicating functionality.

## 9. Data model

No relational database model is required.

Use file-based data artifacts.

### Dataset files

#### `data/generated/inputs.npy`

- Type: NumPy array
- Shape: `[num_samples, sequence_length, input_width]`
- Dtype: `uint8` or `bool`
- Values: `0` or `1`

#### `data/generated/labels.npy`

- Type: NumPy array
- Shape: `[num_samples]`
- Dtype: `uint8`, `int8`, or `bool`
- Values: `0` or `1`

#### `data/generated/metadata.json`

Fields:

```json
{
  "generated_at": "ISO-8601 timestamp",
  "seed": 1234,
  "num_samples": 1000,
  "sequence_length": 32,
  "input_width": 4,
  "label_counts": {"0": 500, "1": 500},
  "valid_pattern": [0, 1, 2],
  "config": {}
}
```

#### `data/generated/test_vectors.txt`

Required format:

```text
# sample_index label sequence_length input_width
0 1 32 4 0000 0001 0010 0100 ...
1 0 32 4 0000 0000 0001 0000 ...
```

Each timestep token must be a binary string of length `input_width`.

### Result files

#### `results/benchmark_results.json`

Fields:

```json
{
  "config": {},
  "dataset": {
    "num_samples": 1000,
    "sequence_length": 32,
    "input_width": 4,
    "label_counts": {"0": 500, "1": 500}
  },
  "classifiers": {
    "threshold": {
      "accuracy": 0.0,
      "precision": 0.0,
      "recall": 0.0,
      "f1": 0.0,
      "tp": 0,
      "tn": 0,
      "fp": 0,
      "fn": 0,
      "activity_proxy": {}
    }
  }
}
```

#### `results/benchmark_report.md`

Markdown report with:

- Title
- Generation/config summary
- Dataset summary
- Metrics table
- Activity proxy table
- Notes and interpretation

## 10. API contract

No HTTP API or server action is required.

Use CLI/module contracts instead.

### Command: Generate dataset

- Name: `generate_dataset`
- Method: CLI command
- Path: `python -m tinysnnrfid.generate_dataset --config configs/default.yaml`

Request body: none

Arguments:

```text
--config: path to YAML or JSON config file
--output-dir: optional override for generated dataset directory
```

Response body: none

Outputs:

```text
data/generated/inputs.npy
data/generated/labels.npy
data/generated/metadata.json
data/generated/test_vectors.txt
```

Error cases:

- Config file missing.
- Invalid config schema.
- Output directory cannot be created.
- Pattern refers to out-of-range input channel.

### Command: Run benchmark

- Name: `run_benchmark`
- Method: CLI command
- Path: `python -m tinysnnrfid.run_benchmark --config configs/default.yaml`

Request body: none

Arguments:

```text
--config: path to YAML or JSON config file
--data-dir: optional override for dataset directory
--results-dir: optional override for results directory
```

Response body: none

Outputs:

```text
results/benchmark_results.json
results/benchmark_report.md
```

Error cases:

- Dataset files missing.
- Dataset shape mismatch.
- Unknown classifier configured.
- Classifier prediction shape mismatch.
- Report output path cannot be written.

### Command: Full benchmark

- Name: `benchmark`
- Method: Makefile target
- Path: `make benchmark`

Behavior:

1. Generate dataset.
2. Run benchmark.
3. Print report path.

Error cases:

- Any error from dataset generation or benchmark execution.

## 11. Edge cases

- Dataset contains no positive samples because of misconfigured generation probabilities.
- Dataset contains no negative samples.
- Noise probability is `0.0`.
- Noise probability is `1.0`.
- Jitter moves events outside the sequence window.
- Dropout removes all events from a valid pattern.
- Sequence length is shorter than the valid pattern length.
- Input width is smaller than the largest channel index in the valid pattern.
- A classifier returns predictions with the wrong shape.
- Precision or recall denominator is zero.
- Output files already exist.
- Output directory is missing.
- Config uses YAML but PyYAML is unavailable.
- User runs the command from a different working directory.
- NumPy arrays have unexpected dtypes.
- `test_vectors.txt` line length does not match metadata.
- Activity proxy is not implemented for a classifier.

## 12. Testing plan

### Unit tests

Add tests for:

- Config loading and validation.
- Rejection of invalid probabilities.
- Rejection of out-of-range pattern channels.
- Deterministic dataset generation with a fixed seed.
- Dataset shape and dtype.
- Positive and negative sample generation.
- Test vector text export format.
- Threshold classifier predictions.
- FSM classifier predictions on known ordered patterns.
- LUT-like classifier predictions on known features.
- Tiny SNN state update and threshold/reset behavior.
- Metric calculations, including zero-division cases.
- Report generation from a small fake result object.

### Integration tests

Add an end-to-end test that:

1. Creates a temporary config.
2. Generates a small dataset.
3. Runs the benchmark.
4. Verifies JSON and Markdown reports exist.
5. Verifies all enabled classifiers appear in the JSON report.
6. Verifies all metric values are within valid ranges.

### UI tests

No browser UI tests are needed.

For CLI UX, test:

- `--help` works for dataset generation.
- `--help` works for benchmark execution.
- Missing config exits non-zero with a useful message.

### Manual checks

Run:

```bash
make data
make eval
make benchmark
python -m tinysnnrfid.generate_dataset --config configs/default.yaml
python -m tinysnnrfid.run_benchmark --config configs/default.yaml
```

Open:

```text
results/benchmark_report.md
results/benchmark_results.json
data/generated/test_vectors.txt
```

Confirm:

- The report is readable.
- The classifier table is populated.
- The generated dataset has both positive and negative labels.
- Re-running with the same seed gives the same inputs and labels.

## 13. Definition of done

The task is complete only when:

- All functional requirements are implemented.
- Tests pass.
- Lint/typecheck passes if the repo has lint/typecheck tooling.
- Existing behavior is not broken.
- The implementation matches this spec.
- `make data`, `make eval`, and `make benchmark` work from a clean checkout.
- The generated JSON report contains metrics for threshold, FSM, LUT-like, and tiny SNN classifiers.
- The generated Markdown report summarizes the benchmark results clearly.
- The dataset artifacts are documented and reusable for future RTL testbenches.
- Activity proxy metrics are clearly labeled as proxies, not hardware power numbers.

## 14. Codex implementation instructions

Implement this spec.

Do not change unrelated files.

Do not introduce new dependencies unless necessary. If YAML parsing would require a new dependency, prefer JSON config or implement graceful fallback behavior.

Follow existing project patterns. If the repository already has modules with similar names, extend them rather than creating duplicate implementations.

Keep the MVP small and reproducible. Prefer simple deterministic logic over complex model training.

Use NumPy for dataset arrays if it already exists in the project or is acceptable for this Python benchmark. Avoid heavyweight ML frameworks for this feature.

Implement threshold, FSM, LUT-like, and tiny SNN classifiers behind a shared interface.

Make the tiny SNN inference path integer-based where practical. Do not implement backpropagation, surrogate gradients, or on-chip learning in this task.

Write tests for config validation, dataset generation, classifiers, metrics, report generation, and the full benchmark flow.

Run the relevant tests before finishing.

Run lint and typecheck if the repository has configured commands.

Summarize changed files and any tradeoffs after implementation.

If a requirement cannot be implemented because the current repository structure is missing expected tooling, implement the smallest compatible version and document the limitation in the final summary.
