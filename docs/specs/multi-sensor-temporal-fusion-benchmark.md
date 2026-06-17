# Feature Spec: Multi-Sensor Temporal Fusion Benchmark

## 1. Goal

Design and implement a second benchmark family called `multi_sensor_temporal_fusion`.

The current `temporal_hard` benchmark is valuable, but it still centers on a small exact ordered motif over 4 input channels. That is a natural strength for compact FSM and LUT-like baselines.

This benchmark should test a less FSM-friendly setting:

```text
Can sparse SNN-style classifiers become more useful when the task requires soft evidence accumulation across many noisy event channels, loose timing windows, partial evidence, and distractors?
```

The first implementation must be software-first. Do not create new RTL until software evidence shows a candidate worth mapping.

## 2. Research Hypothesis

FSM and LUT-like baselines are strongest for small exact motifs. A sequence such as:

```text
channel 0 -> channel 1 -> channel 2
```

can be represented directly by a small state machine or compact rule table.

Sparse SNN-style classifiers may become more interesting when the decision is not one exact ordered pattern. The target should require accumulating multiple weak pieces of evidence across channels and time while resisting noise, dropout, distractors, and near-misses.

The expected result is not that the SNN automatically wins. The benchmark should fairly test whether SNN-style temporal accumulation becomes more competitive as task complexity increases.

## 3. Non-goals

Do not implement:

- new RTL in the first branch
- training or gradient-based learning
- PyTorch, TensorFlow, JAX, pandas, or other heavyweight dependencies
- runtime-programmable weights
- changes that remove, weaken, or replace the current `temporal_hard` benchmark
- changes that remove, weaken, or replace the current sparse SNN RTL milestone
- silicon area claims
- measured power claims
- measured energy claims
- signoff claims

This is a software-first benchmark-design task.

## 4. Required Work

1. Keep the existing `temporal_hard` benchmark unchanged.
2. Add a new config for `multi_sensor_temporal_fusion`.
3. Use more channels than the current 4-channel task, for example 8 channels.
4. Use longer sequences than the current task, for example 64 cycles.
5. Positive samples must require loose temporal evidence across multiple channels, not one exact ordered motif.
6. Include dropout, jitter, distractor events, burst noise, and partial near-misses.
7. Keep FSM and LUT-like baselines fair and included.
8. Add reporting that compares SNN vs FSM/LUT as task complexity increases.
9. Track:
   - F1
   - false positives
   - false negatives
   - software activity proxy
   - RTL simulation status when RTL exists
   - synthesis cell-count proxy when RTL exists
   - VCD toggle-count proxy when RTL exists
10. Do not claim silicon area, measured power, measured energy, or signoff.
11. Do not remove or weaken the current sparse SNN RTL milestone.

## 5. Suggested Benchmark Shape

Add:

```text
configs/multi_sensor_temporal_fusion.json
```

Suggested starting values:

```json
{
  "dataset": {
    "num_samples": 480,
    "sequence_length": 64,
    "input_width": 8,
    "positive_ratio": 0.5,
    "valid_pattern": [0, 1, 2],
    "noise_probability": 0.03,
    "jitter_probability": 0.10,
    "dropout_probability": 0.08,
    "max_jitter": 3,
    "max_gap": 10,
    "train_test_split": 0.8,
    "random_seed": 2030
  },
  "scenario_suite": {
    "mode": "multi_sensor_temporal_fusion",
    "evidence_channels": [0, 1, 2, 3, 4],
    "context_channels": [5, 6, 7],
    "min_positive_evidence": 4,
    "evidence_window": 28,
    "loose_order": true,
    "mix": {
      "clean_fusion_positive": 0.12,
      "jittered_fusion_positive": 0.14,
      "dropout_fusion_positive": 0.12,
      "distractor_fusion_positive": 0.12,
      "weak_partial_negative": 0.14,
      "wrong_context_negative": 0.12,
      "burst_noise_negative": 0.12,
      "near_miss_fusion_negative": 0.12
    },
    "burst_length": 5,
    "distractor_count": 5,
    "allow_legacy_tags": false
  },
  "paths": {
    "data_dir": "data/generated_multi_sensor_temporal_fusion",
    "results_dir": "results/multi_sensor_temporal_fusion"
  }
}
```

