from __future__ import annotations

import json

from tinysnnrfid.summarize_vcd_activity import parse_vcd_activity, summarize_vcd_activity


def write_sim_status(tmp_path, outputs: dict | None = None, status: str = "pass") -> None:
    (tmp_path / "sim_status.json").write_text(
        json.dumps(
            {
                "step": "sim",
                "started_at": "2026-01-01T00:00:00+00:00",
                "finished_at": "2026-01-01T00:00:01+00:00",
                "status": status,
                "missing_tools": [] if status == "pass" else ["iverilog", "vvp"],
                "outputs_written": outputs or {},
                "return_codes": {},
                "note": "simulation status for test; stale VCDs ignored.",
            }
        ),
        encoding="utf-8",
    )


def tiny_vcd() -> str:
    return """$date
synthetic
$end
$timescale 1ns $end
$scope module tb $end
$var wire 1 ! clk $end
$var wire 4 " sample_bits [3:0] $end
$upscope $end
$enddefinitions $end
#0
0!
b0000 "
#5
1!
b0011 "
#10
0!
b0011 "
#15
1!
b0101 "
"""


def test_missing_vcd_files_produce_missing_statuses_and_outputs(tmp_path) -> None:
    summary = summarize_vcd_activity(tmp_path, tmp_path / "out")
    assert all(values["status"] == "missing" for values in summary["baselines"].values())
    assert summary["baselines"]["tiny_snn_v2"]["status"] == "missing"
    assert summary["baselines"]["tiny_snn_v2_sparse_activity"]["status"] == "missing"
    assert summary["recommendation_context"]["activity_vcd_available"] is False
    assert (tmp_path / "out" / "rtl_activity_summary.json").is_file()
    report = (tmp_path / "out" / "rtl_activity_report.md").read_text(encoding="utf-8")
    assert "## Toggle Summary" in report
    assert "not measured silicon power" in report


def test_tiny_synthetic_vcd_counts_signal_toggles(tmp_path) -> None:
    path = tmp_path / "vcd_threshold.vcd"
    path.write_text(tiny_vcd(), encoding="utf-8")
    parsed = parse_vcd_activity(path)
    assert parsed["status"] == "available"
    assert parsed["signal_count"] == 2
    assert parsed["total_toggles"] > 0
    top = {row["signal"]: row["toggles"] for row in parsed["top_toggled_signals"]}
    assert top["clk"] == 3
    assert top["sample_bits"] == 2


def test_activity_summary_selects_lowest_toggle_baseline(tmp_path) -> None:
    (tmp_path / "vcd_threshold.vcd").write_text(tiny_vcd(), encoding="utf-8")
    (tmp_path / "vcd_fsm.vcd").write_text(
        tiny_vcd().replace("#15\n1!\nb0101 \"\n", ""),
        encoding="utf-8",
    )
    write_sim_status(
        tmp_path,
        {
            "threshold": ["vcd_threshold.vcd"],
            "fsm": ["vcd_fsm.vcd"],
        },
    )
    summary = summarize_vcd_activity(tmp_path)
    assert summary["baselines"]["threshold"]["total_toggles"] == 5
    assert summary["baselines"]["fsm"]["total_toggles"] == 3
    assert summary["recommendation_context"]["lowest_toggle_baseline"] == "fsm"
    written = json.loads((tmp_path / "rtl_activity_summary.json").read_text(encoding="utf-8"))
    assert written["baselines"]["lut_like"]["status"] == "missing"
    assert written["baselines"]["tiny_snn_v2_sparse_activity"]["status"] == "missing"


def test_stale_vcd_is_ignored_when_sim_status_is_skipped(tmp_path) -> None:
    (tmp_path / "vcd_tiny_snn_v2_sparse_activity.vcd").write_text(tiny_vcd(), encoding="utf-8")
    write_sim_status(tmp_path, status="skipped")

    summary = summarize_vcd_activity(tmp_path)

    sparse = summary["baselines"]["tiny_snn_v2_sparse_activity"]
    assert sparse["status"] == "stale"
    assert "total_toggles" not in sparse
    assert summary["recommendation_context"]["activity_vcd_available"] is False
    activity_status = json.loads((tmp_path / "activity_status.json").read_text(encoding="utf-8"))
    assert activity_status["status"] == "skipped"
    report = (tmp_path / "rtl_activity_report.md").read_text(encoding="utf-8")
    assert "stale VCDs ignored" in report
