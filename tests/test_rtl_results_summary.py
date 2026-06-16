from __future__ import annotations

import json

from tinysnnrfid.summarize_rtl_results import (
    parse_simulation_log,
    parse_synthesis_json,
    summarize_rtl_results,
)


def test_missing_inputs_produce_missing_statuses_and_outputs(tmp_path) -> None:
    input_dir = tmp_path / "rtl"
    output_dir = tmp_path / "output"
    summary = summarize_rtl_results(input_dir, output_dir)
    assert all(values["status"] == "missing" for values in summary["simulations"].values())
    assert all(values["status"] == "missing" for values in summary["synthesis"].values())
    assert summary["simulations"]["tiny_snn_v2"]["status"] == "missing"
    assert summary["synthesis"]["tiny_snn_v2"]["status"] == "missing"
    assert summary["recommendation_context"]["baseline_rtl_available"] is False
    assert (output_dir / "rtl_summary.json").is_file()
    report = (output_dir / "rtl_report.md").read_text(encoding="utf-8")
    assert "## Simulation Summary" in report
    assert "not silicon signoff" in report
    assert "measured silicon power" in report


def test_simulation_summary_is_parsed(tmp_path) -> None:
    log = tmp_path / "sim_threshold.log"
    log.write_text("FAIL sample=3\nbaseline detector: 9 passed, 1 failed\n", encoding="utf-8")
    assert parse_simulation_log(log) == {
        "found": True,
        "passed": 9,
        "failed": 1,
        "status": "fail",
    }


def test_yosys_style_json_cell_count_is_parsed(tmp_path) -> None:
    synth = tmp_path / "synth_fsm.json"
    synth.write_text(json.dumps({"modules": {"fsm_detector": {"attributes": {"top": "1"}, "cells": {"a": {}, "b": {}}}}}), encoding="utf-8")
    assert parse_synthesis_json(synth) == {"found": True, "status": "available", "cell_count": 2}


def test_summary_selects_lowest_cell_count(tmp_path) -> None:
    for name, count in (("threshold", 4), ("fsm", 2), ("lut_like", 7)):
        (tmp_path / f"synth_{name}.json").write_text(json.dumps({"num_cells": count}), encoding="utf-8")
    summary = summarize_rtl_results(tmp_path)
    assert summary["recommendation_context"]["lowest_cell_count_baseline"] == "fsm"


def test_rtl_report_includes_activity_summary_when_present(tmp_path) -> None:
    (tmp_path / "rtl_activity_summary.json").write_text(
        json.dumps(
            {
                "baselines": {
                    "threshold": {"found": True, "status": "available", "total_toggles": 12},
                    "fsm": {"found": True, "status": "available", "total_toggles": 7},
                    "lut_like": {"found": False, "status": "missing"},
                    "tiny_snn_v2": {"found": False, "status": "missing"},
                },
                "recommendation_context": {"lowest_toggle_baseline": "fsm"},
                "note": "Toggle counts are simulation activity proxies and are not measured silicon power.",
            }
        ),
        encoding="utf-8",
    )
    summary = summarize_rtl_results(tmp_path)
    assert summary["activity"]["baselines"]["fsm"]["total_toggles"] == 7
    report = (tmp_path / "rtl_report.md").read_text(encoding="utf-8")
    assert "## Toggle Activity Summary" in report
    assert "tiny_snn_v2" in report
    assert "Lowest available toggle-count baseline: `fsm`" in report
    assert "not measured silicon power" in report
