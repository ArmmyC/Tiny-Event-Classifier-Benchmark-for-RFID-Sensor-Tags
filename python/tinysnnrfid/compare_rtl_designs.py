from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Any


DESIGNS = ("threshold", "fsm", "lut_like", "tiny_snn_v2", "tiny_snn_v2_sparse_activity")
REFERENCE_DESIGN = "fsm"
LEGACY_SNN_DESIGN = "tiny_snn_v2"
CANDIDATE_DESIGN = "tiny_snn_v2_sparse_activity"
CONTINUE_RATIO_LIMIT = 2.0
OPTIMIZE_RATIO_LIMIT = 4.0


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


def _ratio(value: Any, reference: Any) -> float | None:
    if not isinstance(value, int | float) or not isinstance(reference, int | float):
        return None
    if reference == 0:
        return None
    return float(value) / float(reference)


def build_design_rows(
    rtl_summary: dict[str, Any] | None,
    activity_summary: dict[str, Any] | None,
) -> dict[str, dict[str, Any]]:
    rtl_status = rtl_summary.get("status", {}) if isinstance(rtl_summary, dict) else {}
    sim_current = _status_passed(rtl_status.get("simulation") if isinstance(rtl_status, dict) else None)
    synth_current = _status_passed(rtl_status.get("synthesis") if isinstance(rtl_status, dict) else None)
    activity_status = activity_summary.get("status", {}) if isinstance(activity_summary, dict) else {}
    activity_current = _status_passed(
        activity_status.get("simulation") if isinstance(activity_status, dict) else None
    )
    simulations = rtl_summary.get("simulations", {}) if isinstance(rtl_summary, dict) else {}
    synthesis = rtl_summary.get("synthesis", {}) if isinstance(rtl_summary, dict) else {}
    activity = activity_summary.get("baselines", {}) if isinstance(activity_summary, dict) else {}
    fsm_cells = (
        synthesis.get(REFERENCE_DESIGN, {}).get("cell_count")
        if synth_current and isinstance(synthesis, dict)
        else None
    )
    fsm_toggles = (
        activity.get(REFERENCE_DESIGN, {}).get("total_toggles")
        if activity_current and isinstance(activity, dict)
        else None
    )
    rows: dict[str, dict[str, Any]] = {}
    for name in DESIGNS:
        sim_values = simulations.get(name, {}) if isinstance(simulations, dict) else {}
        synth_values = synthesis.get(name, {}) if isinstance(synthesis, dict) else {}
        activity_values = activity.get(name, {}) if isinstance(activity, dict) else {}
        cell_count = synth_values.get("cell_count") if synth_current and isinstance(synth_values, dict) else None
        total_toggles = (
            activity_values.get("total_toggles") if activity_current and isinstance(activity_values, dict) else None
        )
        rows[name] = {
            "simulation_status": (
                sim_values.get("status", "missing") if sim_current and isinstance(sim_values, dict) else "stale"
            ),
            "cell_count": cell_count,
            "total_toggles": total_toggles,
            "cell_ratio_vs_fsm": _ratio(cell_count, fsm_cells),
            "toggle_ratio_vs_fsm": _ratio(total_toggles, fsm_toggles),
        }
    return rows


def _status_passed(status: Any) -> bool:
    return isinstance(status, dict) and status.get("status") == "pass"


def choose_recommendation(
    rows: dict[str, dict[str, Any]],
    candidate_design: str = CANDIDATE_DESIGN,
) -> tuple[str, str]:
    fsm = rows.get(REFERENCE_DESIGN, {})
    candidate = rows.get(candidate_design, {})
    if candidate.get("simulation_status") != "pass":
        return "insufficient_rtl_data", f"{candidate_design} simulation is missing or not passing."
    if fsm.get("simulation_status") != "pass":
        return "insufficient_rtl_data", "FSM reference simulation is missing or not passing."
    cell_ratio = candidate.get("cell_ratio_vs_fsm")
    toggle_ratio = candidate.get("toggle_ratio_vs_fsm")
    if cell_ratio is None or toggle_ratio is None:
        return "insufficient_rtl_data", f"FSM and {candidate_design} cell/toggle proxy data are required."
    if cell_ratio <= CONTINUE_RATIO_LIMIT and toggle_ratio <= CONTINUE_RATIO_LIMIT:
        return (
            "continue_snn_rtl_optimization",
            f"{candidate_design} RTL proxy costs are within 2.0x of the FSM reference.",
        )
    if cell_ratio <= OPTIMIZE_RATIO_LIMIT or toggle_ratio <= OPTIMIZE_RATIO_LIMIT:
        return (
            "optimize_snn_rtl_before_more_features",
            f"{candidate_design} has at least one proxy cost within 4.0x of FSM, but needs RTL optimization.",
        )
    return (
        "prioritize_fsm_or_lut_rtl_baseline",
        f"{candidate_design} cell and toggle proxy ratios are both above 4.0x versus FSM.",
    )


