from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Any


SECTIONS = (
    "Abstract",
    "Research Question",
    "Methodology",
    "Dataset and Scenario Suites",
    "Classifiers Compared",
    "Software Evidence Summary",
    "RTL Evidence Summary",
    "Decision Summary",
    "Limitations",
    "Reproducibility",
    "Next Steps",
)

PROXY_LIMITATION = (
    "Software activity, RTL cell counts, and RTL toggle counts are proxies, "
    "not silicon measurements or signoff results."
)


def _load_optional_json(path: Path) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    found = path.is_file()
    info: dict[str, Any] = {"path": str(path), "found": found}
    if not found:
        return None, info
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        info["error"] = str(exc)
        return None, info
    if not isinstance(payload, dict):
        info["error"] = "JSON root is not an object"
        return None, info
    return payload, info


def _load_optional_text(path: Path) -> tuple[str | None, dict[str, Any]]:
    found = path.is_file()
    info: dict[str, Any] = {"path": str(path), "found": found}
    if not found:
        return None, info
    try:
        return path.read_text(encoding="utf-8"), info
    except OSError as exc:
        info["error"] = str(exc)
        return None, info


def input_paths(input_root: Path) -> dict[str, Path]:
    return {
        "artifact_card": input_root / "artifact_card.json",
        "research_decision_summary": input_root / "research_decision_summary.json",
        "research_decision_report": input_root / "research_decision_report.md",
        "rtl_comparison_summary": input_root / "rtl" / "rtl_comparison_summary.json",
        "rtl_comparison_report": input_root / "rtl" / "rtl_comparison_report.md",
        "evidence_manifest": input_root / "evidence_manifest.json",
    }


def _fmt(value: Any) -> str:
    if value is None:
        return "-"
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)


def _missing_output_count(manifest: dict[str, Any] | None) -> int | None:
    if not isinstance(manifest, dict):
        return None
    missing = manifest.get("missing_outputs")
    if isinstance(missing, list):
        return len(missing)
    outputs = manifest.get("outputs")
    if isinstance(outputs, list):
        return sum(1 for entry in outputs if isinstance(entry, dict) and not entry.get("found", False))
    return None


def _research_highlights(research: dict[str, Any]) -> list[str]:
    highlights = research.get("highlights")
    if isinstance(highlights, list):
        return [str(item) for item in highlights[:8]]
    return []


def _software_counts(research: dict[str, Any]) -> dict[str, Any]:
    evidence = research.get("evidence", {}) if isinstance(research, dict) else {}
    legacy_search = evidence.get("legacy_snn_search", {}) if isinstance(evidence, dict) else {}
    temporal_search = evidence.get("temporal_snn_search", {}) if isinstance(evidence, dict) else {}
    legacy_sweep = evidence.get("legacy_sweep", {}) if isinstance(evidence, dict) else {}
    temporal_sweep = evidence.get("temporal_sweep", {}) if isinstance(evidence, dict) else {}
    return {
        "legacy_sweep_recommendation": legacy_sweep.get("recommendation"),
        "legacy_snn_search_recommendation": legacy_search.get("recommendation"),
        "legacy_snn_search_competitive": legacy_search.get("competitive_candidate_count"),
        "temporal_sweep_recommendation": temporal_sweep.get("recommendation"),
        "temporal_snn_search_recommendation": temporal_search.get("recommendation"),
        "temporal_snn_search_competitive": temporal_search.get("competitive_candidate_count"),
    }


