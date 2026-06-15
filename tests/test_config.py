import json

import pytest

from tinysnnrfid.config import load_config


def test_load_default_config() -> None:
    config = load_config("configs/default.json")
    assert config["dataset"]["sequence_length"] == 32
    assert set(config["classifiers"]["enabled"]) == {
        "threshold",
        "fsm",
        "lut_like",
        "tiny_snn",
        "tiny_snn_v2",
    }
    assert config["classifiers"]["tiny_snn_v2"]["hidden_neurons"] == 6
    assert config["scenario"]["dense_noise_spike_threshold"] == 8
    assert config["scenario"]["force_minimum_per_scenario"] is False
    assert config["scenario_suite"]["mode"] == "legacy"


def test_load_temporal_hard_config() -> None:
    config = load_config("configs/temporal_hard.json")
    assert config["scenario_suite"]["mode"] == "temporal_hard"
    assert "long_gap_positive" in config["scenario_suite"]["mix"]


@pytest.mark.parametrize("field", ["noise_probability", "jitter_probability", "dropout_probability"])
def test_rejects_invalid_probability(tmp_path, field: str) -> None:
    path = tmp_path / "bad.json"
    path.write_text(json.dumps({"dataset": {field: 1.1}}), encoding="utf-8")
    with pytest.raises(ValueError, match=field):
        load_config(path)


def test_rejects_out_of_range_pattern(tmp_path) -> None:
    path = tmp_path / "bad.json"
    path.write_text(json.dumps({"dataset": {"input_width": 2, "valid_pattern": [0, 2]}}), encoding="utf-8")
    with pytest.raises(ValueError, match="valid_pattern"):
        load_config(path)


@pytest.mark.parametrize(
    ("scenario", "message"),
    [
        ({"dense_noise_spike_threshold": -1}, "dense_noise_spike_threshold"),
        ({"force_minimum_per_scenario": "false"}, "force_minimum_per_scenario"),
    ],
)
def test_rejects_invalid_scenario_config(tmp_path, scenario: dict, message: str) -> None:
    path = tmp_path / "bad.json"
    path.write_text(json.dumps({"scenario": scenario}), encoding="utf-8")
    with pytest.raises(ValueError, match=message):
        load_config(path)


@pytest.mark.parametrize(
    ("scenario_suite", "message"),
    [
        ({"mode": "unknown"}, "scenario_suite.mode"),
        ({"mode": "temporal_hard", "mix": {"bogus": 1.0}}, "mix key"),
        ({"mode": "temporal_hard", "mix": {"clean_positive": -1.0}}, "clean_positive"),
        ({"mode": "temporal_hard", "mix": {"clean_positive": 0.0}}, "sum"),
        ({"mode": "temporal_hard", "mix": {"clean_positive": 1.0}, "burst_length": 0}, "burst_length"),
        ({"mode": "temporal_hard", "mix": {"clean_positive": 1.0}, "allow_legacy_tags": "yes"}, "allow_legacy_tags"),
    ],
)
def test_rejects_invalid_scenario_suite_config(tmp_path, scenario_suite: dict, message: str) -> None:
    path = tmp_path / "bad_suite.json"
    path.write_text(json.dumps({"scenario_suite": scenario_suite}), encoding="utf-8")
    with pytest.raises(ValueError, match=message):
        load_config(path)
