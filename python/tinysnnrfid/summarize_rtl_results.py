from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sys
from typing import Any


BASELINES = ("threshold", "fsm", "lut_like", "tiny_snn_v2", "tiny_snn_v2_sparse_activity")
SIMULATION_SUMMARY = re.compile(
    r"(?P<passed>\d+)\s+passed\s*,\s*(?P<failed>\d+)\s+failed",
    re.IGNORECASE,
)


def parse_simulation_log(path: str | Path) -> dict[str, Any]:
    path = Path(path)
    if not path.is_file():
        return {"found": False, "status": "missing"}
    text = path.read_text(encoding="utf-8", errors="replace")
    matches = list(SIMULATION_SUMMARY.finditer(text))
    if not matches:
        return {"found": True, "status": "unknown"}
    match = matches[-1]
    passed = int(match.group("passed"))
    failed = int(match.group("failed"))
    status = "fail" if failed else ("pass" if passed else "unknown")
    return {"found": True, "passed": passed, "failed": failed, "status": status}


def _integer_metric(mapping: Any) -> int | None:
    if not isinstance(mapping, dict):
        return None
    for key in ("cell_count", "num_cells"):
        value = mapping.get(key)
        if isinstance(value, int) and not isinstance(value, bool):
            return value
    return None


def extract_cell_count(payload: dict[str, Any]) -> int | None:
    """Extract a simple cell-count proxy from common Yosys JSON shapes."""
    for candidate in (payload, payload.get("design"), payload.get("stats")):
        count = _integer_metric(candidate)
        if count is not None:
            return count

    modules = payload.get("modules")
    if not isinstance(modules, dict):
        return None
    module_values = [module for module in modules.values() if isinstance(module, dict)]
    top_modules = [
        module
        for module in module_values
        if str(module.get("attributes", {}).get("top", "0")) in {"1", "00000000000000000000000000000001"}
    ]
    selected = top_modules or module_values
    counts = [len(module["cells"]) for module in selected if isinstance(module.get("cells"), dict)]
    return sum(counts) if counts else None


def parse_synthesis_json(path: str | Path) -> dict[str, Any]:
    path = Path(path)
    if not path.is_file():
        return {"found": False, "status": "missing"}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        return {"found": True, "status": "unparseable", "error": str(exc)}
    if not isinstance(payload, dict):
        return {"found": True, "status": "unparseable", "error": "JSON root is not an object"}
    cell_count = extract_cell_count(payload)
    result: dict[str, Any] = {"found": True, "status": "available"}
    if cell_count is not None:
        result["cell_count"] = cell_count
    return result