def build_comparison_summary(input_dir: str | Path = "results/rtl") -> dict[str, Any]:
    directory = Path(input_dir)
    rtl_summary, rtl_info = _load_optional_json(directory / "rtl_summary.json")
    activity_summary, activity_info = _load_optional_json(directory / "rtl_activity_summary.json")
    rows = build_design_rows(rtl_summary, activity_summary)
    recommendation, reason = choose_recommendation(rows)
    snn = rows[LEGACY_SNN_DESIGN]
    sparse = rows[CANDIDATE_DESIGN]
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "rtl_summary": rtl_info,
            "rtl_activity_summary": activity_info,
        },
        "evidence_status": {
            "rtl_summary": rtl_summary.get("status", {}) if isinstance(rtl_summary, dict) else {},
            "rtl_activity_summary": activity_summary.get("status", {}) if isinstance(activity_summary, dict) else {},
        },
        "reference_design": REFERENCE_DESIGN,
        "candidate_design": CANDIDATE_DESIGN,
        "legacy_snn_design": LEGACY_SNN_DESIGN,
        "designs": rows,
        "recommendation": recommendation,
        "reason": reason,
        "tiny_snn_v2_context": {
            "simulation_passed": snn["simulation_status"] == "pass",
            "cell_ratio_vs_fsm": snn.get("cell_ratio_vs_fsm"),
            "toggle_ratio_vs_fsm": snn.get("toggle_ratio_vs_fsm"),
            "cell_count_higher_than_fsm": _is_higher(snn.get("cell_ratio_vs_fsm")),
            "toggle_count_higher_than_fsm": _is_higher(snn.get("toggle_ratio_vs_fsm")),
        },
        "tiny_snn_v2_sparse_activity_context": {
            "simulation_passed": sparse["simulation_status"] == "pass",
            "cell_ratio_vs_fsm": sparse.get("cell_ratio_vs_fsm"),
            "toggle_ratio_vs_fsm": sparse.get("toggle_ratio_vs_fsm"),
            "cell_count_higher_than_fsm": _is_higher(sparse.get("cell_ratio_vs_fsm")),
            "toggle_count_higher_than_fsm": _is_higher(sparse.get("toggle_ratio_vs_fsm")),
        },
        "note": (
            "Cell counts and toggle counts are local-tool proxies, not silicon area or measured power."
        ),
    }


def _is_higher(ratio: Any) -> bool | None:
    if not isinstance(ratio, int | float):
        return None
    return float(ratio) > 1.0


def _fmt(value: Any) -> str:
    if value is None:
        return "-"
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)


