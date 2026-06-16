from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Any, Iterable


EXPECTED_OUTPUTS = (
    "results/benchmark_results.json",
    "results/benchmark_report.md",
    "results/sweeps/sweep_results.json",
    "results/sweeps/sweep_summary.csv",
    "results/sweeps/sweep_report.md",
    "results/snn_search/search_results.json",
    "results/snn_search/search_summary.csv",
    "results/snn_search/search_report.md",
    "results/temporal_sweeps/sweep_results.json",
    "results/temporal_sweeps/sweep_summary.csv",
    "results/temporal_sweeps/sweep_report.md",
    "results/temporal_snn_search/search_results.json",
    "results/temporal_snn_search/search_summary.csv",
    "results/temporal_snn_search/search_report.md",
    "results/rtl/rtl_summary.json",
    "results/rtl/rtl_report.md",
    "results/rtl/rtl_activity_summary.json",
    "results/rtl/rtl_activity_report.md",
    "results/rtl/rtl_comparison_summary.json",
    "results/rtl/rtl_comparison_report.md",
    "results/research_decision_summary.json",
    "results/research_decision_report.md",
    "results/evidence_manifest.json",
    "results/evidence_manifest.md",
)

LIMITATION_NOTE = (
    "RTL simulation, synthesis, and toggle evidence depends on local tool availability "
    "and is not silicon signoff."
)


def inspect_output(path: Path, display_path: str) -> dict[str, Any]:
    found = path.is_file()
    entry: dict[str, Any] = {"path": display_path, "found": found}
    if found:
        stat = path.stat()
        entry["size_bytes"] = stat.st_size
        entry["modified_at"] = datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat()
    return entry


def collect_manifest(
    root_dir: str | Path = ".",
    expected_outputs: Iterable[str] = EXPECTED_OUTPUTS,
) -> dict[str, Any]:
    root = Path(root_dir)
    outputs = [
        inspect_output(root / relative_path, relative_path)
        for relative_path in expected_outputs
    ]
    missing = [entry["path"] for entry in outputs if not entry["found"]]
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "outputs": outputs,
        "missing_outputs": missing,
        "complete": not missing,
        "note": LIMITATION_NOTE,
    }


def render_manifest_report(manifest: dict[str, Any]) -> str:
    lines = [
        "# Evidence Pipeline Manifest",
        "",
        "## Generated Outputs",
        "",
        "| Path | Found | Size Bytes | Modified At |",
        "|---|---|---:|---|",
    ]
    for entry in manifest["outputs"]:
        lines.append(
            f"| `{entry['path']}` | {'yes' if entry['found'] else 'no'} | "
            f"{entry.get('size_bytes', '-')} | {entry.get('modified_at', '-')} |"
        )
    lines.extend(["", "## Missing Outputs", ""])
    if manifest["missing_outputs"]:
        lines.extend(f"- `{path}`" for path in manifest["missing_outputs"])
    else:
        lines.append("- None.")
    lines.extend(["", "## Notes and Limitations", "", manifest["note"], ""])
    return "\n".join(lines)


def build_evidence_manifest(
    root_dir: str | Path = ".",
    output_dir: str | Path | None = None,
    expected_outputs: Iterable[str] = EXPECTED_OUTPUTS,
) -> dict[str, Any]:
    root = Path(root_dir)
    directory = Path(output_dir) if output_dir is not None else root / "results"
    directory.mkdir(parents=True, exist_ok=True)
    json_path = directory / "evidence_manifest.json"
    markdown_path = directory / "evidence_manifest.md"
    manifest = collect_manifest(root, expected_outputs)
    for _ in range(2):
        json_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        markdown_path.write_text(render_manifest_report(manifest), encoding="utf-8")
        manifest = collect_manifest(root, expected_outputs)
    json_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    markdown_path.write_text(render_manifest_report(manifest), encoding="utf-8")
    print(f"Evidence manifest written: {json_path}")
    print(f"Evidence manifest report written: {markdown_path}")
    return manifest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build an evidence pipeline manifest.")
    parser.add_argument("--root-dir", type=Path, default=Path("."))
    parser.add_argument("--output-dir", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        build_evidence_manifest(args.root_dir, args.output_dir)
        return 0
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
