from __future__ import annotations

import json

from tinysnnrfid.summarize_rtl_results import (
    parse_simulation_log,
    parse_synthesis_json,
    summarize_rtl_results,
)


def write_step_status(tmp_path, step: str, status: str, outputs: dict | None = None, missing=None) -> None:
    (tmp_path / f"{step}_status.json").write_text(
        json.dumps(
            {
                "step": step,
                "started_at": "2026-01-01T00:00:00+00:00",
                "finished_at": "2026-01-01T00:00:01+00:00",
                "status": status,
                "missing_tools": missing or [],
                "outputs_written": outputs or {},
                "return_codes": {},
                "note": f"{step} {status}; stale artifacts ignored.",
            }
        ),
        encoding="utf-8",
    )


def test_missing_inputs_produce_missing_statuses_and_outputs(tmp_path) -> None:
    input_dir = tmp_path / "rtl"
    output_dir = tmp_path / "output"
    summary = summarize_rtl_results(input_dir, output_dir)
    assert all(values["status"] == "missing" for values in summary["simulations"].values())
    assert all(values["status"] == "missing" for values in summary["synthesis"].values())
    assert summary["simulations"]["tiny_snn_v2"]["status"] == "missing"
    assert summary["synthesis"]["tiny_snn_v2"]["status"] == "missing"
    assert summary["simulations"]["tiny_snn_v2_sparse_activity"]["status"] == "missing"
    assert summary["synthesis"]["tiny_snn_v2_sparse_activity"]["status"] == "missing"
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
    for name, count in (("threshold", 4), ("fsm", 2), ("lut_like", 7), ("tiny_snn_v2_sparse_activity", 9)):
        (tmp_path / f"synth_{name}.json").write_text(json.dumps({"num_cells": count}), encoding="utf-8")
    write_step_status(
        tmp_path,
        "synth",
        "pass",
        {
            "threshold": ["synth_threshold.json"],
            "fsm": ["synth_fsm.json"],
            "lut_like": ["synth_lut_like.json"],
            "tiny_snn_v2_sparse_activity": ["synth_tiny_snn_v2_sparse_activity.json"],
        },
    )
    summary = summarize_rtl_results(tmp_path)
    assert summary["recommendation_context"]["lowest_cell_count_baseline"] == "fsm"


def test_stale_synth_json_is_ignored_when_synth_status_is_skipped(tmp_path) -> None:
    (tmp_path / "synth_tiny_snn_v2_sparse_activity.json").write_text(
        json.dumps({"num_cells": 610}),
        encoding="utf-8",
    )
    write_step_status(tmp_path, "synth", "skipped", missing=["yosys"])

    summary = summarize_rtl_results(tmp_path)

    sparse = summary["synthesis"]["tiny_snn_v2_sparse_activity"]
    assert sparse["status"] == "stale"
    assert "cell_count" not in sparse
    assert summary["recommendation_context"]["lowest_cell_count_baseline"] is None
    report = (tmp_path / "rtl_report.md").read_text(encoding="utf-8")
    assert "stale artifacts ignored" in report


def test_stale_sim_log_is_ignored_when_sim_status_is_skipped(tmp_path) -> None:
    (tmp_path / "sim_tiny_snn_v2_sparse_activity.log").write_text(
        "baseline detector: 320 passed, 0 failed\n",
        encoding="utf-8",
    )
    write_step_status(tmp_path, "sim", "skipped", missing=["iverilog", "vvp"])

    summary = summarize_rtl_results(tmp_path)

    sparse = summary["simulations"]["tiny_snn_v2_sparse_activity"]
    assert sparse["status"] == "stale"
    assert "passed" not in sparse
    assert summary["recommendation_context"]["all_available_sims_pass"] is False
    report = (tmp_path / "rtl_report.md").read_text(encoding="utf-8")
    assert "stale artifacts ignored" in report


def test_rtl_report_includes_activity_summary_when_present(tmp_path) -> None:
    (tmp_path / "rtl_activity_summary.json").write_text(
        json.dumps(
            {
                "baselines": {
                    "threshold": {"found": True, "status": "available", "total_toggles": 12},
                    "fsm": {"found": True, "status": "available", "total_toggles": 7},
                    "lut_like": {"found": False, "status": "missing"},
                    "tiny_snn_v2": {"found": False, "status": "missing"},
                    "tiny_snn_v2_sparse_activity": {"found": False, "status": "missing"},
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
    assert "tiny_snn_v2_sparse_activity" in report
    assert "Lowest available toggle-count baseline: `fsm`" in report
    assert "not measured silicon power" in report
