from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import Any


KNOWN_CLASSIFIERS = {"threshold", "fsm", "lut_like", "tiny_snn", "tiny_snn_v2"}

DEFAULT_CONFIG: dict[str, Any] = {
    "dataset": {
        "num_samples": 1000,
        "sequence_length": 32,
        "input_width": 4,
        "positive_ratio": 0.5,
        "valid_pattern": [0, 1, 2],
        "noise_probability": 0.03,
        "jitter_probability": 0.2,
        "dropout_probability": 0.1,
        "max_jitter": 1,
        "max_gap": 5,
        "train_test_split": 0.8,
        "random_seed": 1234,
    },
    "classifiers": {
        "enabled": ["threshold", "fsm", "lut_like", "tiny_snn", "tiny_snn_v2"],
        "threshold": {"min_active_cycles": 3, "min_total_spikes": 3},
        "fsm": {"max_gap": 6},
        "lut_like": {"max_total_spikes": 10},
        "tiny_snn": {"threshold": 2, "leak": 1, "membrane_max": 7, "max_gap": 6},
        "tiny_snn_v2": {
            "hidden_neurons": 6,
            "hidden_threshold": 4,
            "output_threshold": 3,
            "leak": 1,
            "membrane_min": 0,
            "membrane_max": 7,
            "reset_on_spike": True,
            "input_weights": [
                [4, 0, 0, -1, 3, 0],
                [0, 3, 0, -1, 3, 3],
                [0, 0, 4, -1, 0, 3],
                [-1, -1, -1, 7, -2, -2],
            ],
            "output_weights": [-2, 0, 1, -3, 2, 2],
        },
    },
    "scenario": {"dense_noise_spike_threshold": 8, "force_minimum_per_scenario": False},
    "paths": {"data_dir": "data/generated", "results_dir": "results"},
}


def _merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _merge(result[key], value)
        else:
            result[key] = value
    return result


def load_config(path: str | Path) -> dict[str, Any]:
    """Load, merge, and validate a JSON or safely parsed YAML configuration."""
    config_path = Path(path)
    if not config_path.is_file():
        raise ValueError(f"Config file does not exist: {config_path}")
    try:
        if config_path.suffix.lower() == ".json":
            raw = json.loads(config_path.read_text(encoding="utf-8"))
        elif config_path.suffix.lower() in {".yaml", ".yml"}:
            try:
                import yaml  # type: ignore[import-not-found]
            except ImportError as exc:
                raise ValueError(
                    f"YAML config requires PyYAML; use a JSON config instead: {config_path}"
                ) from exc
            raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        else:
            raise ValueError(f"Config must be .json, .yaml, or .yml: {config_path}")
    except (json.JSONDecodeError, OSError) as exc:
        raise ValueError(f"Could not read config {config_path}: {exc}") from exc
    if not isinstance(raw, dict):
        raise ValueError(f"Config root must be an object: {config_path}")
    config = _merge(DEFAULT_CONFIG, raw)
    validate_config(config)
    return config