def render_comparison_report(summary: dict[str, Any]) -> str:
    lines = [
        "# RTL SNN-vs-Baseline Comparison Report",
        "",
        "## Inputs Found",
        "",
        "| Input | Path | Found |",
        "|---|---|---|",
    ]
    for name, values in summary["inputs"].items():
        lines.append(f"| {name} | `{values['path']}` | {'yes' if values['found'] else 'no'} |")
    _append_status_warnings(lines, summary.get("evidence_status", {}))
    lines.extend(["", "## Simulation Status", "", "| Design | Status |", "|---|---|"])
    for name, values in summary["designs"].items():
        lines.append(f"| {name} | {values['simulation_status']} |")
    lines.extend(["", "## Cell Count Proxy Comparison", "", "| Design | Cell Count | Ratio vs FSM |", "|---|---:|---:|"])
    for name, values in summary["designs"].items():
        lines.append(f"| {name} | {_fmt(values.get('cell_count'))} | {_fmt(values.get('cell_ratio_vs_fsm'))} |")
    lines.extend(["", "## Toggle Count Proxy Comparison", "", "| Design | Total Toggles | Ratio vs FSM |", "|---|---:|---:|"])
    for name, values in summary["designs"].items():
        lines.append(f"| {name} | {_fmt(values.get('total_toggles'))} | {_fmt(values.get('toggle_ratio_vs_fsm'))} |")
    candidate_design = summary.get("candidate_design", CANDIDATE_DESIGN)
    legacy_snn_design = summary.get("legacy_snn_design", LEGACY_SNN_DESIGN)
    reference_design = summary.get("reference_design", REFERENCE_DESIGN)
    context = summary["tiny_snn_v2_context"]
    sparse_context = summary.get("tiny_snn_v2_sparse_activity_context", {})
    lines.extend(
        [
            "",
            "## Primary RTL Candidate Decision",
            "",
            f"- Candidate design: `{candidate_design}`.",
            f"- Reference design: `{reference_design}`.",
            f"- Legacy/default SNN context: `{legacy_snn_design}`.",
            f"- Recommendation: `{summary['recommendation']}`.",
            f"- Reason: {summary['reason']}",
            f"- `tiny_snn_v2_sparse_activity` cell ratio vs FSM: `{_fmt(sparse_context.get('cell_ratio_vs_fsm'))}`.",
            f"- `tiny_snn_v2_sparse_activity` toggle ratio vs FSM: `{_fmt(sparse_context.get('toggle_ratio_vs_fsm'))}`.",
            f"- `tiny_snn_v2` legacy cell ratio vs FSM: `{_fmt(context.get('cell_ratio_vs_fsm'))}`.",
            f"- `tiny_snn_v2` legacy toggle ratio vs FSM: `{_fmt(context.get('toggle_ratio_vs_fsm'))}`.",
            "",
            "## Notes and Limitations",
            "",
            summary["note"],
            "",
        ]
    )
    return "\n".join(lines)


def _append_status_warnings(lines: list[str], statuses: dict[str, Any]) -> None:
    messages: list[str] = []
    rtl_status = statuses.get("rtl_summary", {}) if isinstance(statuses, dict) else {}
    activity_status = statuses.get("rtl_activity_summary", {}) if isinstance(statuses, dict) else {}
    for label, values in (
        ("simulation", rtl_status.get("simulation", {}) if isinstance(rtl_status, dict) else {}),
        ("synthesis", rtl_status.get("synthesis", {}) if isinstance(rtl_status, dict) else {}),
        ("activity", activity_status.get("simulation", {}) if isinstance(activity_status, dict) else {}),
    ):
        if not isinstance(values, dict) or values.get("status") == "pass":
            continue
        note = values.get("note") or f"Current-run {label} evidence is incomplete; stale artifacts were ignored."
        messages.append(note)
    if messages:
        lines.extend(["", "## Current-Run Status", ""])
        for message in dict.fromkeys(messages):
            lines.append(f"- {message}")


def compare_rtl_designs(
    input_dir: str | Path = "results/rtl",
    output_dir: str | Path | None = None,
) -> dict[str, Any]:
    input_directory = Path(input_dir)
    output_directory = Path(output_dir) if output_dir is not None else input_directory
    output_directory.mkdir(parents=True, exist_ok=True)
    summary = build_comparison_summary(input_directory)
    json_path = output_directory / "rtl_comparison_summary.json"
    report_path = output_directory / "rtl_comparison_report.md"
    json_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    report_path.write_text(render_comparison_report(summary), encoding="utf-8")
    print(f"RTL comparison summary written: {json_path}")
    print(f"RTL comparison report written: {report_path}")
    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Compare RTL SNN and baseline proxy evidence.")
    parser.add_argument("--input-dir", type=Path, default=Path("results/rtl"))
    parser.add_argument("--output-dir", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        compare_rtl_designs(args.input_dir, args.output_dir)
        return 0
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