def collect_rtl_summary(input_dir: str | Path = "results/rtl") -> dict[str, Any]:
    directory = Path(input_dir)
    simulations = {
        name: parse_simulation_log(directory / f"sim_{name}.log") for name in BASELINES
    }
    synthesis = {
        name: parse_synthesis_json(directory / f"synth_{name}.json") for name in BASELINES
    }
    cell_counts = {
        name: values["cell_count"]
        for name, values in synthesis.items()
        if isinstance(values.get("cell_count"), int)
    }
    available_simulations = [values for values in simulations.values() if values["found"]]
    lowest = min(cell_counts, key=lambda name: (cell_counts[name], name)) if cell_counts else None
    summary: dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "simulations": simulations,
        "synthesis": synthesis,
        "recommendation_context": {
            "baseline_rtl_available": bool(available_simulations or any(v["found"] for v in synthesis.values())),
            "all_available_sims_pass": bool(available_simulations)
            and all(values["status"] == "pass" for values in available_simulations),
            "lowest_cell_count_baseline": lowest,
        },
        "note": (
            "Open-source RTL simulation and synthesis results depend on local tools and are not silicon signoff. "
            "Cell counts are synthesis proxies; no measured silicon power is reported."
        ),
    }
    activity_path = directory / "rtl_activity_summary.json"
    if activity_path.is_file():
        try:
            activity = json.loads(activity_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            activity = {"status": "unparseable", "error": str(exc)}
        if isinstance(activity, dict):
            summary["activity"] = activity
    return summary


def render_rtl_report(summary: dict[str, Any], input_dir: str | Path = "results/rtl") -> str:
    directory = Path(input_dir)
    lines = [
        "# RTL Baseline Results Report",
        "",
        "## Inputs Found",
        "",
        "| Input | Found |",
        "|---|---|",
    ]
    for name in BASELINES:
        lines.append(f"| `{directory / f'sim_{name}.log'}` | {'yes' if summary['simulations'][name]['found'] else 'no'} |")
        lines.append(f"| `{directory / f'synth_{name}.json'}` | {'yes' if summary['synthesis'][name]['found'] else 'no'} |")
    lines.extend(["", "## Simulation Summary", "", "| Baseline | Status | Passed | Failed |", "|---|---|---:|---:|"])
    for name, values in summary["simulations"].items():
        lines.append(f"| {name} | {values['status']} | {values.get('passed', '-')} | {values.get('failed', '-')} |")
    lines.extend(["", "## Synthesis Summary", "", "| Baseline | Status | Cell Count Proxy |", "|---|---|---:|"])
    for name, values in summary["synthesis"].items():
        lines.append(f"| {name} | {values['status']} | {values.get('cell_count', '-')} |")
    lowest = summary["recommendation_context"]["lowest_cell_count_baseline"]
    lines.extend(["", "## Baseline Comparison", ""])
    if lowest:
        count = summary["synthesis"][lowest]["cell_count"]
        lines.append(f"- Lowest available cell-count proxy: `{lowest}` with `{count}` cells.")
    else:
        lines.append("- No parseable synthesis cell counts are available.")
    if not any(values["found"] for values in summary["simulations"].values()):
        lines.append("- No simulation logs were found; run the optional RTL simulation flow to add evidence.")
    if "activity" in summary:
        _append_activity_section(lines, summary["activity"])
    lines.extend(["", "## Notes and Limitations", "", summary["note"], ""])
    return "\n".join(lines)


def _append_activity_section(lines: list[str], activity: dict[str, Any]) -> None:
    lines.extend(["", "## Toggle Activity Summary", ""])
    baselines = activity.get("baselines", {})
    if not isinstance(baselines, dict):
        lines.append("- RTL activity summary was present but not parseable.")
        return
    lines.extend(["| Baseline | Status | Total Toggles |", "|---|---|---:|"])
    toggle_counts: dict[str, int] = {}
    for name in BASELINES:
        values = baselines.get(name, {})
        if not isinstance(values, dict):
            values = {}
        total = values.get("total_toggles", "-")
        if isinstance(total, int):
            toggle_counts[name] = total
        lines.append(f"| {name} | {values.get('status', 'missing')} | {total} |")
    lowest = activity.get("recommendation_context", {}).get("lowest_toggle_baseline")
    if lowest:
        lines.append(f"\n- Lowest available toggle-count baseline: `{lowest}`.")
    elif not toggle_counts:
        lines.append("\n- No parseable VCD toggle counts are available.")
    lines.append("- Toggle counts are simulation activity proxies and are not measured silicon power or energy.")


def summarize_rtl_results(
    input_dir: str | Path = "results/rtl",
    output_dir: str | Path | None = None,
) -> dict[str, Any]:
    input_directory = Path(input_dir)
    output_directory = Path(output_dir) if output_dir is not None else input_directory
    output_directory.mkdir(parents=True, exist_ok=True)
    summary = collect_rtl_summary(input_directory)
    json_path = output_directory / "rtl_summary.json"
    report_path = output_directory / "rtl_report.md"
    json_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    report_path.write_text(render_rtl_report(summary, input_directory), encoding="utf-8")
    print(f"RTL summary written: {json_path}")
    print(f"RTL report written: {report_path}")
    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Summarize available RTL baseline outputs.")
    parser.add_argument("--input-dir", type=Path, default=Path("results/rtl"))
    parser.add_argument("--output-dir", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        summarize_rtl_results(args.input_dir, args.output_dir)
        return 0
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
