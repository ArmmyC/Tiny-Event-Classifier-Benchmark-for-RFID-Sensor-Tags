from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Any

from .build_evidence_manifest import build_evidence_manifest
from .build_research_report import build_research_report
from .compare_rtl_designs import compare_rtl_designs
from .config import load_config
from .dataset import DatasetConfig, save_dataset
from .export_rtl_vectors import export_rtl_vectors
from .run_benchmark import run_benchmark
from .run_snn_search import run_snn_search
from .run_sweep import run_sweep
from .summarize_rtl_results import summarize_rtl_results
from .summarize_vcd_activity import summarize_vcd_activity


SMOKE_NOTE = "Smoke evidence uses tiny configs and is not a final benchmark result."

OPTIONAL_RTL_TOOL_OUTPUTS = (
    "rtl/sim_threshold.log",
    "rtl/sim_fsm.log",
    "rtl/sim_lut_like.log",
    "rtl/sim_tiny_snn_v2.log",
    "rtl/synth_threshold.json",
    "rtl/synth_fsm.json",
    "rtl/synth_lut_like.json",
    "rtl/synth_tiny_snn_v2.json",
    "rtl/vcd_threshold.vcd",
    "rtl/vcd_fsm.vcd",
    "rtl/vcd_lut_like.vcd",
    "rtl/vcd_tiny_snn_v2.vcd",
)

SMOKE_EXPECTED_OUTPUTS = (
    "benchmark_results.json",
    "benchmark_report.md",
    "sweeps/sweep_results.json",
    "sweeps/sweep_summary.csv",
    "sweeps/sweep_report.md",
    "snn_search/search_results.json",
    "snn_search/search_summary.csv",
    "snn_search/search_report.md",
    "temporal_sweeps/sweep_results.json",
    "temporal_sweeps/sweep_summary.csv",
    "temporal_sweeps/sweep_report.md",
    "temporal_snn_search/search_results.json",
    "temporal_snn_search/search_summary.csv",
    "temporal_snn_search/search_report.md",
    "rtl/vectors.svh",
    "rtl/rtl_activity_summary.json",
    "rtl/rtl_activity_report.md",
    "rtl/rtl_summary.json",
    "rtl/rtl_report.md",
    "rtl/rtl_comparison_summary.json",
    "rtl/rtl_comparison_report.md",
    "research_decision_summary.json",
    "research_decision_report.md",
    "evidence_manifest.json",
    "evidence_manifest.md",
    "smoke_summary.json",
    "smoke_report.md",
)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _tiny_config(base: dict[str, Any], output_dir: Path, data_dir: Path, seed: int) -> dict[str, Any]:
    config = deepcopy(base)
    config["dataset"].update(
        {
            "num_samples": 24,
            "sequence_length": 16,
            "input_width": 4,
            "positive_ratio": 0.5,
            "noise_probability": 0.02,
            "jitter_probability": 0.1,
            "dropout_probability": 0.05,
            "max_jitter": 1,
            "max_gap": 3,
            "random_seed": seed,
        }
    )
    config["scenario"]["dense_noise_spike_threshold"] = 6
    config["paths"]["data_dir"] = str(data_dir)
    config["paths"]["results_dir"] = str(output_dir)
    return config


def _tiny_temporal_config(base: dict[str, Any], output_dir: Path, data_dir: Path) -> dict[str, Any]:
    config = _tiny_config(base, output_dir, data_dir, seed=2026)
    config["dataset"].update({"jitter_probability": 0.0, "dropout_probability": 0.0})
    config["scenario_suite"] = {
        "mode": "temporal_hard",
        "mix": {
            "clean_positive": 0.15,
            "long_gap_positive": 0.10,
            "distractor_positive": 0.10,
            "dropout_positive": 0.10,
            "reversed_negative": 0.15,
            "partial_order_negative": 0.15,
            "burst_noise_negative": 0.15,
            "near_miss_negative": 0.10,
        },
        "max_long_gap": 6,
        "burst_length": 3,
        "distractor_count": 1,
        "allow_legacy_tags": True,
    }
    return config


