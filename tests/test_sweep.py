import csv
import json

import pytest

from tinysnnrfid.config import DEFAULT_CONFIG
from tinysnnrfid.run_sweep import (
    apply_sweep_config,
    compare_candidate_to_reference,
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
            "f1_tolerance": 0.05,
        },
    }


def test_load_sweep_config(tmp_path) -> None:
    config = tiny_sweep_config(tmp_path)
    path = tmp_path / "sweep.json"
    write_json(path, config)
    loaded = load_sweep_config(path)
    assert loaded["name"] == "tiny"
    assert loaded["parameters"]["dataset.noise_probability"] == [0.0, 0.1]
    assert loaded["comparison"]["f1_tolerance"] == 0.05


@pytest.mark.parametrize(
    "patch, message",
    [
        ({"seeds": []}, "seeds"),
        ({"base_config": "missing.json"}, "base_config"),
        ({"parameters": {"dataset.noise_probability": []}}, "noise_probability"),
        ({"parameters": {"dataset.noise_probability": [1.1]}}, "probabilities"),
        ({"parameters": {"dataset.unknown": [0.1]}}, "Unsupported"),
        ({"comparison": {"reference_classifier": "fsm", "candidate_classifier": "tiny_snn_v2", "f1_tolerance": -0.1}}, "f1_tolerance"),
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
    assert (tmp_path / "sweeps" / "sweep_summary.csv").is_file()
    assert (tmp_path / "sweeps" / "sweep_report.md").is_file()
    with (tmp_path / "sweeps" / "sweep_summary.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == first["sweep"]["run_count"] * len(first["runs"][0]["classifiers"])
    assert {"run_id", "seed", "classifier", "f1", "software_proxy_mean_operations"} <= set(rows[0])
    for run in first["runs"]:
        assert "dataset" in run
        assert "classifiers" in run
        assert "tiny_snn_v2" in run["classifiers"]
        assert run["classifiers"]["tiny_snn_v2"]["per_scenario"]
        assert run["classifiers"]["tiny_snn_v2"]["activity_proxy"]
    assert "by_classifier" in first["aggregate"]
    assert "best_by_scenario" in first["aggregate"]
    assert first["comparison"]["candidate_classifier"] == "tiny_snn_v2"
    assert first["comparison"]["f1_tolerance"] == 0.05
    for field in (
        "candidate_f1_wins",
        "candidate_f1_losses",
        "candidate_f1_ties_within_tolerance",
        "candidate_activity_wins",
        "candidate_activity_wins_within_f1_tolerance",
        "competitive_runs",
    ):
        assert field in first["comparison"]
    assert "decision" in first
    assert first["decision"]["activity_note"].startswith("Activity metrics are software operation proxies")


def test_compare_candidate_to_reference_uses_f1_tolerance_and_activity() -> None:
    runs = [
        _comparison_run("win", 0.90, 0.80, 30, 50),
        _comparison_run("loss", 0.70, 0.90, 20, 10),
        _comparison_run("tie_activity", 0.86, 0.88, 12, 40),
    ]
    comparison = compare_candidate_to_reference(runs, "tiny_snn_v2", "fsm", f1_tolerance=0.03)
    assert comparison["candidate_f1_wins"] == 1
    assert comparison["candidate_f1_losses"] == 1
    assert comparison["candidate_f1_ties_within_tolerance"] == 1
    assert comparison["candidate_activity_wins"] == 2
    assert comparison["candidate_activity_wins_within_f1_tolerance"] == 2
    assert [row["run_id"] for row in comparison["competitive_runs"]] == ["win", "tie_activity"]
    tie_row = next(row for row in comparison["rows"] if row["run_id"] == "tie_activity")
    assert tie_row["f1_outcome"] == "tie_within_tolerance"
    assert tie_row["activity_outcome"] == "win"
    assert tie_row["competitive"] is True


def test_markdown_report_contains_required_sections(tmp_path) -> None:
    results = run_sweep(tiny_sweep_config(tmp_path))
    report = render_sweep_report(results)
    assert "Best Classifier By Sweep Point" in report
    assert "Best Classifier By Scenario" in report
    assert "tiny_snn_v2 vs fsm" in report
    assert "Cases Where tiny_snn_v2 Wins" in report
    assert "Cases Where tiny_snn_v2 Loses" in report
    assert "Competitive Cases" in report
    assert "Decision Summary" in report
    assert "F1 ties within tolerance" in report
    assert "activity wins within F1 tolerance" in report
    assert "not hardware power" in report


def _comparison_run(
    run_id: str,
    candidate_f1: float,
    reference_f1: float,
    candidate_activity: float,
    reference_activity: float,
) -> dict:
    return {
        "run_id": run_id,
        "seed": 1,
        "parameters": {"dataset.noise_probability": 0.0},
        "classifiers": {
            "tiny_snn_v2": {
                "f1": candidate_f1,
                "activity_proxy": {"software_proxy_mean_operations": candidate_activity},
            },
            "fsm": {
                "f1": reference_f1,
                "activity_proxy": {"software_proxy_mean_operations": reference_activity},
            },
        },
    }
