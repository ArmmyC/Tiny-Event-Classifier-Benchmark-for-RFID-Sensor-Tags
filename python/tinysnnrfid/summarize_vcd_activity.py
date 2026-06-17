from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Any

from tinysnnrfid.rtl_status import design_output_was_written, load_status, stale_result, utc_now, write_status


BASELINES = ("threshold", "fsm", "lut_like", "tiny_snn_v2", "tiny_snn_v2_sparse_activity")


def _clean_signal_name(raw: str) -> str:
    return raw.split()[0].replace("[", "_").replace("]", "").replace(":", "_")


def parse_vcd_activity(path: str | Path, top_n: int = 10) -> dict[str, Any]:
    path = Path(path)
    if not path.is_file():
        return {"found": False, "status": "missing"}

    id_to_signal: dict[str, str] = {}
    last_values: dict[str, str] = {}
    toggles: dict[str, int] = {}
    in_definitions = True

    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError as exc:
        return {"found": True, "status": "unreadable", "error": str(exc)}

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue
        if in_definitions:
            if line.startswith("$var "):
                parts = line.split()
                if len(parts) >= 5:
                    identifier = parts[3]
                    signal = _clean_signal_name(" ".join(parts[4:-1]))
                    id_to_signal[identifier] = signal
                    toggles.setdefault(identifier, 0)
            elif line.startswith("$enddefinitions"):
                in_definitions = False
            continue
        if line[0] in "#$":
            continue

        identifier: str | None = None
        value: str | None = None
        if line[0] in "01xzXZ":
            value = line[0].lower()
            identifier = line[1:]
        elif line[0] in "bBrR":
            parts = line.split(maxsplit=1)
            if len(parts) == 2:
                value = parts[0].lower()
                identifier = parts[1]
        if not identifier or identifier not in id_to_signal or value is None:
            continue

        previous = last_values.get(identifier)
        if previous is not None and previous != value:
            toggles[identifier] = toggles.get(identifier, 0) + 1
        last_values[identifier] = value

    named_toggles = [
        {"signal": id_to_signal[identifier], "toggles": count}
        for identifier, count in toggles.items()
        if identifier in id_to_signal
    ]
    named_toggles.sort(key=lambda item: (-item["toggles"], item["signal"]))
    return {
        "found": True,
        "status": "available",
        "signal_count": len(id_to_signal),
        "total_toggles": sum(toggles.values()),
        "top_toggled_signals": named_toggles[:top_n],
    }


def collect_activity_summary(input_dir: str | Path = "results/rtl") -> dict[str, Any]:
    directory = Path(input_dir)
    sim_status = load_status(directory, "sim")
    baselines = {
        name: (
            parse_vcd_activity(directory / f"vcd_{name}.vcd")
            if design_output_was_written(sim_status, name, f"vcd_{name}.vcd")
            else stale_result(
                directory / f"vcd_{name}.vcd",
                reason=_stale_reason(sim_status),
            )
        )
        for name in BASELINES
    }
    toggle_counts = {
        name: values["total_toggles"]
        for name, values in baselines.items()
        if isinstance(values.get("total_toggles"), int)
    }
    lowest = min(toggle_counts, key=lambda name: (toggle_counts[name], name)) if toggle_counts else None
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": {
            "simulation": sim_status or {"status": "missing", "note": "sim_status.json was not found."},
        },
        "baselines": baselines,
        "recommendation_context": {
            "activity_vcd_available": bool(toggle_counts),
            "lowest_toggle_baseline": lowest,
        },
        "note": (
            "Toggle counts are simulation activity proxies and are not measured silicon power or energy."
        ),
    }


