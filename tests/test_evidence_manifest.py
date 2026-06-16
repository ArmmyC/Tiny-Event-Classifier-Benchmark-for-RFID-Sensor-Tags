from __future__ import annotations

import json
from pathlib import Path
import re

from tinysnnrfid.build_evidence_manifest import build_evidence_manifest


ROOT = Path(__file__).resolve().parents[1]


def test_makefile_contains_evidence_targets() -> None:
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    for target in ("software-evidence:", "rtl-evidence:", "evidence:", "evidence-manifest:"):
        assert target in makefile
    evidence_index = makefile.index("evidence:")
    assert makefile.index("$(MAKE) software-evidence", evidence_index) < makefile.index(
        "$(MAKE) rtl-evidence", evidence_index
    )
    assert makefile.index("$(MAKE) rtl-evidence", evidence_index) < makefile.index(
        "$(MAKE) research-report", evidence_index
    )
    assert makefile.index("$(MAKE) research-report", evidence_index) < makefile.index(
        "$(MAKE) evidence-manifest", evidence_index
    )


def test_recursive_evidence_targets_use_make_macro() -> None:
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    recursive_targets = {"software-evidence", "rtl-evidence", "evidence"}
    current_target = None
    recursive_lines: list[str] = []
    for line in makefile.splitlines():
        if line and not line.startswith(("\t", " ")) and line.endswith(":"):
            current_target = line[:-1]
            continue
        if current_target in recursive_targets and line.startswith("\t"):
            recursive_lines.append(line)
    assert recursive_lines
    assert all(not line.startswith("\tmake ") for line in recursive_lines)
    assert all(line.startswith("\t$(MAKE) ") for line in recursive_lines)


def test_make_macro_is_not_unconditionally_forced_to_pymake() -> None:
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    assert re.search(r"(?m)^MAKE\s*=", makefile) is None
    conditional_default = "MAKE ?= python -m pymake"
    assert conditional_default in makefile


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
