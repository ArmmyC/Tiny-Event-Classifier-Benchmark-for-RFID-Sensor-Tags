import json
from collections import Counter

import numpy as np

from tinysnnrfid.dataset import (
    DatasetConfig,
    contains_ordered_pattern,
    generate_noisy_event_dataset,
    generate_noisy_event_dataset_with_scenarios,
    save_dataset,
)


def test_dataset_is_deterministic_and_binary() -> None:
    config = DatasetConfig(num_sequences=20, seq_len=12, seed=7, jitter_prob=0.5, dropout_prob=0.2)
    first_inputs, first_labels = generate_noisy_event_dataset(config)
    second_inputs, second_labels = generate_noisy_event_dataset(config)
    np.testing.assert_array_equal(first_inputs, second_inputs)
    np.testing.assert_array_equal(first_labels, second_labels)
    assert first_inputs.shape == (20, 12, 4)
    assert first_inputs.dtype == np.uint8
    assert set(first_labels.tolist()) == {0, 1}


def test_save_dataset_artifacts_and_vector_format(tmp_path) -> None:
    config = DatasetConfig(num_sequences=4, seq_len=8, input_width=4, seed=2)
    save_dataset(tmp_path, config)
    assert (tmp_path / "inputs.npy").is_file()
    assert (tmp_path / "labels.npy").is_file()
    assert (tmp_path / "scenario_tags.json").is_file()
    metadata = json.loads((tmp_path / "metadata.json").read_text(encoding="utf-8"))
    scenario_tags = json.loads((tmp_path / "scenario_tags.json").read_text(encoding="utf-8"))
    assert metadata["input_shape"] == [4, 8, 4]
    assert len(scenario_tags) == 4
    assert sum(metadata["scenario_counts"].values()) == 4
    assert {key: value for key, value in metadata["scenario_counts"].items() if value} == Counter(scenario_tags)
    lines = (tmp_path / "test_vectors.txt").read_text(encoding="utf-8").splitlines()
    assert lines[0] == "# sample_index label sequence_length input_width"
    fields = lines[1].split()
    assert fields[2:4] == ["8", "4"]
    assert len(fields) == 12
    assert all(len(token) == 4 for token in fields[4:])


def test_contains_ordered_pattern_and_gap() -> None:
    sequence = np.zeros((8, 4), dtype=np.uint8)
    sequence[1, 0] = 1
    sequence[3, 1] = 1
    sequence[7, 2] = 1
    assert contains_ordered_pattern(sequence, (0, 1, 2))
    assert not contains_ordered_pattern(sequence, (2, 1, 0))
    assert contains_ordered_pattern(sequence, (0, 1, 2), max_gap=4)
    assert not contains_ordered_pattern(sequence, (0, 1, 2), max_gap=3)


def test_accidental_pattern_negative_detection() -> None:
    sequence = np.zeros((6, 4), dtype=np.uint8)
    sequence[0, 0] = 1
    sequence[2, 1] = 1
    sequence[4, 2] = 1
    assert contains_ordered_pattern(sequence, (0, 1, 2), max_gap=3)


def test_dense_noise_negatives_are_tagged() -> None:
    config = DatasetConfig(
        num_sequences=5,
        seq_len=4,
        input_width=4,
        positive_ratio=0.0,
        noise_prob=1.0,
        dense_noise_spike_threshold=8,
        seed=3,
    )
    _, labels, scenario_tags = generate_noisy_event_dataset_with_scenarios(config)
    assert labels.tolist() == [0, 0, 0, 0, 0]
    assert scenario_tags == ["dense_noise_negative"] * 5