def _stale_reason(status: dict[str, Any] | None) -> str:
    if not isinstance(status, dict):
        return "Current-run simulation status file sim_status.json is missing; existing VCD artifacts are stale."
    if status.get("status") == "skipped":
        missing_tools = status.get("missing_tools", [])
        tools = ", ".join(missing_tools) if isinstance(missing_tools, list) else ""
        if not tools:
            return "Current-run simulation was skipped because required tools were missing; existing VCD artifacts are stale."
        verb = "was" if len(missing_tools) == 1 else "were"
        return f"Current-run simulation was skipped because {tools} {verb} missing; existing VCD artifacts are stale."
    if status.get("status") == "fail":
        return "Current-run simulation failed and did not produce this VCD; existing VCD artifacts are stale."
    return "Current-run simulation did not list this VCD output; existing VCD artifacts are stale."


def render_activity_report(summary: dict[str, Any], input_dir: str | Path = "results/rtl") -> str:
    directory = Path(input_dir)
    lines = [
        "# RTL Toggle Activity Report",
        "",
        "## Inputs Found",
        "",
        "| Input | Found |",
        "|---|---|",
    ]
    for name in BASELINES:
        values = summary["baselines"][name]
        lines.append(f"| `{directory / f'vcd_{name}.vcd'}` | {'yes' if values['found'] else 'no'} |")
    sim = summary.get("status", {}).get("simulation", {})
    if isinstance(sim, dict) and sim.get("status") != "pass":
        lines.extend(
            [
                "",
                "## Current-Run Status",
                "",
                "- "
                + (
                    sim.get("note")
                    or "RTL simulation evidence is incomplete; previous VCD files were ignored as stale."
                ),
            ]
        )
    lines.extend(["", "## Toggle Summary", "", "| Baseline | Status | Signals | Total Toggles |", "|---|---|---:|---:|"])
    for name, values in summary["baselines"].items():
        lines.append(
            f"| {name} | {values['status']} | {values.get('signal_count', '-')} | {values.get('total_toggles', '-')} |"
        )
    lines.extend(["", "## Highest Toggle Signals", ""])
    for name, values in summary["baselines"].items():
        lines.append(f"### {name}")
        top = values.get("top_toggled_signals", [])
        if not top:
            lines.append("- No VCD toggle data available.")
            lines.append("")
            continue
        for row in top[:5]:
            lines.append(f"- `{row['signal']}`: `{row['toggles']}` toggles")
        lines.append("")
    lines.extend(["## Notes and Limitations", "", summary["note"], ""])
    return "\n".join(lines)


def summarize_vcd_activity(
    input_dir: str | Path = "results/rtl",
    output_dir: str | Path | None = None,
) -> dict[str, Any]:
    started_at = utc_now()
    input_directory = Path(input_dir)
    output_directory = Path(output_dir) if output_dir is not None else input_directory
    output_directory.mkdir(parents=True, exist_ok=True)
    summary = collect_activity_summary(input_directory)
    json_path = output_directory / "rtl_activity_summary.json"
    report_path = output_directory / "rtl_activity_report.md"
    json_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    report_path.write_text(render_activity_report(summary, input_directory), encoding="utf-8")
    sim = summary.get("status", {}).get("simulation", {})
    status_value = "pass" if summary["recommendation_context"]["activity_vcd_available"] else "fail"
    note = "RTL activity summary completed in the current run."
    if isinstance(sim, dict) and sim.get("status") != "pass":
        status_value = "skipped"
        note = (
            sim.get("note")
            or "RTL activity was skipped because current simulation evidence was unavailable; stale VCDs were ignored."
        )
    write_status(
        output_directory,
        "activity",
        started_at=started_at,
        status=status_value,
        missing_tools=sim.get("missing_tools", []) if isinstance(sim, dict) else [],
        outputs_written=["rtl_activity_summary.json", "rtl_activity_report.md"],
        return_codes={},
        note=note,
    )
    print(f"RTL activity summary written: {json_path}")
    print(f"RTL activity report written: {report_path}")
    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Summarize RTL VCD toggle activity proxies.")
    parser.add_argument("--input-dir", type=Path, default=Path("results/rtl"))
    parser.add_argument("--output-dir", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        summarize_vcd_activity(args.input_dir, args.output_dir)
        return 0
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