def collect_writeup(input_root: str | Path = "results", output_dir: str | Path = "results") -> dict[str, Any]:
    root = Path(input_root)
    out = Path(output_dir)
    paths = input_paths(root)
    artifact, artifact_info = _load_optional_json(paths["artifact_card"])
    research, research_info = _load_optional_json(paths["research_decision_summary"])
    research_report, research_report_info = _load_optional_text(paths["research_decision_report"])
    rtl, rtl_info = _load_optional_json(paths["rtl_comparison_summary"])
    rtl_report, rtl_report_info = _load_optional_text(paths["rtl_comparison_report"])
    manifest, manifest_info = _load_optional_json(paths["evidence_manifest"])

    artifact = artifact or {}
    research = research or {}
    rtl = rtl or {}
    manifest = manifest or {}
    rtl_context = rtl.get("tiny_snn_v2_context", {}) if isinstance(rtl, dict) else {}
    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "input_root": str(root),
        "output_dir": str(out),
        "inputs": {
            "artifact_card": artifact_info,
            "research_decision_summary": research_info,
            "research_decision_report": research_report_info,
            "rtl_comparison_summary": rtl_info,
            "rtl_comparison_report": rtl_report_info,
            "evidence_manifest": manifest_info,
        },
        "missing_inputs": [
            name
            for name, info in (
                ("artifact_card", artifact_info),
                ("research_decision_summary", research_info),
                ("research_decision_report", research_report_info),
                ("rtl_comparison_summary", rtl_info),
                ("rtl_comparison_report", rtl_report_info),
                ("evidence_manifest", manifest_info),
            )
            if not info["found"]
        ],
        "recommendation": research.get("recommendation")
        or artifact.get("main_recommendation", {}).get("recommendation"),
        "reason": research.get("reason") or artifact.get("main_recommendation", {}).get("reason"),
        "software": _software_counts(research),
        "research_highlights": _research_highlights(research),
        "rtl": {
            "recommendation": rtl.get("recommendation"),
            "reason": rtl.get("reason"),
            "reference_design": rtl.get("reference_design"),
            "tiny_snn_v2_cell_ratio_vs_fsm": rtl_context.get("cell_ratio_vs_fsm"),
            "tiny_snn_v2_toggle_ratio_vs_fsm": rtl_context.get("toggle_ratio_vs_fsm"),
        },
        "evidence_manifest": {
            "complete": manifest.get("complete"),
            "missing_output_count": _missing_output_count(manifest),
        },
        "source_report_lengths": {
            "research_decision_report_chars": len(research_report or ""),
            "rtl_comparison_report_chars": len(rtl_report or ""),
        },
        "limitations": [PROXY_LIMITATION],
        "outputs": {
            "markdown": str(out / "research_writeup.md"),
            "summary_json": str(out / "research_writeup_summary.json"),
        },
    }
    return summary