def validate_config(config: dict[str, Any]) -> None:
    """Validate benchmark configuration values and classifier names."""
    try:
        dataset = config["dataset"]
        classifiers = config["classifiers"]
        scenario = config["scenario"]
        paths = config["paths"]
    except KeyError as exc:
        raise ValueError(f"Missing required config field: {exc.args[0]}") from exc

    for field in ("num_samples", "sequence_length", "input_width"):
        if not isinstance(dataset.get(field), int) or dataset[field] <= 0:
            raise ValueError(f"dataset.{field} must be an integer greater than 0")
    for field in ("noise_probability", "jitter_probability", "dropout_probability", "positive_ratio"):
        value = dataset.get(field)
        if not isinstance(value, (int, float)) or not 0.0 <= value <= 1.0:
            raise ValueError(f"dataset.{field} must be within [0.0, 1.0]")
    split = dataset.get("train_test_split")
    if not isinstance(split, (int, float)) or not 0.0 < split < 1.0:
        raise ValueError("dataset.train_test_split must be greater than 0 and less than 1")
    pattern = dataset.get("valid_pattern")
    if not isinstance(pattern, list) or not pattern:
        raise ValueError("dataset.valid_pattern must be a non-empty list")
    width = dataset["input_width"]
    if any(not isinstance(channel, int) or channel < 0 or channel >= width for channel in pattern):
        raise ValueError(f"dataset.valid_pattern channels must be within [0, {width - 1}]")
    if dataset["sequence_length"] < len(pattern):
        raise ValueError("dataset.sequence_length must be at least the valid pattern length")
    for field in ("max_jitter", "max_gap"):
        if not isinstance(dataset.get(field), int) or dataset[field] < 0:
            raise ValueError(f"dataset.{field} must be a non-negative integer")
    enabled = classifiers.get("enabled")
    if not isinstance(enabled, list) or not enabled:
        raise ValueError("classifiers.enabled must be a non-empty list")
    unknown = sorted(set(enabled) - KNOWN_CLASSIFIERS)
    if unknown:
        raise ValueError(f"Unknown classifier name(s) in classifiers.enabled: {', '.join(unknown)}")
    dense_threshold = scenario.get("dense_noise_spike_threshold")
    if not isinstance(dense_threshold, int) or isinstance(dense_threshold, bool) or dense_threshold < 0:
        raise ValueError("scenario.dense_noise_spike_threshold must be a non-negative integer")
    if not isinstance(scenario.get("force_minimum_per_scenario"), bool):
        raise ValueError("scenario.force_minimum_per_scenario must be a boolean")
    _validate_tiny_snn_v2_config(classifiers.get("tiny_snn_v2", {}), dataset["input_width"])
    for field in ("data_dir", "results_dir"):
        if not isinstance(paths.get(field), str) or not paths[field].strip():
            raise ValueError(f"paths.{field} must be a non-empty string")


def _validate_tiny_snn_v2_config(settings: dict[str, Any], input_width: int) -> None:
    """Validate the fixed-weight hidden-layer SNN config without executing it."""
    for field in ("hidden_neurons", "hidden_threshold", "output_threshold"):
        value = settings.get(field)
        if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
            raise ValueError(f"classifiers.tiny_snn_v2.{field} must be a positive integer")
    leak = settings.get("leak")
    if not isinstance(leak, int) or isinstance(leak, bool) or leak < 0:
        raise ValueError("classifiers.tiny_snn_v2.leak must be a non-negative integer")
    membrane_min = settings.get("membrane_min")
    membrane_max = settings.get("membrane_max")
    if (
        not isinstance(membrane_min, int)
        or isinstance(membrane_min, bool)
        or not isinstance(membrane_max, int)
        or isinstance(membrane_max, bool)
        or membrane_min >= membrane_max
    ):
        raise ValueError(
            "classifiers.tiny_snn_v2.membrane_min and membrane_max must be integers with membrane_min < membrane_max"
        )
    if not isinstance(settings.get("reset_on_spike"), bool):
        raise ValueError("classifiers.tiny_snn_v2.reset_on_spike must be a boolean")
    hidden_neurons = settings["hidden_neurons"]
    input_weights = settings.get("input_weights")
    if (
        not isinstance(input_weights, list)
        or len(input_weights) != input_width
        or any(not isinstance(row, list) or len(row) != hidden_neurons for row in input_weights)
    ):
        raise ValueError(
            "classifiers.tiny_snn_v2.input_weights must have shape [input_width, hidden_neurons]"
        )
    if any(not isinstance(weight, int) or isinstance(weight, bool) for row in input_weights for weight in row):
        raise ValueError("classifiers.tiny_snn_v2.input_weights must contain only integers")
    output_weights = settings.get("output_weights")
    if not isinstance(output_weights, list) or len(output_weights) != hidden_neurons:
        raise ValueError("classifiers.tiny_snn_v2.output_weights must have length hidden_neurons")
    if any(not isinstance(weight, int) or isinstance(weight, bool) for weight in output_weights):
        raise ValueError("classifiers.tiny_snn_v2.output_weights must contain only integers")
