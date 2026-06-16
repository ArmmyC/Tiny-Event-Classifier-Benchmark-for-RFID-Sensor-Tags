from __future__ import annotations

import json
from pathlib import Path
import re

from tinysnnrfid.build_evidence_manifest import build_evidence_manifest


ROOT = Path(__file__).resolve().parents[1]


def _makefile_target_header_and_block(makefile: str, target: str) -> tuple[str, list[str]]:
    lines = makefile.splitlines()
    start = next(index for index, line in enumerate(lines) if line.startswith(f"{target}:"))
    header = lines[start]
    block: list[str] = []
    for line in lines[start + 1 :]:
        if line and not line.startswith(("\t", " ")):
            break
        block.append(line)
    return header, block


def _target_dependencies(header: str) -> list[str]:
    return header.split(":", 1)[1].split()


def test_makefile_contains_dependency_only_evidence_targets() -> None:
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    expected_dependencies = {
        "software-evidence": [
            "benchmark",
            "sweep",
            "snn-search",
            "temporal-benchmark",
            "temporal-sweep",
            "temporal-snn-search",
        ],
        "rtl-evidence": [
            "rtl-vectors",
            "rtl-sim",
            "rtl-synth",
            "rtl-activity",
            "rtl-report",
            "rtl-compare",
        ],
        "evidence": [
            "software-evidence",
            "rtl-evidence",
            "research-report",
            "evidence-manifest",
            "artifact-card",
            "research-writeup",
        ],
    }
    for target, dependencies in expected_dependencies.items():
        header, block = _makefile_target_header_and_block(makefile, target)
        assert _target_dependencies(header) == dependencies
        assert all(not line.startswith("\t") for line in block)
    for target in ("evidence-manifest:", "artifact-card:", "research-writeup:"):
        assert target in makefile


def test_evidence_aggregate_targets_do_not_use_recursive_make() -> None:
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    for target in ("software-evidence", "rtl-evidence", "evidence"):
        _, block = _makefile_target_header_and_block(makefile, target)
        assert all("$(MAKE)" not in line for line in block)
        assert all(not line.startswith("\tmake ") for line in block)
    assert "$(MAKE)" not in makefile


def test_make_macro_is_not_forced_to_pymake() -> None:
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    assert re.search(r"(?m)^MAKE\s*=\s*python -m pymake\s*$", makefile) is None
    assert "MAKE ?= python -m pymake" not in makefile


def test_manifest_builder_writes_json_and_markdown(tmp_path) -> None:
    existing = tmp_path / "results" / "existing.json"
    existing.parent.mkdir(parents=True)
    existing.write_text('{"ok": true}', encoding="utf-8")
    manifest = build_evidence_manifest(
        root_dir=tmp_path,
        output_dir=tmp_path / "out",
        expected_outputs=("results/existing.json", "results/missing.md"),
    )
    assert manifest["complete"] is False
    assert (tmp_path / "out" / "evidence_manifest.json").is_file()
    assert (tmp_path / "out" / "evidence_manifest.md").is_file()
    written = json.loads((tmp_path / "out" / "evidence_manifest.json").read_text(encoding="utf-8"))
    assert len(written["outputs"]) == 2
    existing_entry = next(entry for entry in written["outputs"] if entry["path"] == "results/existing.json")
    missing_entry = next(entry for entry in written["outputs"] if entry["path"] == "results/missing.md")
    assert existing_entry["found"] is True
    assert existing_entry["size_bytes"] == len('{"ok": true}')
    assert "modified_at" in existing_entry
    assert missing_entry == {"path": "results/missing.md", "found": False}
    markdown = (tmp_path / "out" / "evidence_manifest.md").read_text(encoding="utf-8")
    assert "## Missing Outputs" in markdown
    assert "`results/missing.md`" in markdown
    assert "not silicon signoff" in markdown


def test_manifest_self_outputs_are_present_after_write(tmp_path) -> None:
    manifest = build_evidence_manifest(
        root_dir=tmp_path,
        output_dir=tmp_path / "results",
        expected_outputs=("results/evidence_manifest.json", "results/evidence_manifest.md"),
    )
    assert manifest["complete"] is True
    written = json.loads((tmp_path / "results" / "evidence_manifest.json").read_text(encoding="utf-8"))
    assert all(entry["found"] for entry in written["outputs"])