The exact values may be adjusted during implementation, but the benchmark must remain larger and less exact-motif-oriented than `temporal_hard`.

## 6. Scenario Definitions

### `clean_fusion_positive`

A positive sample with enough evidence-channel events inside the allowed temporal window and little extra noise.

Purpose: establishes the core fusion task.

### `jittered_fusion_positive`

A positive sample where evidence events are shifted within a loose timing window.

Purpose: tests whether classifiers can tolerate timing variation without requiring an exact event order.

### `dropout_fusion_positive`

A positive sample where one or more evidence events may be missing, but the remaining evidence still crosses the configured positive threshold.

Purpose: tests robustness to partial sensor dropout.

### `distractor_fusion_positive`

A positive sample with sufficient true evidence plus extra distractor events on evidence or context channels.

Purpose: tests whether classifiers can accumulate useful evidence while ignoring unrelated activity.

### `weak_partial_negative`

A negative sample with some evidence events, but fewer than `min_positive_evidence`.

Purpose: tests false positives from partial evidence.

### `wrong_context_negative`

A negative sample with activity on context or distractor channels that resembles a positive in density but not in channel composition.

Purpose: tests channel selectivity.

### `burst_noise_negative`

A negative sample with bursts across one or more channels but without enough valid evidence-channel support.

Purpose: tests robustness to dense local noise.

### `near_miss_fusion_negative`

A negative sample that nearly satisfies the evidence threshold or timing window but violates at least one configured rule.

Purpose: tests ambiguity and near-boundary behavior.

## 7. Fair Baseline Requirements

FSM and LUT-like baselines must remain included and fair.

This benchmark should not make baselines artificially weak. Instead, it should increase the task dimensions in a realistic way:

- more channels
- longer sequences
- loose timing windows
- partial evidence
- distractors
- scenario-level complexity sweeps

The FSM baseline may need a fair software implementation that tracks evidence counts or temporal windows rather than only exact motif states. The LUT-like baseline may need a fair compact rule implementation that uses the same observable information available to the SNN.

The report should compare SNN candidates against:

- threshold logic
- FSM
- LUT-like logic
- `tiny_snn_v2`
- future sparse software variants, if added

## 8. Complexity Sweep

Add reporting that compares SNN vs FSM/LUT as task complexity increases.

Suggested complexity axes:

- number of input channels: 4, 6, 8
- sequence length: 32, 48, 64
- evidence threshold: 3 of 4, 4 of 5, 5 of 6
- distractor count: low, medium, high
- burst noise level: low, medium, high
- dropout probability: low, medium, high
- timing-window width: tight, medium, loose

The first implementation can use a modest grid, but the report must make clear whether SNN competitiveness changes as the task becomes less exact-motif-like.

## 9. Suggested Configs And Commands

Add:

```text
configs/multi_sensor_temporal_fusion.json
configs/sweep_multi_sensor_temporal_fusion.json
configs/snn_search_multi_sensor_temporal_fusion.json
```

Add Makefile targets:

```makefile
multi-sensor-benchmark:
	python python/generate_dataset.py --config configs/multi_sensor_temporal_fusion.json
	python python/evaluate_python.py --config configs/multi_sensor_temporal_fusion.json

multi-sensor-sweep:
	python python/run_sweep.py --config configs/sweep_multi_sensor_temporal_fusion.json

multi-sensor-snn-search:
	python python/run_snn_search.py --config configs/snn_search_multi_sensor_temporal_fusion.json
```

Do not add new RTL targets in the first branch.

Do not add this benchmark to `make evidence` until the software flow is stable and the runtime cost is understood.

