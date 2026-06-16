from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any, Callable


PROXY_LIMITATION = (
    "RTL simulation, synthesis, and VCD activity results are local-tool proxies, "
    "not silicon signoff, silicon area, or measured power."
)


TOOLS: dict[str, dict[str, Any]] = {
    "bash": {
        "version_args": ["--version"],
        "role": "Runs the repository RTL helper scripts.",
        "required_for": ["rtl-sim", "rtl-synth"],
    },
    "iverilog": {
        "version_args": ["-V"],
        "role": "Compiles SystemVerilog testbenches for RTL simulation.",
        "required_for": ["rtl-sim"],
    },
    "vvp": {
        "version_args": ["-V"],
        "role": "Runs Icarus Verilog simulation outputs and emits VCD traces.",
        "required_for": ["rtl-sim", "rtl-activity"],
    },
    "yosys": {
        "version_args": ["-V"],
        "role": "Runs open-source RTL synthesis for cell-count proxy evidence.",
        "required_for": ["rtl-synth"],
    },
}


WhichFunc = Callable[[str], str | None]
RunFunc = Callable[..., subprocess.CompletedProcess[str]]


def _first_nonempty_line(text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return ""


def check_tool(
    name: str,
    metadata: dict[str, Any],
    *,
    which: WhichFunc = shutil.which,
    run: RunFunc = subprocess.run,
) -> dict[str, Any]:
    path = which(name)
    result: dict[str, Any] = {
        "found": path is not None,
        "path": path,
        "version_available": False,
        "version": None,
        "role": metadata["role"],
        "required_for": list(metadata["required_for"]),
    }
    if path is None:
        return result

    command = [path, *metadata["version_args"]]
    try:
        completed = run(
            command,
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        result["version"] = f"version check failed: {exc}"
        return result

    output = "\n".join(part for part in (completed.stdout, completed.stderr) if part)
    first_line = _first_nonempty_line(output)
    if completed.returncode == 0 and first_line:
        result["version_available"] = True
        result["version"] = first_line
    else:
        detail = first_line or f"command exited with status {completed.returncode}"
        result["version"] = f"version check failed: {detail}"
    return result


def collect_toolchain_status(
    *,
    which: WhichFunc = shutil.which,
    run: RunFunc = subprocess.run,
) -> dict[str, Any]:
    tools = {
        name: check_tool(name, metadata, which=which, run=run)
        for name, metadata in TOOLS.items()
    }
    missing = [name for name, values in tools.items() if not values["found"]]
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "tools": tools,
        "all_required_found": not missing,
        "missing_required_tools": missing,
        "note": PROXY_LIMITATION,
    }


def render_markdown(status: dict[str, Any]) -> str:
    lines = [
        "# RTL Toolchain Doctor",
        "",
        "## Summary",
        "",
        f"- All required tools found: `{'yes' if status['all_required_found'] else 'no'}`.",
    ]
    missing = status["missing_required_tools"]
    if missing:
        lines.append(f"- Missing required tools: `{', '.join(missing)}`.")
    else:
        lines.append("- Missing required tools: `none`.")
    lines.extend(
        [
            "",
            "## Tool Status",
            "",
            "| Tool | Found | Path | Version Available | Version | Required For | Role |",
            "|---|---|---|---|---|---|---|",
        ]
    )
    for name, values in status["tools"].items():
        path = values["path"] if values["path"] is not None else "-"
        version = values["version"] if values["version"] is not None else "-"
        required_for = ", ".join(values["required_for"])
        lines.append(
            f"| {name} | {'yes' if values['found'] else 'no'} | `{path}` | "
            f"{'yes' if values['version_available'] else 'no'} | {version} | "
            f"{required_for} | {values['role']} |"
        )

    lines.extend(["", "## Missing Tools", ""])
    if missing:
        for name in missing:
            required_for = ", ".join(status["tools"][name]["required_for"])
            lines.append(f"- `{name}` is missing; required for {required_for}.")
    else:
        lines.append("- No required RTL tools are missing.")

    lines.extend(
        [
            "",
            "## Notes and Limitations",
            "",
            status["note"],
            "This command only reports local tool availability. It does not install tools, modify PATH, or make network calls.",
            "",
        ]
    )
    return "\n".join(lines)


def write_toolchain_status(
    output_dir: str | Path = "results/rtl",
    *,
    which: WhichFunc = shutil.which,
    run: RunFunc = subprocess.run,
) -> dict[str, Any]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    status = collect_toolchain_status(which=which, run=run)
    json_path = output_path / "toolchain_status.json"
    markdown_path = output_path / "toolchain_status.md"
    json_path.write_text(json.dumps(status, indent=2), encoding="utf-8")
    markdown_path.write_text(render_markdown(status), encoding="utf-8")
    print(f"RTL toolchain status written: {json_path}")
    print(f"RTL toolchain report written: {markdown_path}")
    return status


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check optional RTL simulation and synthesis tool availability.")
    parser.add_argument("--output-dir", type=Path, default=Path("results/rtl"))
    parser.add_argument("--strict", action="store_true", help="Exit nonzero if any required RTL tool is missing.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        status = write_toolchain_status(args.output_dir)
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if args.strict and not status["all_required_found"]:
        missing = ", ".join(status["missing_required_tools"])
        print(f"error: missing required RTL tools: {missing}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
