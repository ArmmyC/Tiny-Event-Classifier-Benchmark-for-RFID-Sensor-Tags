from __future__ import annotations

import json
from pathlib import Path

from tinysnnrfid.run_evidence_smoke import run_evidence_smoke


ROOT = Path(__file__).resolve().parents[1]


def test_makefile_contains_evidence_smoke_and_cleanup() -> None:
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    assert "evidence-smoke:" in makefile
    assert "python python/run_evidence_smoke.py" in makefile
    assert "results/evidence_manifest.json" in makefile
    assert "results/evidence_manifest.md" in makefile
    assert "results/smoke" in makefile


def test_ci_runs_evidence_smoke_after_tests_when_present() -> None:
    workflow = ROOT / ".github" / "workflows" / "test.yml"
    if not workflow.is_file():
        return
    text = workflow.read_text(encoding="utf-8")
    assert "make test" in text
    assert "make evidence-smoke" in text
    assert text.index("make test") < text.index("make evidence-smoke")


def test_smoke_runner_writes_summary_and_report(tmp_path) -> None:
    output_dir = tmp_path / "smoke"
    summary = run_evidence_smoke(ROOT, output_dir)

    summary_path = output_dir / "smoke_summary.json"
    report_path = output_dir / "smoke_report.md"
    assert summary["status"] == "pass"
    assert summary_path.is_file()
    assert report_path.is_file()

    written = json.loads(summary_path.read_text(encoding="utf-8"))
    assert written["status"] == "pass"
    assert written["missing_required_outputs"] == []
    assert (output_dir / "evidence_manifest.json").is_file()
    assert (output_dir / "research_decision_report.md").is_file()
    assert (output_dir / "rtl" / "vectors.svh").is_file()
    assert "rtl/sim_threshold.log" in written["missing_optional_outputs"]

    report = report_path.read_text(encoding="utf-8")
    assert "Smoke outputs are not final benchmark results" in report
    assert "Icarus Verilog/Yosys are not required" in report
