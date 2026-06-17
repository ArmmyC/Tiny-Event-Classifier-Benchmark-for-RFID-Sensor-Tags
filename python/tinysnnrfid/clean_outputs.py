from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import shutil
import sys


FILE_PATTERNS: tuple[str, ...] = (
    "data/generated/*.npy",
    "data/generated/*.npz",
    "data/generated/*.txt",
    "data/generated/*.hex",
    "data/generated/metadata.json",
    "results/benchmark_results.json",
    "results/benchmark_report.md",
    "results/research_decision_report.md",
    "results/research_decision_summary.json",
    "results/evidence_manifest.json",
    "results/evidence_manifest.md",
    "results/artifact_card.json",
    "results/artifact_card.md",
    "results/research_writeup.md",
    "results/research_writeup_summary.json",
    "results/rtl/toolchain_status.json",
    "results/rtl/toolchain_status.md",
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
    "results/temporal_snn_optimized/search_results.json",
    "results/temporal_snn_optimized/search_summary.csv",
    "results/temporal_snn_optimized/search_report.md",
    "results/temporal_snn_optimized/optimization_gate.json",
    "results/temporal_snn_optimized/optimization_gate.md",
    "results/temporal_snn_v2_search/search_results.json",
    "results/temporal_snn_v2_search/search_summary.csv",
    "results/temporal_snn_v2_search/search_report.md",
    "results/temporal_snn_v2_search/optimization_gate.json",
    "results/temporal_snn_v2_search/optimization_gate.md",
    "results/accuracy/*.json",
    "results/vcd/*.vcd",
    "sim.out",
)

DIRECTORIES: tuple[str, ...] = (
    "results/sweeps/generated",
    "results/sweeps/runs",
    "results/snn_search/generated",
    "results/snn_search/runs",
    "results/temporal_sweeps/generated",
    "results/temporal_sweeps/runs",
    "results/temporal_snn_search/generated",
    "results/temporal_snn_search/runs",
    "results/temporal_snn_optimized/generated",
    "results/temporal_snn_optimized/runs",
    "results/temporal_snn_v2_search/generated",
    "results/temporal_snn_v2_search/runs",
    "results/rtl",
    "results/smoke",
)


@dataclass(frozen=True)
class CleanSummary:
    removed_files: int
    removed_directories: int
    missing_patterns: int


def _is_within_root(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root)
    except ValueError:
        return False
    return True


def clean_outputs(root: str | Path = ".") -> CleanSummary:
    root_path = Path(root).resolve()
    removed_files = 0
    removed_dirs = 0
    missing_patterns = 0

    for pattern in FILE_PATTERNS:
        matches = [path for path in root_path.glob(pattern) if path.is_file()]
        if not matches:
            missing_patterns += 1
            continue
        for path in matches:
            if not _is_within_root(path, root_path):
                raise ValueError(f"Refusing to remove path outside project root: {path}")
            path.unlink()
            removed_files += 1

    for directory in DIRECTORIES:
        path = root_path / directory
        if not path.exists():
            missing_patterns += 1
            continue
        if not path.is_dir():
            continue
        if not _is_within_root(path, root_path):
            raise ValueError(f"Refusing to remove path outside project root: {path}")
        shutil.rmtree(path)
        removed_dirs += 1

    return CleanSummary(
        removed_files=removed_files,
        removed_directories=removed_dirs,
        missing_patterns=missing_patterns,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Remove generated project outputs.")
    parser.add_argument("--root", type=Path, default=Path("."))
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        summary = clean_outputs(args.root)
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(
        "Cleaned generated outputs: "
        f"{summary.removed_files} file(s), "
        f"{summary.removed_directories} directory/directories removed; "
        f"{summary.missing_patterns} missing pattern(s) ignored."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
