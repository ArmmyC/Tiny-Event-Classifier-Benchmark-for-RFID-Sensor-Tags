import json

from tinysnnrfid.config import load_config
from tinysnnrfid.run_snn_search import load_search_config, run_snn_search
from tinysnnrfid.run_sweep import load_sweep_config, run_sweep


def write_json(path, payload: dict) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_temporal_evaluation_configs_load() -> None:
    sweep = load_sweep_config("configs/sweep_temporal_hard.json")
    search = load_search_config("configs/snn_search_temporal_hard.json")
    assert sweep["base_config"] == "configs/temporal_hard.json"
    assert sweep["output_dir"] == "results/temporal_sweeps"
    assert search["base_config"] == "configs/temporal_hard.json"
    assert search["output_dir"] == "results/temporal_snn_search"
    assert load_config(sweep["base_config"])["scenario_suite"]["mode"] == "temporal_hard"
    assert load_config(search["base_config"])["scenario_suite"]["mode"] == "temporal_hard"


def test_tiny_temporal_sweep_integration(tmp_path) -> None:
    base_path = write_tiny_temporal_base(tmp_path)
    output_dir = tmp_path / "temporal_sweeps"
    config = {
        "name": "tiny_temporal_sweep",
        "base_config": str(base_path),
        "output_dir": str(output_dir),
        "dataset_output_root": str(output_dir / "generated"),
        "seeds": [31],
        "overrides": {"dataset.num_samples": 16},
        "parameters": {
            "dataset.noise_probability": [0.0],
            "dataset.jitter_probability": [0.0],
            "dataset.dropout_probability": [0.0],
        },
        "comparison": {
            "reference_classifier": "fsm",
            "candidate_classifier": "tiny_snn_v2",
            "f1_tolerance": 0.03,
        },
    }
    results = run_sweep(config)
    assert results["sweep"]["run_count"] == 1
    assert (output_dir / "sweep_results.json").is_file()
    assert (output_dir / "sweep_summary.csv").is_file()
    assert (output_dir / "sweep_report.md").is_file()
    scenarios = results["runs"][0]["classifiers"]["fsm"]["per_scenario"]
    assert "long_gap_positive" in scenarios
    assert "near_miss_negative" in scenarios


def test_tiny_temporal_snn_search_integration(tmp_path) -> None:
    base_path = write_tiny_temporal_base(tmp_path)
    output_dir = tmp_path / "temporal_snn_search"
    config = {
        "name": "tiny_temporal_search",
        "base_config": str(base_path),
        "output_dir": str(output_dir),
        "dataset_output_root": str(output_dir / "generated"),
        "seeds": [31],
        "dataset_overrides": {"dataset.num_samples": 16},
        "dataset_parameters": {
            "dataset.noise_probability": [0.0],
            "dataset.jitter_probability": [0.0],
            "dataset.dropout_probability": [0.0],
        },
        "snn_parameters": {
            "classifiers.tiny_snn_v2.hidden_threshold": [3],
            "classifiers.tiny_snn_v2.output_threshold": [2],
            "classifiers.tiny_snn_v2.leak": [0],
            "classifiers.tiny_snn_v2.reset_on_spike": [True],
        },
        "weight_variants": ["current_default", "ternary_event_order"],
        "comparison": {
            "reference_classifier": "fsm",
            "candidate_classifier": "tiny_snn_v2",
            "f1_tolerance": 0.03,
        },
        "selection": {"strategy": "balanced_round_robin"},
        "limits": {"max_candidates": 2},
    }
    results = run_snn_search(config)
    assert results["search"]["candidate_count"] == 2
    assert (output_dir / "search_results.json").is_file()
    assert (output_dir / "search_summary.csv").is_file()
    assert (output_dir / "search_report.md").is_file()
    scenarios = results["runs"][0]["classifiers"]["fsm"]["per_scenario"]
    assert "long_gap_positive" in scenarios
    assert "near_miss_negative" in scenarios


def write_tiny_temporal_base(tmp_path):
    config = load_config("configs/temporal_hard.json")
    config["dataset"].update({"num_samples": 16, "sequence_length": 40, "random_seed": 31})
    config["scenario_suite"]["mix"] = {
        "clean_positive": 1.0,
        "long_gap_positive": 1.0,
        "distractor_positive": 1.0,
        "dropout_positive": 1.0,
        "reversed_negative": 1.0,
        "partial_order_negative": 1.0,
        "burst_noise_negative": 1.0,
        "near_miss_negative": 1.0,
    }
    path = tmp_path / "temporal_base.json"
    write_json(path, config)
    return path
