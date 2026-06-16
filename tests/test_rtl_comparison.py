from __future__ import annotations

import json

from tinysnnrfid.build_research_report import build_research_report
from tinysnnrfid.compare_rtl_designs import compare_rtl_designs


def write_json(path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def rtl_summary(snn_cells: int, fsm_cells: int = 100, sparse_cells: int = 120) -> dict:
    return {
        "simulations": {
            "threshold": {"found": True, "status": "pass"},
            "fsm": {"found": True, "status": "pass"},
            "lut_like": {"found": True, "status": "pass"},
            "tiny_snn_v2": {"found": True, "status": "pass"},
            "tiny_snn_v2_sparse_activity": {"found": True, "status": "pass"},
        },
        "synthesis": {
            "threshold": {"found": True, "status": "available", "cell_count": 80},
            "fsm": {"found": True, "status": "available", "cell_count": fsm_cells},
            "lut_like": {"found": True, "status": "available", "cell_count": 90},
            "tiny_snn_v2": {"found": True, "status": "available", "cell_count": snn_cells},
            "tiny_snn_v2_sparse_activity": {
                "found": True,
                "status": "available",
                "cell_count": sparse_cells,
            },
        },
    }


def activity_summary(snn_toggles: int, fsm_toggles: int = 1000, sparse_toggles: int = 1100) -> dict:
    return {
        "baselines": {
            "threshold": {"found": True, "status": "available", "total_toggles": 800},
            "fsm": {"found": True, "status": "available", "total_toggles": fsm_toggles},
            "lut_like": {"found": True, "status": "available", "total_toggles": 900},
            "tiny_snn_v2": {"found": True, "status": "available", "total_toggles": snn_toggles},
            "tiny_snn_v2_sparse_activity": {
                "found": True,
                "status": "available",
                "total_toggles": sparse_toggles,
            },
        }
    }


def write_inputs(
    tmp_path,
    snn_cells: int,
    snn_toggles: int,
    sparse_cells: int = 120,
    sparse_toggles: int = 1100,
) -> None:
    write_json(tmp_path / "rtl_summary.json", rtl_summary(snn_cells, sparse_cells=sparse_cells))
    write_json(
        tmp_path / "rtl_activity_summary.json",
        activity_summary(snn_toggles, sparse_toggles=sparse_toggles),
    )


def test_missing_inputs_produce_insufficient_rtl_data_and_outputs(tmp_path) -> None:
    summary = compare_rtl_designs(tmp_path)
    assert summary["recommendation"] == "insufficient_rtl_data"
    assert summary["inputs"]["rtl_summary"]["found"] is False
    assert (tmp_path / "rtl_comparison_summary.json").is_file()
    report = (tmp_path / "rtl_comparison_report.md").read_text(encoding="utf-8")
    assert "## Primary RTL Candidate Decision" in report
    assert "local-tool proxies" in report


def test_sparse_candidate_fields_and_low_ratios_recommend_continue_optimization(tmp_path) -> None:
    write_inputs(tmp_path, snn_cells=450, snn_toggles=5000, sparse_cells=150, sparse_toggles=1600)
    summary = compare_rtl_designs(tmp_path)
    assert summary["reference_design"] == "fsm"
    assert summary["candidate_design"] == "tiny_snn_v2_sparse_activity"
    assert summary["legacy_snn_design"] == "tiny_snn_v2"
    assert summary["recommendation"] == "continue_snn_rtl_optimization"
    assert summary["designs"]["tiny_snn_v2"]["cell_ratio_vs_fsm"] == 4.5
    assert summary["designs"]["tiny_snn_v2"]["toggle_ratio_vs_fsm"] == 5.0
    assert summary["designs"]["tiny_snn_v2_sparse_activity"]["cell_ratio_vs_fsm"] == 1.5
    assert summary["designs"]["tiny_snn_v2_sparse_activity"]["toggle_ratio_vs_fsm"] == 1.6
    assert summary["tiny_snn_v2_sparse_activity_context"]["simulation_passed"] is True
    report = (tmp_path / "rtl_comparison_report.md").read_text(encoding="utf-8")
    assert "Candidate design: `tiny_snn_v2_sparse_activity`" in report
    assert "Legacy/default SNN context: `tiny_snn_v2`" in report


def test_medium_ratios_recommend_optimize_before_more_features(tmp_path) -> None:
    write_inputs(tmp_path, snn_cells=100, snn_toggles=1000, sparse_cells=350, sparse_toggles=5000)
    summary = compare_rtl_designs(tmp_path)
    assert summary["recommendation"] == "optimize_snn_rtl_before_more_features"


def test_high_ratios_recommend_prioritize_baseline(tmp_path) -> None:
    write_inputs(tmp_path, snn_cells=100, snn_toggles=1000, sparse_cells=450, sparse_toggles=5000)
    summary = compare_rtl_designs(tmp_path)
    assert summary["recommendation"] == "prioritize_fsm_or_lut_rtl_baseline"


def test_legacy_snn_failure_does_not_block_sparse_candidate_decision(tmp_path) -> None:
    payload = rtl_summary(450, sparse_cells=150)
    payload["simulations"]["tiny_snn_v2"]["status"] = "fail"
    write_json(tmp_path / "rtl_summary.json", payload)
    write_json(tmp_path / "rtl_activity_summary.json", activity_summary(5000, sparse_toggles=1600))
    summary = compare_rtl_designs(tmp_path)
    assert summary["recommendation"] == "continue_snn_rtl_optimization"
    assert summary["tiny_snn_v2_context"]["simulation_passed"] is False
    assert summary["tiny_snn_v2_sparse_activity_context"]["simulation_passed"] is True


def test_sparse_candidate_nonpassing_simulation_is_insufficient_data(tmp_path) -> None:
    payload = rtl_summary(100, sparse_cells=100)
    payload["simulations"]["tiny_snn_v2_sparse_activity"]["status"] = "fail"
    write_json(tmp_path / "rtl_summary.json", payload)
    write_json(tmp_path / "rtl_activity_summary.json", activity_summary(1000, sparse_toggles=1000))
    summary = compare_rtl_designs(tmp_path)
    assert summary["recommendation"] == "insufficient_rtl_data"
    assert "tiny_snn_v2_sparse_activity simulation" in summary["reason"]


def test_research_report_shows_sparse_candidate_design(tmp_path) -> None:
    input_dir = tmp_path / "rtl"
    write_inputs(input_dir, snn_cells=450, snn_toggles=5000, sparse_cells=150, sparse_toggles=1600)
    compare_rtl_designs(input_dir)
    paths = {
        "legacy_benchmark": tmp_path / "missing_benchmark.json",
        "legacy_sweep": tmp_path / "missing_sweep.json",
        "legacy_snn_search": tmp_path / "missing_search.json",
        "temporal_sweep": tmp_path / "missing_temporal_sweep.json",
        "temporal_snn_search": tmp_path / "missing_temporal_search.json",
        "rtl_comparison": input_dir / "rtl_comparison_summary.json",
    }

    summary = build_research_report(tmp_path / "report", input_paths=paths)

    assert summary["evidence"]["rtl_comparison"]["candidate_design"] == "tiny_snn_v2_sparse_activity"
    report = (tmp_path / "report" / "research_decision_report.md").read_text(encoding="utf-8")
    assert "Candidate design: `tiny_snn_v2_sparse_activity`" in report
    assert "Legacy/default SNN context: `tiny_snn_v2`" in report
