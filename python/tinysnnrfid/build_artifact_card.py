from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Any


PROXY_LIMITATION = (
    "Software activity, RTL cell counts, and RTL toggle counts are proxies, "
    "not silicon measurements, measured silicon power, or measured energy."
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


def _input_paths(input_root: Path) -> dict[str, Path]:
    smoke_in_root = input_root / "smoke_summary.json"
    smoke_nested = input_root / "smoke" / "smoke_summary.json"
    return {
        "research_decision_summary": input_root / "research_decision_summary.json",
        "rtl_comparison_summary": input_root / "rtl" / "rtl_comparison_summary.json",
        "evidence_manifest": input_root / "evidence_manifest.json",
        "smoke_summary": smoke_in_root if smoke_in_root.is_file() else smoke_nested,
    }


def _fmt(value: Any) -> str:
    if value is None:
        return "-"
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)


def _manifest_missing_count(manifest: dict[str, Any] | None) -> int | None:
    if not isinstance(manifest, dict):
        return None
    missing = manifest.get("missing_outputs")
    if isinstance(missing, list):
        return len(missing)
    outputs = manifest.get("outputs")
    if isinstance(outputs, list):
        return sum(1 for item in outputs if isinstance(item, dict) and not item.get("found", False))
    return None


def _key_files(input_root: Path, output_dir: Path, inputs: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    paths = [
        output_dir / "artifact_card.json",
        output_dir / "artifact_card.md",
        input_root / "research_decision_report.md",
        input_root / "evidence_manifest.md",
        input_root / "rtl" / "rtl_comparison_report.md",
        input_root / "smoke_report.md",
        input_root / "smoke" / "smoke_report.md",
    ]
    seen: set[str] = set()
    files: list[dict[str, Any]] = []
    for path in paths:
        key = str(path)
        if key in seen:
            continue
        seen.add(key)
        files.append({"path": key, "found": path.is_file()})
    for info in inputs.values():
        path = info["path"]
        if path not in seen:
            seen.add(path)
            files.append({"path": path, "found": bool(info.get("found"))})
    return files


def collect_artifact_card(input_root: str | Path = "results", output_dir: str | Path = "results") -> dict[str, Any]:
    root = Path(input_root)
    out = Path(output_dir)
    paths = _input_paths(root)
    payloads: dict[str, dict[str, Any] | None] = {}
    inputs: dict[str, dict[str, Any]] = {}
    for name, path in paths.items():
        payload, info = _load_optional_json(path)
        payloads[name] = payload
        inputs[name] = info

    research = payloads["research_decision_summary"] or {}
    rtl = payloads["rtl_comparison_summary"] or {}
    manifest = payloads["evidence_manifest"] or {}
    smoke = payloads["smoke_summary"] or {}
    rtl_context = rtl.get("tiny_snn_v2_context", {}) if isinstance(rtl, dict) else {}
    manifest_missing_count = _manifest_missing_count(manifest)
    evidence_complete = manifest.get("complete") if isinstance(manifest, dict) else None
    smoke_status = smoke.get("status") if isinstance(smoke, dict) else None

    missing_inputs = [name for name, info in inputs.items() if not info["found"]]
    card = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "input_root": str(root),
        "output_dir": str(out),
        "inputs": inputs,
        "missing_inputs": missing_inputs,
        "executive_summary": build_executive_summary(
            research,
            rtl,
            evidence_complete,
            manifest_missing_count,
            smoke_status,
        ),
        "main_recommendation": {
            "recommendation": research.get("recommendation"),
            "reason": research.get("reason"),
        },
        "rtl_snapshot": {
            "recommendation": rtl.get("recommendation"),
            "reason": rtl.get("reason"),
            "reference_design": rtl.get("reference_design"),
            "tiny_snn_v2_cell_ratio_vs_fsm": rtl_context.get("cell_ratio_vs_fsm"),
            "tiny_snn_v2_toggle_ratio_vs_fsm": rtl_context.get("toggle_ratio_vs_fsm"),
        },
        "evidence_status": {
            "manifest_complete": evidence_complete,
            "missing_output_count": manifest_missing_count,
            "smoke_status": smoke_status,
        },
        "key_files": _key_files(root, out, inputs),
        "commands": [
            "make evidence",
            "make evidence-smoke",
            "make research-report",
            "make evidence-manifest",
            "make artifact-card",
        ],
        "limitations": [PROXY_LIMITATION],
    }
    return card


