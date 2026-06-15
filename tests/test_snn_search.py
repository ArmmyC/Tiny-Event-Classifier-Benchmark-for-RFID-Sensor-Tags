import csv
import json

import pytest

from tinysnnrfid.config import DEFAULT_CONFIG
from tinysnnrfid.run_snn_search import (
    RECOMMENDATIONS,
    WEIGHT_VARIANTS,
    build_search_decision,
    expand_candidate_grid,
    load_search_config,
    run_snn_search,
)


REQUIRED_CSV_COLUMNS = {
    "candidate_id",
    "seed",
    "weight_variant",
    "hidden_threshold",
    "output_threshold",
    "leak",
    "reset_on_spike",
    "noise_probability",
    "jitter_probability",
    "dropout_probability",
    "candidate_f1",
    "reference_f1",
    "f1_delta",
    "candidate_accuracy",
    "reference_accuracy",
    "candidate_activity",
    "reference_activity",
    "activity_delta",
    "competitive_reason",
    "recommendation",
}


def write_json(path, payload: dict) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def tiny_search_config(tmp_path) -> dict:
    base_config = json.loads(json.dumps(DEFAULT_CONFIG))
    base_config["dataset"].update({"num_samples": 16, "sequence_length": 10})
    base_path = tmp_path / "base.json"
    write_json(base_path, base_config)
    return {
        "name": "tiny_search",
        "base_config": str(base_path),
        "output_dir": str(tmp_path / "snn_search"),
        "dataset_output_root": str(tmp_path / "snn_search" / "generated"),
        "seeds": [7],
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
            "classifiers.tiny_snn_v2.reset_on_spike": [True, False],
        },
        "weight_variants": ["ternary_event_order", "balanced_small_int"],
        "comparison": {
            "reference_classifier": "fsm",
            "candidate_classifier": "tiny_snn_v2",
            "f1_tolerance": 0.03,
        },
        "limits": {"max_candidates": 3},
    }


def test_load_search_config(tmp_path) -> None:
    config = tiny_search_config(tmp_path)
    path = tmp_path / "search.json"
    write_json(path, config)
    loaded = load_search_config(path)
    assert loaded["name"] == "tiny_search"
    assert loaded["comparison"]["f1_tolerance"] == 0.03


def test_load_search_config_rejects_invalid_weight_variant(tmp_path) -> None:
    config = tiny_search_config(tmp_path)
    config["weight_variants"] = ["missing_variant"]
    path = tmp_path / "bad_search.json"
    write_json(path, config)
    with pytest.raises(ValueError, match="Unknown weight variant"):
        load_search_config(path)


def test_expand_candidate_grid_is_deterministic_and_limited(tmp_path) -> None:
    config = tiny_search_config(tmp_path)
    first = expand_candidate_grid(config)
    second = expand_candidate_grid(config)
    assert first == second
    assert len(first) == 3
    assert [candidate["candidate_id"] for candidate in first] == [
        "candidate_0000",
        "candidate_0001",
        "candidate_0002",
    ]
    assert {candidate["weight_variant"] for candidate in first} == {
        "ternary_event_order",
        "balanced_small_int",
    }


def test_weight_variants_are_integer_and_include_required_precision() -> None:
    assert {
        "current_default",
        "ternary_event_order",
        "ternary_noise_guard",
        "low_activity_sparse",
        "balanced_small_int",
    } <= set(WEIGHT_VARIANTS)
    ternary_variants = []
    small_int_variants = []
    for name, variant in WEIGHT_VARIANTS.items():
        weights = [weight for row in variant["input_weights"] for weight in row] + variant["output_weights"]
        assert all(isinstance(weight, int) for weight in weights)
        if set(weights) <= {-1, 0, 1}:
            ternary_variants.append(name)
        if all(-2 <= weight <= 2 for weight in weights):
            small_int_variants.append(name)
    assert ternary_variants
    assert "balanced_small_int" in small_int_variants


def test_run_snn_search_writes_outputs_and_schema(tmp_path) -> None:
    results = run_snn_search(tiny_search_config(tmp_path))
    output_dir = tmp_path / "snn_search"
    assert (output_dir / "search_results.json").is_file()
    assert (output_dir / "search_summary.csv").is_file()
    assert (output_dir / "search_report.md").is_file()
    assert results["search"]["candidate_count"] == 3
    assert len(results["runs"]) == 3
    assert "threshold" in results["runs"][0]["classifiers"]
    assert "fsm" in results["runs"][0]["classifiers"]
    assert "tiny_snn_v2" in results["runs"][0]["classifiers"]
    assert results["runs"][0]["comparison"]["competitive_reason"] in {
        "f1_win",
        "activity_win_within_f1_tolerance",
        "not_competitive",
        "missing_classifier",
    }
    assert results["decision"]["recommendation"] in RECOMMENDATIONS
    assert isinstance(results["decision"]["reason"], str)
    with (output_dir / "search_summary.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 3
    assert REQUIRED_CSV_COLUMNS <= set(rows[0])
    report = (output_dir / "search_report.md").read_text(encoding="utf-8")
    for section in (
        "# Tiny SNN v2 Parameter Search Report",
        "## Search Setup",
        "## Top Candidates By F1",
        "## Lower-Activity Competitive Candidates",
        "## Best Candidate By Scenario",
        "## Weight Variant Summary",
        "## Decision Summary",
        "## Notes and Limitations",
    ):
        assert section in report
    assert "not hardware power" in report


def test_search_decision_recommendation_branches() -> None:
    aggregate = {"best_candidate_by_scenario": {}}
    f1_win = [_decision_run("f1_win", f1_delta=0.1)]
    assert build_search_decision(f1_win, aggregate, 0.03)["recommendation"] == "continue_snn_optimization"

    activity_win = [_decision_run("activity_win_within_f1_tolerance", f1_delta=-0.01)]
    assert build_search_decision(activity_win, aggregate, 0.03)["recommendation"] == "continue_snn_optimization"

    close = [_decision_run("not_competitive", f1_delta=-0.01)]
    assert build_search_decision(close, aggregate, 0.03)["recommendation"] == "add_harder_temporal_scenarios"

    far = [_decision_run("not_competitive", f1_delta=-0.2)]
    assert build_search_decision(far, aggregate, 0.03)["recommendation"] == "prioritize_fsm_or_lut_rtl_baseline"


def _decision_run(reason: str, f1_delta: float) -> dict:
    candidate_f1 = 0.8 + f1_delta
    return {
        "candidate_id": "candidate_x",
        "weight_variant": "ternary_event_order",
        "classifiers": {"tiny_snn_v2": {"accuracy": candidate_f1}},
        "comparison": {
            "candidate_f1": candidate_f1,
            "reference_f1": 0.8,
            "f1_delta": f1_delta,
            "candidate_activity": 10.0,
            "reference_activity": 12.0,
            "activity_delta": -2.0,
            "competitive": reason != "not_competitive",
            "competitive_reason": reason,
        },
    }