def _write_smoke_configs(root_dir: Path, output_dir: Path) -> dict[str, Path]:
    configs_dir = output_dir / "configs"
    legacy = _tiny_config(
        load_config(root_dir / "configs" / "default.json"),
        output_dir,
        output_dir / "data" / "benchmark",
        seed=1234,
    )
    temporal = _tiny_temporal_config(
        load_config(root_dir / "configs" / "temporal_hard.json"),
        output_dir / "temporal_benchmark",
        output_dir / "data" / "temporal_benchmark",
    )
    paths = {
        "legacy": configs_dir / "smoke_default.json",
        "temporal": configs_dir / "smoke_temporal_hard.json",
        "sweep": configs_dir / "smoke_sweep.json",
        "search": configs_dir / "smoke_snn_search.json",
        "temporal_sweep": configs_dir / "smoke_temporal_sweep.json",
        "temporal_search": configs_dir / "smoke_temporal_snn_search.json",
    }
    _write_json(paths["legacy"], legacy)
    _write_json(paths["temporal"], temporal)
    _write_json(
        paths["sweep"],
        _tiny_sweep_config(paths["legacy"], output_dir / "sweeps", output_dir / "sweeps" / "generated"),
    )
    _write_json(
        paths["search"],
        _tiny_search_config(paths["legacy"], output_dir / "snn_search", output_dir / "snn_search" / "generated"),
    )
    _write_json(
        paths["temporal_sweep"],
        _tiny_sweep_config(
            paths["temporal"],
            output_dir / "temporal_sweeps",
            output_dir / "temporal_sweeps" / "generated",
        ),
    )
    _write_json(
        paths["temporal_search"],
        _tiny_search_config(
            paths["temporal"],
            output_dir / "temporal_snn_search",
            output_dir / "temporal_snn_search" / "generated",
        ),
    )
    return paths


def _tiny_sweep_config(base_config: Path, output_dir: Path, dataset_root: Path) -> dict[str, Any]:
    return {
        "name": "smoke_sweep",
        "base_config": str(base_config),
        "output_dir": str(output_dir),
        "dataset_output_root": str(dataset_root),
        "seeds": [101],
        "parameters": {"dataset.noise_probability": [0.02]},
        "comparison": {
            "candidate_classifier": "tiny_snn_v2",
            "reference_classifier": "fsm",
            "f1_tolerance": 0.05,
        },
    }


def _tiny_search_config(base_config: Path, output_dir: Path, dataset_root: Path) -> dict[str, Any]:
    return {
        "name": "smoke_snn_search",
        "base_config": str(base_config),
        "output_dir": str(output_dir),
        "dataset_output_root": str(dataset_root),
        "seeds": [202],
        "dataset_parameters": {"dataset.noise_probability": [0.02]},
        "snn_parameters": {
            "classifiers.tiny_snn_v2.hidden_threshold": [4],
            "classifiers.tiny_snn_v2.output_threshold": [3],
            "classifiers.tiny_snn_v2.leak": [1],
            "classifiers.tiny_snn_v2.reset_on_spike": [True],
        },
        "weight_variants": ["current_default", "balanced_small_int"],
        "comparison": {
            "candidate_classifier": "tiny_snn_v2",
            "reference_classifier": "fsm",
            "f1_tolerance": 0.05,
        },
        "selection": {"strategy": "prefix"},
        "limits": {"max_candidates": 2},
    }


def _collect_outputs(output_dir: Path, paths: tuple[str, ...]) -> list[dict[str, Any]]:
    outputs: list[dict[str, Any]] = []
    for relative_path in paths:
        path = output_dir / relative_path
        entry: dict[str, Any] = {"path": str(path), "found": path.is_file()}
        if path.is_file():
            entry["size_bytes"] = path.stat().st_size
        outputs.append(entry)
    return outputs


def _missing_paths(output_dir: Path, paths: tuple[str, ...]) -> list[str]:
    return [relative_path for relative_path in paths if not (output_dir / relative_path).is_file()]


def render_smoke_report(summary: dict[str, Any]) -> str:
    lines = [
        "# Evidence Smoke Report",
        "",
        summary["note"],
        "",
        "Smoke outputs are not final benchmark results; use `make evidence` for the full reproducible evidence pipeline.",
        "",
        f"- Status: `{summary['status']}`",
        f"- Output directory: `{summary['output_dir']}`",
        "",
        "## Required Outputs",
        "",
        "| Path | Found | Size Bytes |",
        "|---|---|---:|",
    ]
    for entry in summary["outputs"]:
        lines.append(
            f"| `{entry['path']}` | {'yes' if entry['found'] else 'no'} | {entry.get('size_bytes', '-')} |"
        )
    lines.extend(["", "## Optional RTL Tool Outputs", ""])
    if summary["missing_optional_outputs"]:
        lines.append("These are allowed to be missing in smoke mode because Icarus Verilog/Yosys are not required:")
        lines.extend(f"- `{path}`" for path in summary["missing_optional_outputs"])
    else:
        lines.append("- All optional RTL tool outputs were present.")
    lines.extend(
        [
            "",
            "## Limitations",
            "",
            "RTL simulation, synthesis, and VCD activity from open-source tools are optional local evidence, "
            "not silicon signoff, measured silicon power, or measured energy.",
            "",
        ]
    )
    return "\n".join(lines)


