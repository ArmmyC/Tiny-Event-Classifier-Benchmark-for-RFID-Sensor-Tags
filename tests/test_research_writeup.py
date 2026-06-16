from __future__ import annotations

import json
from pathlib import Path

from tinysnnrfid.build_research_writeup import SECTIONS, build_research_writeup


ROOT = Path(__file__).resolve().parents[1]


def test_missing_inputs_still_write_research_writeup(tmp_path) -> None:
    output = tmp_path / "out"
    summary = build_research_writeup(tmp_path / "missing", output)

    assert summary["recommendation"] is None
    assert set(summary["missing_inputs"]) == {
        "artifact_card",
        "research_decision_summary",
        "research_decision_report",
        "rtl_comparison_summary",
        "rtl_comparison_report",
        "evidence_manifest",
    }
    assert (output / "research_writeup.md").is_file()
    assert (output / "research_writeup_summary.json").is_file()
    markdown = (output / "research_writeup.md").read_text(encoding="utf-8")
    for section in SECTIONS:
        assert f"## {section}" in markdown
    assert "proxies, not silicon measurements or signoff results" in markdown


def test_research_writeup_loads_synthetic_evidence(tmp_path) -> None:
    root = tmp_path / "results"
    (root / "rtl").mkdir(parents=True)
    (root / "artifact_card.json").write_text(
        json.dumps(
            {
                "main_recommendation": {
                    "recommendation": "artifact_recommendation",
                    "reason": "Artifact reason.",
                }
            }
        ),
        encoding="utf-8",
    )
    (root / "research_decision_summary.json").write_text(
        json.dumps(
            {
                "recommendation": "continue_snn_optimization",
                "reason": "Synthetic research reason.",
                "highlights": ["Benchmark best classifier by F1: fsm."],
                "evidence": {
                    "legacy_sweep": {"recommendation": "add_harder_temporal_scenarios"},
                    "legacy_snn_search": {
                        "recommendation": "continue_snn_optimization",
                        "competitive_candidate_count": 3,
                    },
                    "temporal_sweep": {"recommendation": "add_harder_temporal_scenarios"},
                    "temporal_snn_search": {
                        "recommendation": "prioritize_fsm_or_lut_rtl_baseline",
                        "competitive_candidate_count": 0,
                    },
                },
            }
        ),
        encoding="utf-8",
    )
    (root / "research_decision_report.md").write_text("# Research Report\n", encoding="utf-8")
    (root / "rtl" / "rtl_comparison_summary.json").write_text(
        json.dumps(
            {
                "recommendation": "insufficient_rtl_data",
                "reason": "Synthetic RTL reason.",
                "reference_design": "fsm",
                "tiny_snn_v2_context": {
                    "cell_ratio_vs_fsm": 1.25,
                    "toggle_ratio_vs_fsm": 2.5,
                },
            }
        ),
        encoding="utf-8",
    )
    (root / "rtl" / "rtl_comparison_report.md").write_text("# RTL Report\n", encoding="utf-8")
    (root / "evidence_manifest.json").write_text(
        json.dumps({"complete": False, "missing_outputs": ["missing.json"]}),
        encoding="utf-8",
    )

    summary = build_research_writeup(root, root)

    assert summary["recommendation"] == "continue_snn_optimization"
    assert summary["rtl"]["recommendation"] == "insufficient_rtl_data"
    assert summary["rtl"]["tiny_snn_v2_cell_ratio_vs_fsm"] == 1.25
    assert summary["rtl"]["tiny_snn_v2_toggle_ratio_vs_fsm"] == 2.5
    assert summary["evidence_manifest"]["complete"] is False
    assert summary["evidence_manifest"]["missing_output_count"] == 1
    markdown = (root / "research_writeup.md").read_text(encoding="utf-8")
    assert "Synthetic research reason." in markdown
    assert "Synthetic RTL reason." in markdown
    assert "`1.250`" in markdown
    assert "`2.500`" in markdown


def test_makefile_contains_research_writeup_target_and_order() -> None:
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    assert "research-writeup:" in makefile
    assert "python python/build_research_writeup.py --input-root results --output-dir results" in makefile
    evidence_index = makefile.index("evidence:")
    assert makefile.index("$(MAKE) artifact-card", evidence_index) < makefile.index(
        "$(MAKE) research-writeup", evidence_index
    )


def test_clean_removes_research_writeup_outputs() -> None:
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    assert "results/research_writeup.md" in makefile
    assert "results/research_writeup_summary.json" in makefile
