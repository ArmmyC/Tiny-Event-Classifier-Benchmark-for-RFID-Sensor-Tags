import json

import pytest

from tinysnnrfid.config import DEFAULT_CONFIG
from tinysnnrfid.run_sweep import (
    apply_sweep_config,
    expand_sweep_grid,
    load_sweep_config,
    render_sweep_report,
    run_sweep,
    set_dotted_path,
)


def write_json(path, payload: dict) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def tiny_sweep_config(tmp_path) -> dict:
    base_config = json.loads(json.dumps(DEFAULT_CONFIG))
    base_config["dataset"].update({"num_samples": 16, "sequence_length": 10})
    base_path = tmp_path / "base.json"
    write_json(base_path, base_config)
    return {
        "name": "tiny",
        "base_config": str(base_path),
        "output_dir": str(tmp_path / "sweeps"),
        "dataset_output_root": str(tmp_path / "sweeps" / "generated"),
        "seeds": [11],
        "overrides": {"dataset.num_samples": 16},
        "parameters": {
            "dataset.noise_probability": [0.0, 0.1],
            "dataset.jitter_probability": [0.0],
            "dataset.dropout_probability": [0.0],
            "scenario.dense_noise_spike_threshold": [8],
        },
        "comparison": {
            "reference_classifier": "fsm",
            "candidate_classifier": "tiny_snn_v2",
        },
    }


def test_load_sweep_config(tmp_path) -> None:
    config = tiny_sweep_config(tmp_path)
    path = tmp_path / "sweep.json"
    write_json(path, config)
    loaded = load_sweep_config(path)
    assert loaded["name"] == "tiny"
    assert loaded["parameters"]["dataset.noise_probability"] == [0.0, 0.1]


@pytest.mark.parametrize(
    "patch, message",
    [
        ({"seeds": []}, "seeds"),
        ({"base_config": "missing.json"}, "base_config"),
        ({"parameters": {"dataset.noise_probability": []}}, "noise_probability"),
        ({"parameters": {"dataset.noise_probability": [1.1]}}, "probabilities"),
        ({"parameters": {"dataset.unknown": [0.1]}}, "Unsupported"),
    ],
)
def test_load_sweep_config_rejects_invalid_values(tmp_path, patch: dict, message: str) -> None:
    config = tiny_sweep_config(tmp_path)
    config.update(patch)
    path = tmp_path / "bad.json"
    write_json(path, config)
    with pytest.raises(ValueError, match=message):
        load_sweep_config(path)


def test_set_dotted_path_and_apply_sweep_config() -> None:
    config = json.loads(json.dumps(DEFAULT_CONFIG))
    set_dotted_path(config, "dataset.noise_probability", 0.2)
    assert config["dataset"]["noise_probability"] == 0.2
    point = {
        "run_id": "run_0000",
        "seed": 7,
        "parameters": {"dataset.dropout_probability": 0.0},
    }
    effective = apply_sweep_config(config, point, {"dataset.num_samples": 12})
    assert effective["dataset"]["num_samples"] == 12
    assert effective["dataset"]["random_seed"] == 7
    assert effective["dataset"]["dropout_probability"] == 0.0


def test_expand_sweep_grid_count_and_stable_ids(tmp_path) -> None:
    config = tiny_sweep_config(tmp_path)
    config["seeds"] = [1, 2]
    points = expand_sweep_grid(config)
    assert len(points) == 4
    assert [point["run_id"] for point in points] == ["run_0000", "run_0001", "run_0002", "run_0003"]


def test_deterministic_small_sweep_and_output_schema(tmp_path) -> None:
    config = tiny_sweep_config(tmp_path)
    first = run_sweep(config)
    second = run_sweep(config)
    assert first["sweep"]["run_count"] == 2
    assert [run["parameters"] for run in first["runs"]] == [run["parameters"] for run in second["runs"]]
    assert first["aggregate"] == second["aggregate"]
    assert (tmp_path / "sweeps" / "sweep_results.json").is_file()
    assert (tmp_path / "sweeps" / "sweep_report.md").is_file()
    for run in first["runs"]:
        assert "dataset" in run
        assert "classifiers" in run
        assert "tiny_snn_v2" in run["classifiers"]
        assert run["classifiers"]["tiny_snn_v2"]["per_scenario"]
        assert run["classifiers"]["tiny_snn_v2"]["activity_proxy"]
    assert "by_classifier" in first["aggregate"]
    assert "best_by_scenario" in first["aggregate"]
    assert first["comparison"]["candidate_classifier"] == "tiny_snn_v2"


def test_markdown_report_contains_required_sections(tmp_path) -> None:
    results = run_sweep(tiny_sweep_config(tmp_path))
    report = render_sweep_report(results)
    assert "Best Classifier By Sweep Point" in report
    assert "Best Classifier By Scenario" in report
    assert "tiny_snn_v2 vs fsm" in report
    assert "Cases Where tiny_snn_v2 Wins" in report
    assert "Cases Where tiny_snn_v2 Loses" in report
    assert "not hardware power" in report
