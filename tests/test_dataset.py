import json

import numpy as np

from tinysnnrfid.dataset import DatasetConfig, generate_noisy_event_dataset, save_dataset


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
    metadata = json.loads((tmp_path / "metadata.json").read_text(encoding="utf-8"))
    assert metadata["input_shape"] == [4, 8, 4]
    lines = (tmp_path / "test_vectors.txt").read_text(encoding="utf-8").splitlines()
    assert lines[0] == "# sample_index label sequence_length input_width"
    fields = lines[1].split()
    assert fields[2:4] == ["8", "4"]
    assert len(fields) == 12
    assert all(len(token) == 4 for token in fields[4:])
