# Codex Prompt: Multi-Sensor Temporal Fusion Benchmark

You are working in the repository `Tiny-Event-Classifier-Benchmark-for-RFID-Sensor-Tags`.

Implement this spec:

```text
docs/specs/multi-sensor-temporal-fusion-benchmark.md
```

## Goal

Add a software-first benchmark family called `multi_sensor_temporal_fusion`.

The benchmark should test whether SNN-style temporal accumulation becomes more useful when the task is less friendly to exact-motif FSM/LUT baselines: more channels, longer sequences, loose timing windows, partial evidence, dropout, jitter, distractors, burst noise, and near-misses.

## Research Hypothesis

FSM and LUT-like baselines are strongest for small exact motifs. Sparse SNN-style classifiers may become more interesting when classification requires soft evidence accumulation across many noisy event channels.

Do not assume the SNN wins. Keep FSM and LUT-like baselines fair and included.

## Required Work

1. Keep the existing `temporal_hard` benchmark unchanged.
2. Add `configs/multi_sensor_temporal_fusion.json`.
3. Add `configs/sweep_multi_sensor_temporal_fusion.json`.
4. Add `configs/snn_search_multi_sensor_temporal_fusion.json`.
5. Add dataset support for `scenario_suite.mode = multi_sensor_temporal_fusion`.
6. Use a starting point of 8 channels and 64 cycles unless the implementation reveals a better documented value.
7. Generate positive samples from loose temporal evidence across multiple channels, not one exact ordered motif.
8. Include dropout, jitter, distractor events, burst noise, and partial near-misses.
9. Keep threshold, FSM, LUT-like, `tiny_snn_v2`, and existing SNN candidates available for comparison.
10. Add reporting that compares SNN vs FSM/LUT as task complexity increases.
11. Track F1, false positives, false negatives, and software activity proxy.
12. Preserve RTL evidence fields only as optional future fields: RTL simulation status, synthesis cell-count proxy, and VCD toggle-count proxy when RTL exists.
13. Do not create new RTL in this branch.
14. Do not remove or weaken the current sparse SNN RTL milestone.

## Suggested Scenario Tags

Add deterministic scenario generation for:

```text
clean_fusion_positive
jittered_fusion_positive
dropout_fusion_positive
distractor_fusion_positive
weak_partial_negative
wrong_context_negative
burst_noise_negative
near_miss_fusion_negative
```

Positive samples should satisfy the configured evidence rule. Negative samples should fail the evidence rule while remaining plausible near-boundary or noisy cases.

## Suggested Commands

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

Do not add the new benchmark to `make evidence` yet. Keep it as an explicit research branch until software evidence and runtime cost are understood.

## Constraints

- Software-first only.
- Do not add RTL.
- Do not add training.
- Do not add heavyweight ML dependencies.
- Do not change or remove `temporal_hard`.
- Do not weaken or rewrite the current `tiny_snn_v2_sparse_activity` RTL milestone.
- Do not claim silicon area.
- Do not claim measured power.
- Do not claim measured energy.
- Do not claim signoff.
- Do not commit generated outputs.

## Tests

Add tests for:

1. Existing `temporal_hard` config remains unchanged.
2. New config loads and uses `scenario_suite.mode = multi_sensor_temporal_fusion`.
3. New config uses 8 input channels and 64 cycles.
4. Scenario generation emits all configured tags with sufficient sample count.
5. Positive fusion scenarios satisfy the evidence rule.
6. Negative near-miss and partial scenarios fail the evidence rule.
7. Dropout, jitter, distractors, and burst noise are deterministic under seed.
8. Scenario counts appear in metadata.
9. Benchmark evaluation works with the new config.
10. Sweep works with a tiny temporary grid.
11. SNN search works with a tiny temporary candidate limit.
12. Reports compare SNN vs FSM/LUT baselines.
13. Reports include proxy limitation language.
14. Makefile has only software-first multi-sensor targets.
15. `make evidence` does not depend on the new benchmark.
16. Current sparse SNN RTL milestone docs remain unchanged.

## Manual Run

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

## Final Response

Summarize:

- scenario implemented
- configs added
- commands added
- reporting added
- tests added and run results
- how this benchmark tests whether SNNs become more useful when temporal classification is less FSM-friendly
- confirmation that no RTL was added
- confirmation that no silicon area, measured power, measured energy, or signoff claims were introduced
- confirmation that generated outputs were not committed
