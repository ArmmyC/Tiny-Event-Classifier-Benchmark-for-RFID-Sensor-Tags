from __future__ import annotations

import json

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


def write_inputs(tmp_path, snn_cells: int, snn_toggles: int) -> None:
    write_json(tmp_path / "rtl_summary.json", rtl_summary(snn_cells))
    write_json(tmp_path / "rtl_activity_summary.json", activity_summary(snn_toggles))


def test_missing_inputs_produce_insufficient_rtl_data_and_outputs(tmp_path) -> None:
    summary = compare_rtl_designs(tmp_path)
    assert summary["recommendation"] == "insufficient_rtl_data"
    assert summary["inputs"]["rtl_summary"]["found"] is False
    assert (tmp_path / "rtl_comparison_summary.json").is_file()
    report = (tmp_path / "rtl_comparison_report.md").read_text(encoding="utf-8")
    assert "## Tiny SNN v2 Decision" in report
    assert "local-tool proxies" in report


def test_low_ratios_recommend_continue_optimization(tmp_path) -> None:
    write_inputs(tmp_path, snn_cells=150, snn_toggles=1600)
    summary = compare_rtl_designs(tmp_path)
    assert summary["recommendation"] == "continue_snn_rtl_optimization"
    assert summary["designs"]["tiny_snn_v2"]["cell_ratio_vs_fsm"] == 1.5
    assert summary["designs"]["tiny_snn_v2"]["toggle_ratio_vs_fsm"] == 1.6
    assert summary["designs"]["tiny_snn_v2_sparse_activity"]["cell_ratio_vs_fsm"] == 1.2
    assert summary["designs"]["tiny_snn_v2_sparse_activity"]["toggle_ratio_vs_fsm"] == 1.1
    assert summary["tiny_snn_v2_sparse_activity_context"]["simulation_passed"] is True


def test_medium_ratios_recommend_optimize_before_more_features(tmp_path) -> None:
    write_inputs(tmp_path, snn_cells=350, snn_toggles=5000)
    summary = compare_rtl_designs(tmp_path)
    assert summary["recommendation"] == "optimize_snn_rtl_before_more_features"


def test_high_ratios_recommend_prioritize_baseline(tmp_path) -> None:
    write_inputs(tmp_path, snn_cells=450, snn_toggles=5000)
    summary = compare_rtl_designs(tmp_path)
    assert summary["recommendation"] == "prioritize_fsm_or_lut_rtl_baseline"


def test_nonpassing_simulation_is_insufficient_data(tmp_path) -> None:
    payload = rtl_summary(100)
    payload["simulations"]["tiny_snn_v2"]["status"] = "fail"
    write_json(tmp_path / "rtl_summary.json", payload)
    write_json(tmp_path / "rtl_activity_summary.json", activity_summary(1000))
    summary = compare_rtl_designs(tmp_path)
    assert summary["recommendation"] == "insufficient_rtl_data"
    assert "simulation" in summary["reason"]