## 10. Reporting Requirements

Reports should include:

- benchmark name: `multi_sensor_temporal_fusion`
- scenario mix and scenario counts
- per-classifier F1
- false positives
- false negatives
- per-scenario metrics
- SNN vs FSM/LUT comparison
- software activity proxy
- complexity-axis summary
- recommendation about whether a software candidate is worth later RTL mapping

When RTL exists later, reports should also include:

- RTL simulation status
- synthesis cell-count proxy
- VCD toggle-count proxy

Reports must state that:

- software activity is a proxy, not hardware power
- synthesis cell count is a proxy, not silicon area
- VCD toggle count is a proxy, not measured power or measured energy
- available RTL flow evidence is not signoff

## 11. Suggested Implementation Notes

Likely files to modify in the implementation branch:

```text
python/tinysnnrfid/config.py
python/tinysnnrfid/dataset.py
python/tinysnnrfid/generate_dataset.py
python/tinysnnrfid/evaluate_python.py
python/tinysnnrfid/run_sweep.py
python/tinysnnrfid/run_snn_search.py
configs/multi_sensor_temporal_fusion.json
configs/sweep_multi_sensor_temporal_fusion.json
configs/snn_search_multi_sensor_temporal_fusion.json
Makefile
README.md
tests/test_dataset.py
tests/test_benchmark_flow.py
```

Optional new tests:

```text
tests/test_multi_sensor_temporal_fusion.py
```

Keep changes compatible with existing `legacy` and `temporal_hard` modes.

## 12. Tests

Add tests that cover:

1. `temporal_hard` config remains unchanged.
2. `multi_sensor_temporal_fusion` config loads successfully.
3. The new config uses `input_width = 8`.
4. The new config uses `sequence_length = 64`.
5. The new scenario mode is validated.
6. All configured scenario tags can be generated with sufficient sample count.
7. Positive fusion scenarios meet the configured evidence rule.
8. Negative near-miss scenarios do not meet the configured evidence rule.
9. Dropout and jitter are deterministic under seed.
10. Scenario tags length equals the sample count.
11. Scenario counts are included in metadata.
12. Benchmark evaluation works with the new config.
13. Sweep config works with a tiny temporary grid.
14. SNN search config works with a tiny temporary candidate limit.
15. Reports include proxy limitation language.
16. Makefile includes new software-first targets only.
17. `make evidence` does not depend on the new benchmark yet.
18. Current sparse RTL milestone docs remain unchanged.

## 13. Manual Checks

Run:

```bash
python -m pytest
make multi-sensor-benchmark
make multi-sensor-sweep
make multi-sensor-snn-search
```

Inspect:

```text
results/multi_sensor_temporal_fusion/benchmark_report.md
results/multi_sensor_temporal_fusion_sweeps/sweep_report.md
results/multi_sensor_temporal_fusion_snn_search/search_report.md
```

Confirm:

- reports include scenario-level metrics
- reports compare SNN vs FSM/LUT baselines
- reports describe activity as a software proxy
- no silicon area, measured power, measured energy, or signoff claims are introduced
- no generated outputs are committed

## 14. Definition Of Done

This task is complete when:

- `multi_sensor_temporal_fusion` is implemented as a separate benchmark family.
- `temporal_hard` remains unchanged and tested.
- The new config uses a larger 8-channel, 64-cycle starting point.
- Positives require loose multi-channel temporal evidence, not one exact ordered motif.
- Negatives include partial evidence, wrong context, burst noise, and near misses.
- Dropout, jitter, distractors, and burst noise are represented.
- FSM and LUT-like baselines remain included and fair.
- Reports compare SNN vs FSM/LUT as complexity increases.
- Reports track F1, false positives, false negatives, and software activity proxy.
- RTL proxy fields are included only when RTL exists.
- No new RTL is created before software evidence justifies mapping.
- The current sparse SNN RTL milestone remains intact.
- Tests pass.
- No generated outputs are committed.
