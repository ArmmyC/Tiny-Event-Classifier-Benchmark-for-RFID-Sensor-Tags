from __future__ import annotations

import json
from pathlib import Path

from tinysnnrfid.build_artifact_card import build_artifact_card
from tinysnnrfid.clean_outputs import FILE_PATTERNS


ROOT = Path(__file__).resolve().parents[1]


def test_missing_inputs_still_produce_artifact_card(tmp_path) -> None:
    card = build_artifact_card(tmp_path / "empty", tmp_path / "out")

    assert card["missing_inputs"] == [
        "research_decision_summary",
        "rtl_comparison_summary",
        "evidence_manifest",
        "smoke_summary",
    ]
    assert (tmp_path / "out" / "artifact_card.json").is_file()
    assert (tmp_path / "out" / "artifact_card.md").is_file()
    key_files = {entry["path"]: entry["found"] for entry in card["key_files"]}
    assert key_files[str(tmp_path / "out" / "artifact_card.json")] is True
    assert key_files[str(tmp_path / "out" / "artifact_card.md")] is True
    markdown = (tmp_path / "out" / "artifact_card.md").read_text(encoding="utf-8")
    for section in (
        "# Tiny SNN RFID Artifact Card",
        "## Executive Summary",
        "## Main Recommendation",
        "## Evidence Status",
        "## RTL SNN-vs-Baseline Snapshot",
        "## Key Files",
        "## Commands",
        "## Limitations",
    ):
        assert section in markdown
    assert "proxies, not silicon measurements" in markdown


def test_artifact_card_loads_synthetic_inputs(tmp_path) -> None:
    root = tmp_path / "results"
    (root / "rtl").mkdir(parents=True)
    (root / "smoke").mkdir()
    (root / "research_decision_summary.json").write_text(
        json.dumps(
            {
                "recommendation": "prioritize_fsm_or_lut_rtl_baseline",
                "reason": "Synthetic research reason.",
            }
        ),
        encoding="utf-8",
    )
    (root / "rtl" / "rtl_comparison_summary.json").write_text(
        json.dumps(
            {
                "recommendation": "insufficient_rtl_data",
                "reason": "Synthetic RTL reason.",
                "reference_design": "fsm",
                "tiny_snn_v2_context": {
                    "cell_ratio_vs_fsm": 1.5,
                    "toggle_ratio_vs_fsm": 2.25,
                },
            }
        ),
        encoding="utf-8",
    )
    (root / "evidence_manifest.json").write_text(
        json.dumps({"complete": False, "missing_outputs": ["a.json", "b.md"]}),
        encoding="utf-8",
    )
    (root / "smoke" / "smoke_summary.json").write_text(
        json.dumps({"status": "pass"}),
        encoding="utf-8",
    )

    card = build_artifact_card(root, root)

    assert card["main_recommendation"]["recommendation"] == "prioritize_fsm_or_lut_rtl_baseline"
    assert card["rtl_snapshot"]["recommendation"] == "insufficient_rtl_data"
    assert card["rtl_snapshot"]["tiny_snn_v2_cell_ratio_vs_fsm"] == 1.5
    assert card["rtl_snapshot"]["tiny_snn_v2_toggle_ratio_vs_fsm"] == 2.25
    assert card["evidence_status"]["manifest_complete"] is False
    assert card["evidence_status"]["missing_output_count"] == 2
    assert card["evidence_status"]["smoke_status"] == "pass"

    markdown = (root / "artifact_card.md").read_text(encoding="utf-8")
    assert "Synthetic research reason." in markdown
    assert "`1.500`" in markdown
    assert "`2.250`" in markdown


def test_artifact_card_supports_smoke_input_root(tmp_path) -> None:
    smoke = tmp_path / "results" / "smoke"
    smoke.mkdir(parents=True)
    (smoke / "smoke_summary.json").write_text(json.dumps({"status": "pass"}), encoding="utf-8")

    card = build_artifact_card(smoke, smoke)

    assert card["inputs"]["smoke_summary"]["found"] is True
    assert card["evidence_status"]["smoke_status"] == "pass"
    assert (smoke / "artifact_card.json").is_file()
    assert (smoke / "artifact_card.md").is_file()


def test_makefile_contains_artifact_card_target_and_order() -> None:
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    assert "artifact-card:" in makefile
    assert "python python/build_artifact_card.py --input-root results --output-dir results" in makefile
    evidence_header = next(line for line in makefile.splitlines() if line.startswith("evidence:"))
    dependencies = evidence_header.split(":", 1)[1].split()
    assert dependencies.index("evidence-manifest") < dependencies.index("artifact-card")


def test_clean_removes_artifact_card_outputs() -> None:
    assert "results/artifact_card.json" in FILE_PATTERNS
    assert "results/artifact_card.md" in FILE_PATTERNS