def write_smoke_outputs(output_dir: Path, summary: dict[str, Any]) -> None:
    summary_path = output_dir / "smoke_summary.json"
    report_path = output_dir / "smoke_report.md"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    report_path.write_text(render_smoke_report(summary), encoding="utf-8")


def run_evidence_smoke(
    root_dir: str | Path = ".",
    output_dir: str | Path = "results/smoke",
) -> dict[str, Any]:
    root = Path(root_dir)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    config_paths = _write_smoke_configs(root, output)

    legacy_config = load_config(config_paths["legacy"])
    save_dataset(
        Path(legacy_config["paths"]["data_dir"]),
        DatasetConfig.from_mapping(legacy_config["dataset"], legacy_config["scenario"], legacy_config.get("scenario_suite")),
        legacy_config,
    )
    run_benchmark(legacy_config, Path(legacy_config["paths"]["data_dir"]), output)

    run_sweep(json.loads(config_paths["sweep"].read_text(encoding="utf-8")), max_runs=1)
    run_snn_search(json.loads(config_paths["search"].read_text(encoding="utf-8")), max_candidates=2)
    run_sweep(json.loads(config_paths["temporal_sweep"].read_text(encoding="utf-8")), max_runs=1)
    run_snn_search(json.loads(config_paths["temporal_search"].read_text(encoding="utf-8")), max_candidates=2)

    temporal_config = load_config(config_paths["temporal"])
    temporal_data_dir = Path(temporal_config["paths"]["data_dir"])
    save_dataset(
        temporal_data_dir,
        DatasetConfig.from_mapping(
            temporal_config["dataset"],
            temporal_config["scenario"],
            temporal_config.get("scenario_suite"),
        ),
        temporal_config,
    )
    export_rtl_vectors(config_paths["temporal"], output / "rtl" / "vectors.svh", temporal_data_dir, limit=4)

    summarize_vcd_activity(output / "rtl")
    summarize_rtl_results(output / "rtl")
    compare_rtl_designs(output / "rtl")
    build_research_report(
        output_dir=output,
        input_paths={
            "legacy_benchmark": output / "benchmark_results.json",
            "legacy_sweep": output / "sweeps" / "sweep_results.json",
            "legacy_snn_search": output / "snn_search" / "search_results.json",
            "temporal_sweep": output / "temporal_sweeps" / "sweep_results.json",
            "temporal_snn_search": output / "temporal_snn_search" / "search_results.json",
            "rtl_baselines": output / "rtl" / "rtl_summary.json",
            "rtl_comparison": output / "rtl" / "rtl_comparison_summary.json",
        },
    )

    placeholder_summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "pass",
        "output_dir": str(output),
        "outputs": _collect_outputs(output, SMOKE_EXPECTED_OUTPUTS),
        "missing_optional_outputs": _missing_paths(output, OPTIONAL_RTL_TOOL_OUTPUTS),
        "note": SMOKE_NOTE,
    }
    write_smoke_outputs(output, placeholder_summary)
    build_evidence_manifest(output, output, SMOKE_EXPECTED_OUTPUTS)

    outputs = _collect_outputs(output, SMOKE_EXPECTED_OUTPUTS)
    missing_required = [entry["path"] for entry in outputs if not entry["found"]]
    status = "fail" if missing_required else "pass"
    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "output_dir": str(output),
        "outputs": outputs,
        "missing_required_outputs": missing_required,
        "missing_optional_outputs": _missing_paths(output, OPTIONAL_RTL_TOOL_OUTPUTS),
        "note": SMOKE_NOTE,
    }
    write_smoke_outputs(output, summary)
    if missing_required:
        raise ValueError(f"Missing required smoke output(s): {', '.join(missing_required)}")
    print(f"Evidence smoke summary written: {output / 'smoke_summary.json'}")
    print(f"Evidence smoke report written: {output / 'smoke_report.md'}")
    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a fast evidence-pipeline smoke workflow.")
    parser.add_argument("--root-dir", type=Path, default=Path("."))
    parser.add_argument("--output-dir", type=Path, default=Path("results/smoke"))
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        run_evidence_smoke(args.root_dir, args.output_dir)
        return 0
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
