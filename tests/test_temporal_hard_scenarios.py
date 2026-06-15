import json
from collections import Counter

import numpy as np

from tinysnnrfid.config import DEFAULT_CONFIG
from tinysnnrfid.dataset import (
    DatasetConfig,
    TEMPORAL_HARD_SCENARIO_TAGS,
    contains_ordered_pattern,
    generate_noisy_event_dataset_with_scenarios,
    save_dataset,
)
from tinysnnrfid.run_benchmark import run_benchmark


TEMPORAL_MIX = {tag: 1.0 for tag in TEMPORAL_HARD_SCENARIO_TAGS}


def temporal_config(num_sequences: int = 80) -> DatasetConfig:
    return DatasetConfig(
        num_sequences=num_sequences,
        seq_len=40,
        input_width=4,
        seed=42,
        motif=(0, 1, 2),
        max_gap=5,
        scenario_suite_mode="temporal_hard",
        scenario_mix=TEMPORAL_MIX,
        max_long_gap=10,
        burst_length=4,
        distractor_count=2,
    )


def test_temporal_hard_generates_all_tags_and_shapes() -> None:
    config = temporal_config()
    inputs, labels, tags = generate_noisy_event_dataset_with_scenarios(config)
    assert inputs.shape == (80, 40, 4)
    assert inputs.dtype == np.uint8
    assert labels.shape == (80,)
    assert set(tags) == set(TEMPORAL_HARD_SCENARIO_TAGS)
    assert len(tags) == 80


def test_temporal_hard_labels_match_tags() -> None:
    inputs, labels, tags = generate_noisy_event_dataset_with_scenarios(temporal_config())
    positive_tags = {"clean_positive", "long_gap_positive", "distractor_positive", "dropout_positive"}
    for sequence, label, tag in zip(inputs, labels, tags):
        assert int(label) == int(tag in positive_tags)
        if tag in {"clean_positive", "long_gap_positive", "distractor_positive"}:
            assert contains_ordered_pattern(sequence, (0, 1, 2))
        if tag == "dropout_positive":
            assert not contains_ordered_pattern(sequence, (0, 1, 2))
        if tag in {"reversed_negative", "partial_order_negative", "burst_noise_negative", "near_miss_negative"}:
            assert int(label) == 0


def test_temporal_hard_scenario_counts_in_metadata(tmp_path) -> None:
    config = temporal_config()
    save_dataset(tmp_path, config)
    metadata = json.loads((tmp_path / "metadata.json").read_text(encoding="utf-8"))
    tags = json.loads((tmp_path / "scenario_tags.json").read_text(encoding="utf-8"))
    assert metadata["scenario_suite"]["mode"] == "temporal_hard"
    assert metadata["scenario_suite"]["effective_counts"] == metadata["scenario_counts"]
    assert Counter(tags) == metadata["scenario_counts"]


def test_temporal_hard_benchmark_flow(tmp_path) -> None:
    benchmark_config = json.loads(json.dumps(DEFAULT_CONFIG))
    benchmark_config["dataset"].update({"num_samples": 40, "sequence_length": 40, "random_seed": 44})
    benchmark_config["scenario_suite"] = {
        "mode": "temporal_hard",
        "mix": TEMPORAL_MIX,
        "max_long_gap": 10,
        "burst_length": 4,
        "distractor_count": 2,
        "allow_legacy_tags": True,
    }
    data_dir = tmp_path / "data"
    results_dir = tmp_path / "results"
    save_dataset(
        data_dir,
        DatasetConfig.from_mapping(
            benchmark_config["dataset"],
            benchmark_config["scenario"],
            benchmark_config["scenario_suite"],
        ),
        benchmark_config,
    )
    results = run_benchmark(benchmark_config, data_dir, results_dir)
    scenarios = set(results["classifiers"]["fsm"]["per_scenario"])
    assert "long_gap_positive" in scenarios
    assert "near_miss_negative" in scenarios
    report = (results_dir / "benchmark_report.md").read_text(encoding="utf-8")
    assert "long_gap_positive" in report
    assert "near_miss_negative" in report
