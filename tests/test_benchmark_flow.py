import json

from tinysnnrfid.config import DEFAULT_CONFIG
from tinysnnrfid.dataset import DatasetConfig, save_dataset
from tinysnnrfid.report import render_markdown_report
from tinysnnrfid.run_benchmark import run_benchmark


def test_end_to_end_benchmark(tmp_path) -> None:
    config = json.loads(json.dumps(DEFAULT_CONFIG))
    config["dataset"].update({"num_samples": 24, "sequence_length": 12, "random_seed": 9})
    data_dir = tmp_path / "data"
    results_dir = tmp_path / "results"
    save_dataset(
        data_dir,
        DatasetConfig.from_mapping(config["dataset"], config["scenario"], config.get("scenario_suite")),
        config,
    )
    results = run_benchmark(config, data_dir, results_dir)
    assert (results_dir / "benchmark_results.json").is_file()
    assert (results_dir / "benchmark_report.md").is_file()
    assert set(results["classifiers"]) == {"threshold", "fsm", "lut_like", "tiny_snn", "tiny_snn_v2"}
    for values in results["classifiers"].values():
        for metric in ("accuracy", "precision", "recall", "f1"):
            assert 0.0 <= values[metric] <= 1.0
        assert values["per_scenario"]
        assert sum(item["count"] for item in values["per_scenario"].values()) == 24
    assert "tiny_snn_v2" in results["classifiers"]
    assert results["classifiers"]["tiny_snn_v2"]["per_scenario"]
    report = render_markdown_report(results)
    assert "## Per-Scenario Metrics" in report
    assert "tiny_snn_v2" in report
    assert "not hardware conclusions" in report