def build_executive_summary(
    research: dict[str, Any],
    rtl: dict[str, Any],
    evidence_complete: Any,
    missing_count: int | None,
    smoke_status: Any,
) -> str:
    recommendation = research.get("recommendation") or "unavailable"
    rtl_recommendation = rtl.get("recommendation") or "unavailable"
    complete_text = "unknown" if evidence_complete is None else str(bool(evidence_complete)).lower()
    missing_text = "unknown" if missing_count is None else str(missing_count)
    smoke_text = smoke_status or "not available"
    return (
        f"Research recommendation: {recommendation}. RTL comparison: {rtl_recommendation}. "
        f"Evidence manifest complete: {complete_text} with {missing_text} missing output(s). "
        f"Smoke status: {smoke_text}."
    )


def render_artifact_card(card: dict[str, Any]) -> str:
    main = card["main_recommendation"]
    rtl = card["rtl_snapshot"]
    status = card["evidence_status"]
    lines = [
        "# Tiny SNN RFID Artifact Card",
        "",
        "## Executive Summary",
        "",
        card["executive_summary"],
        "",
        "## Main Recommendation",
        "",
        f"- Recommendation: `{main.get('recommendation') or 'unavailable'}`.",
        f"- Reason: {main.get('reason') or 'Research decision summary not available.'}",
        "",
        "## Evidence Status",
        "",
        f"- Manifest complete: `{_fmt(status.get('manifest_complete'))}`.",
        f"- Missing output count: `{_fmt(status.get('missing_output_count'))}`.",
        f"- Smoke status: `{status.get('smoke_status') or 'not available'}`.",
        "",
        "## RTL SNN-vs-Baseline Snapshot",
        "",
        f"- RTL recommendation: `{rtl.get('recommendation') or 'unavailable'}`.",
        f"- Reason: {rtl.get('reason') or 'RTL comparison summary not available.'}",
        f"- Reference design: `{rtl.get('reference_design') or 'fsm'}`.",
        f"- `tiny_snn_v2` cell ratio vs FSM: `{_fmt(rtl.get('tiny_snn_v2_cell_ratio_vs_fsm'))}`.",
        f"- `tiny_snn_v2` toggle ratio vs FSM: `{_fmt(rtl.get('tiny_snn_v2_toggle_ratio_vs_fsm'))}`.",
        "",
        "## Key Files",
        "",
        "| File | Found |",
        "|---|---|",
    ]
    for entry in card["key_files"]:
        lines.append(f"| `{entry['path']}` | {'yes' if entry['found'] else 'no'} |")
    lines.extend(["", "## Commands", ""])
    lines.extend(f"- `{command}`" for command in card["commands"])
    lines.extend(["", "## Limitations", ""])
    lines.extend(f"- {limitation}" for limitation in card["limitations"])
    lines.append("")
    return "\n".join(lines)


def build_artifact_card(
    input_root: str | Path = "results",
    output_dir: str | Path = "results",
) -> dict[str, Any]:
    card = collect_artifact_card(input_root, output_dir)
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    json_path = out / "artifact_card.json"
    markdown_path = out / "artifact_card.md"
    for _ in range(2):
        json_path.write_text(json.dumps(card, indent=2), encoding="utf-8")
        markdown_path.write_text(render_artifact_card(card), encoding="utf-8")
        card = collect_artifact_card(input_root, output_dir)
    json_path.write_text(json.dumps(card, indent=2), encoding="utf-8")
    markdown_path.write_text(render_artifact_card(card), encoding="utf-8")
    print(f"Artifact card written: {json_path}")
    print(f"Artifact card report written: {markdown_path}")
    return card


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build a short evidence artifact card.")
    parser.add_argument("--input-root", type=Path, default=Path("results"))
    parser.add_argument("--output-dir", type=Path, default=Path("results"))
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        build_artifact_card(args.input_root, args.output_dir)
        return 0
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
