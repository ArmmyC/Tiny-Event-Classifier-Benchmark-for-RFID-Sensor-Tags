import json

import numpy as np
import pytest

from tinysnnrfid.classifiers import TinySNNV2Classifier
from tinysnnrfid.config import DEFAULT_CONFIG, load_config


def ordered_and_reversed_inputs() -> np.ndarray:
    ordered = np.zeros((8, 4), dtype=np.uint8)
    ordered[1, 0] = 1
    ordered[3, 1] = 1
    ordered[5, 2] = 1

    reversed_sequence = np.zeros((8, 4), dtype=np.uint8)
    reversed_sequence[1, 2] = 1
    reversed_sequence[3, 1] = 1
    reversed_sequence[5, 0] = 1
    return np.stack([ordered, reversed_sequence])


def test_tiny_snn_v2_default_predictions_are_binary_and_deterministic() -> None:
    model = TinySNNV2Classifier()
    inputs = ordered_and_reversed_inputs()
    first = model.predict(inputs)
    second = model.predict(inputs)
    np.testing.assert_array_equal(first, second)
    assert first.shape == (2,)
    assert set(first.tolist()) <= {0, 1}
    assert first.tolist() == [1, 0]


def test_tiny_snn_v2_empty_sequence_returns_zero() -> None:
    model = TinySNNV2Classifier()
    inputs = np.zeros((1, 8, 4), dtype=np.uint8)
    assert model.predict(inputs).tolist() == [0]


def test_tiny_snn_v2_dense_noise_does_not_always_fire() -> None:
    model = TinySNNV2Classifier()
    inputs = np.ones((3, 8, 4), dtype=np.uint8)
    assert model.predict(inputs).tolist() != [1, 1, 1]


def test_tiny_snn_v2_activity_proxy_fields() -> None:
    model = TinySNNV2Classifier()
    proxy = model.activity_proxy(ordered_and_reversed_inputs())
    for field in (
        "software_proxy_total_operations",
        "software_proxy_mean_operations",
        "software_proxy_max_operations",
        "input_spike_processing",
        "hidden_updates",
        "output_updates",
        "hidden_spikes",
        "output_spikes",
    ):
        assert field in proxy
    assert proxy["software_proxy_total_operations"] > 0


def test_tiny_snn_v2_has_no_fsm_progress_field() -> None:
    model = TinySNNV2Classifier()
    assert "progress" not in model.__dict__


@pytest.mark.parametrize(
    "kwargs, message",
    [
        ({"hidden_neurons": 0}, "hidden_neurons"),
        ({"hidden_threshold": 0}, "hidden_threshold"),
        ({"output_threshold": 0}, "output_threshold"),
        ({"leak": -1}, "leak"),
        ({"membrane_min": 3, "membrane_max": 3}, "membrane_min"),
        ({"reset_on_spike": 1}, "reset_on_spike"),
        ({"input_weights": [[1, 2, 3]]}, "input_weights"),
        ({"output_weights": [1, 2]}, "output_weights"),
        ({"input_weights": [[1.5, 0, 0, 0, 0, 0]] * 4}, "input_weights"),
        ({"output_weights": [1, 0, 1, -3, 2.5, 2]}, "output_weights"),
    ],
)
def test_tiny_snn_v2_rejects_invalid_constructor_config(kwargs: dict, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        TinySNNV2Classifier(**kwargs)


@pytest.mark.parametrize(
    "patch",
    [
        {"hidden_neurons": 0},
        {"hidden_threshold": 0},
        {"output_threshold": 0},
        {"leak": -1},
        {"membrane_min": 7, "membrane_max": 7},
        {"reset_on_spike": "yes"},
        {"input_weights": [[1, 2, 3]]},
        {"output_weights": [1, 2]},
        {"input_weights": [[1.5, 0, 0, 0, 0, 0]] * 4},
        {"output_weights": [1, 0, 1, -3, 2.5, 2]},
    ],
)
def test_tiny_snn_v2_config_validation_rejects_invalid_values(tmp_path, patch: dict) -> None:
    config = json.loads(json.dumps(DEFAULT_CONFIG))
    config["classifiers"]["tiny_snn_v2"].update(patch)
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(config), encoding="utf-8")
    with pytest.raises(ValueError, match="tiny_snn_v2"):
        load_config(path)