def render_writeup(summary: dict[str, Any]) -> str:
    recommendation = summary.get("recommendation") or "insufficient_data"
    reason = summary.get("reason") or "Required evidence summaries were not fully available."
    software = summary["software"]
    rtl = summary["rtl"]
    manifest = summary["evidence_manifest"]
    highlights = summary.get("research_highlights", [])
    lines = [
        "# Tiny SNN RFID Research Writeup",
        "",
        "## Abstract",
        "",
        (
            "This writeup summarizes the generated evidence for a benchmark-first study of tiny "
            "spiking-neural-network logic against conventional RFID sensor-tag event classifiers. "
            f"The current evidence-level recommendation is `{recommendation}`. {PROXY_LIMITATION}"
        ),
        "",
        "## Research Question",
        "",
        (
            "Can a tiny event-driven SNN-style classifier provide useful robustness or activity "
            "advantages for sparse RFID sensor-tag event decisions while remaining competitive "
            "against threshold logic, FSMs, and LUT-like baselines?"
        ),
        "",
        "## Methodology",
        "",
        (
            "The project uses deterministic generated datasets, fixed classifier configurations, "
            "parameter sweeps, bounded tiny_snn_v2 searches, RTL vector export, and optional local "
            "RTL simulation/synthesis summaries. This writeup only aggregates existing generated "
            "outputs; it does not rerun training, benchmarks, simulation, or synthesis."
        ),
        "",
        "## Dataset and Scenario Suites",
        "",
        (
            "Evidence covers the legacy noisy-event detector suite and the temporal-hard suite "
            "when their generated reports are present. The temporal-hard suite includes long-gap "
            "positives, distractors, dropouts, reversed/partial-order negatives, burst noise, "
            "and near misses."
        ),
        "",
        "## Classifiers Compared",
        "",
        (
            "The compared software classifiers are threshold logic, an ordered-pattern FSM, a "
            "LUT-like baseline, the legacy tiny_snn detector, and fixed-weight tiny_snn_v2. "
            "The RTL evidence focuses on threshold, FSM, LUT-like, and tiny_snn_v2 detector "
            "implementations where local tool outputs are available."
        ),
        "",
        "## Software Evidence Summary",
        "",
    ]
    if highlights:
        lines.extend(f"- {highlight}" for highlight in highlights)
    else:
        lines.append("- Software evidence summaries were not available.")
    lines.extend(
        [
            f"- Legacy sweep recommendation: `{software.get('legacy_sweep_recommendation') or 'unavailable'}`.",
            f"- Legacy SNN search recommendation: `{software.get('legacy_snn_search_recommendation') or 'unavailable'}`.",
            f"- Legacy SNN search competitive candidates: `{_fmt(software.get('legacy_snn_search_competitive'))}`.",
            f"- Temporal-hard sweep recommendation: `{software.get('temporal_sweep_recommendation') or 'unavailable'}`.",
            f"- Temporal-hard SNN search recommendation: `{software.get('temporal_snn_search_recommendation') or 'unavailable'}`.",
            f"- Temporal-hard SNN search competitive candidates: `{_fmt(software.get('temporal_snn_search_competitive'))}`.",
            "",
            "## RTL Evidence Summary",
            "",
            f"- RTL recommendation: `{rtl.get('recommendation') or 'unavailable'}`.",
            f"- RTL reason: {rtl.get('reason') or 'RTL comparison summary was not available.'}",
            f"- Reference design: `{rtl.get('reference_design') or 'fsm'}`.",
            f"- `tiny_snn_v2` cell ratio vs FSM: `{_fmt(rtl.get('tiny_snn_v2_cell_ratio_vs_fsm'))}`.",
            f"- `tiny_snn_v2` toggle ratio vs FSM: `{_fmt(rtl.get('tiny_snn_v2_toggle_ratio_vs_fsm'))}`.",
            "",
            "## Decision Summary",
            "",
            f"- Recommendation: `{recommendation}`.",
            f"- Reason: {reason}",
            f"- Evidence manifest complete: `{_fmt(manifest.get('complete'))}`.",
            f"- Missing manifest output count: `{_fmt(manifest.get('missing_output_count'))}`.",
            "",
            "## Limitations",
            "",
            f"- {PROXY_LIMITATION}",
            "- Open-source RTL simulation and synthesis outputs, when present, are local-tool evidence and not silicon signoff.",
            "- The SNN configurations are fixed or searched over bounded hand-defined parameter grids; this writeup does not add training.",
            "- Missing inputs are reported in the summary JSON and should be treated as incomplete evidence rather than negative results.",
            "",
            "## Reproducibility",
            "",
            "- `make evidence` rebuilds the full evidence pipeline.",
            "- `make research-report` rebuilds the consolidated research decision report from existing outputs.",
            "- `make evidence-manifest` rebuilds the evidence manifest.",
            "- `make artifact-card` rebuilds the short artifact card.",
            "- `make research-writeup` rebuilds this paper-style writeup.",
            "",
            "## Next Steps",
            "",
            "- Inspect `artifact_card.md` first for the compact reviewer entry point.",
            "- Inspect `research_decision_report.md` and `rtl/rtl_comparison_report.md` for detailed evidence tables.",
            "- Add or rerun optional RTL simulation/synthesis tooling when local Icarus Verilog or Yosys evidence is needed.",
            "- Keep comparing tiny_snn_v2 only against simple baselines unless stronger evidence justifies additional RTL work.",
            "",
        ]
    )
    return "\n".join(lines)


def build_research_writeup(
    input_root: str | Path = "results",
    output_dir: str | Path = "results",
) -> dict[str, Any]:
    summary = collect_writeup(input_root, output_dir)
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    markdown_path = out / "research_writeup.md"
    json_path = out / "research_writeup_summary.json"
    markdown_path.write_text(render_writeup(summary), encoding="utf-8")
    json_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"Research writeup written: {markdown_path}")
    print(f"Research writeup summary written: {json_path}")
    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build a paper-style research writeup from existing evidence.")
    parser.add_argument("--input-root", type=Path, default=Path("results"))
    parser.add_argument("--output-dir", type=Path, default=Path("results"))
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        build_research_writeup(args.input_root, args.output_dir)
        return 0
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
