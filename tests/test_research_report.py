import json

import pytest

from tinysnnrfid.build_research_report import (
    EXPECTED_INPUTS,
    build_research_report,
    choose_recommendation,
)


def write_json(path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def input_paths(tmp_path) -> dict[str, object]:
    return {name: tmp_path / path.name for name, path in EXPECTED_INPUTS.items()}


def test_missing_inputs_produce_insufficient_data_and_outputs(tmp_path) -> None:
    paths = input_paths(tmp_path)
    output_dir = tmp_path / "output"
    summary = build_research_report(output_dir, input_paths=paths)
    assert summary["recommendation"] == "insufficient_data"
    assert len(summary["missing_inputs"]) == len(paths)
    assert (output_dir / "research_decision_summary.json").is_file()
    report_path = output_dir / "research_decision_report.md"
    assert report_path.is_file()
    report = report_path.read_text(encoding="utf-8")
    assert "Missing inputs:" in report
    assert "## RTL Baseline Evidence" in report
    assert "RTL summary not available" in report
    assert "software operation proxies, not hardware power" in report


def test_strict_mode_rejects_missing_inputs(tmp_path) -> None:
    with pytest.raises(ValueError, match="Missing required research input"):
        build_research_report(tmp_path / "output", strict=True, input_paths=input_paths(tmp_path))


def test_continue_search_recommendation_drives_final_decision() -> None:
    evidence = {
        "legacy_snn_search": {
            "kind": "search",
            "recommendation": "continue_snn_optimization",
        }
    }
    recommendation, reason = choose_recommendation(evidence)
    assert recommendation == "continue_snn_optimization"
    assert "SNN search" in reason


def test_missing_temporal_evidence_recommends_harder_scenarios() -> None:
    evidence = {
        "legacy_sweep": {
            "kind": "sweep",
            "recommendation": "prioritize_fsm_or_lut_rtl_baseline",
        },
        "legacy_snn_search": {
            "kind": "search",
            "recommendation": "prioritize_fsm_or_lut_rtl_baseline",
        },
    }
    recommendation, reason = choose_recommendation(evidence)
    assert recommendation == "add_harder_temporal_scenarios"
    assert "temporal-hard" in reason


def test_fsm_dominant_temporal_evidence_prioritizes_baseline() -> None:
    evidence = {
        "temporal_sweep": {
            "kind": "sweep",
            "recommendation": "add_harder_temporal_scenarios",
            "best_overall_classifier": "lut_like",
            "competitive_run_count": 0,
        },
        "temporal_snn_search": {
            "kind": "search",
            "recommendation": "prioritize_fsm_or_lut_rtl_baseline",
        },
    }
    recommendation, reason = choose_recommendation(evidence)
    assert recommendation == "prioritize_fsm_or_lut_rtl_baseline"
    assert "temporal-hard" in reason


def test_report_extracts_synthetic_inputs_and_writes_sections(tmp_path) -> None:
    paths = input_paths(tmp_path)
    write_json(paths["legacy_benchmark"], benchmark_payload())
    write_json(paths["legacy_sweep"], sweep_payload("add_harder_temporal_scenarios", "fsm"))
    write_json(paths["legacy_snn_search"], search_payload("prioritize_fsm_or_lut_rtl_baseline"))
    write_json(paths["temporal_sweep"], sweep_payload("add_harder_temporal_scenarios", "lut_like"))
    write_json(paths["temporal_snn_search"], search_payload("prioritize_fsm_or_lut_rtl_baseline"))
    write_json(paths["rtl_baselines"], rtl_payload())
    output_dir = tmp_path / "output"
    summary = build_research_report(output_dir, strict=True, input_paths=paths)
    assert summary["recommendation"] == "prioritize_fsm_or_lut_rtl_baseline"
    assert summary["missing_inputs"] == []
    report = (output_dir / "research_decision_report.md").read_text(encoding="utf-8")
    for section in (
        "## Inputs Found",
        "## Executive Recommendation",
        "## Legacy Benchmark Evidence",
        "## Legacy Sweep Evidence",
        "## Legacy SNN Search Evidence",
        "## Temporal-Hard Sweep Evidence",
        "## Temporal-Hard SNN Search Evidence",
        "## RTL Baseline Evidence",
        "## Scenario-Level Findings",
        "## Decision Matrix",
        "## Notes and Limitations",
    ):
        assert section in report


def test_research_report_loads_rtl_summary_when_present(tmp_path) -> None:
    paths = input_paths(tmp_path)
    write_json(
        paths["rtl_baselines"],
        {
            "simulations": {"threshold": {"found": True, "status": "pass", "passed": 3, "failed": 0}},
            "synthesis": {"threshold": {"found": True, "status": "available", "cell_count": 12}},
            "recommendation_context": {"lowest_cell_count_baseline": "threshold"},
            "note": "not silicon signoff",
        },
    )
    summary = build_research_report(tmp_path / "output", input_paths=paths)
    assert summary["inputs"]["rtl_baselines"]["found"] is True
    assert summary["evidence"]["rtl_baselines"]["synthesis"]["threshold"]["cell_count"] == 12
    report = (tmp_path / "output" / "research_decision_report.md").read_text(encoding="utf-8")
    assert "## RTL Baseline Evidence" in report
    assert "not silicon signoff" in report


def benchmark_payload() -> dict:
    return {
        "classifiers": {
            "fsm": {
                "f1": 0.9,
                "accuracy": 0.9,
                "activity_proxy": {"software_proxy_mean_operations": 10},
                "per_scenario": {"clean_positive": {"f1": 1.0, "accuracy": 1.0}},
            },
            "tiny_snn_v2": {
                "f1": 0.7,
                "accuracy": 0.75,
                "activity_proxy": {"software_proxy_mean_operations": 20},
                "per_scenario": {"clean_positive": {"f1": 0.8, "accuracy": 0.8}},
            },
        }
    }


def sweep_payload(recommendation: str, best_classifier: str) -> dict:
    return {
        "decision": {
            "recommendation": recommendation,
            "reason": "synthetic sweep",
            "best_overall_classifier": best_classifier,
            "competitive_run_count": 0,
        },
        "comparison": {
            "candidate_f1_wins": 0,
            "candidate_activity_wins_within_f1_tolerance": 0,
            "competitive_runs": [],
        },
        "aggregate": {
            "best_by_scenario": {
                "clean_positive": {"classifier": best_classifier, "mean_f1": 1.0}
            }
        },
    }


def search_payload(recommendation: str) -> dict:
    return {
        "decision": {
            "recommendation": recommendation,
            "reason": "synthetic search",
            "best_candidate_id": "candidate_0000",
            "best_weight_variant": "current_default",
            "competitive_candidate_count": 0,
            "f1_win_count": 0,
            "activity_win_within_tolerance_count": 0,
        },
        "selection": {
            "strategy": "balanced_round_robin",
            "full_grid_candidate_count": 100,
            "evaluated_candidate_count": 10,
            "coverage": {},
        },
        "aggregate": {
            "best_candidate_by_scenario": {
                "clean_positive": {
                    "candidate_id": "candidate_0000",
                    "weight_variant": "current_default",
                    "f1": 0.8,
                }
            }
        },
    }


def rtl_payload() -> dict:
    return {
        "simulations": {
            "threshold": {"found": True, "status": "pass", "passed": 3, "failed": 0},
            "fsm": {"found": False, "status": "missing"},
            "lut_like": {"found": False, "status": "missing"},
        },
        "synthesis": {
            "threshold": {"found": True, "status": "available", "cell_count": 12},
            "fsm": {"found": False, "status": "missing"},
            "lut_like": {"found": False, "status": "missing"},
        },
        "recommendation_context": {"lowest_cell_count_baseline": "threshold"},
        "note": "Open-source RTL results are not silicon signoff.",
    }
