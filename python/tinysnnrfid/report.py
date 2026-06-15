from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def write_reports(results_dir: str | Path, results: dict[str, Any]) -> tuple[Path, Path]:
    """Write machine-readable JSON and a concise human-readable Markdown report."""
    directory = Path(results_dir)
    directory.mkdir(parents=True, exist_ok=True)
    json_path = directory / "benchmark_results.json"
    markdown_path = directory / "benchmark_report.md"
    json_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    markdown_path.write_text(render_markdown_report(results), encoding="utf-8")
    return json_path, markdown_path


def render_markdown_report(results: dict[str, Any]) -> str:
    """Render benchmark results as Markdown."""
    dataset = results["dataset"]
    config = results["config"]["dataset"]
    classifiers = results["classifiers"]
    lines = [
        "# Tiny SNN RFID Benchmark Report",
        "",
        "## Configuration Summary",
        "",
        f"- Seed: `{config['random_seed']}`",
        f"- Samples: `{dataset['num_samples']}`",
        f"- Sequence shape: `{dataset['sequence_length']} x {dataset['input_width']}`",
        f"- Valid pattern: `{config['valid_pattern']}`",
        f"- Noise / jitter / dropout: `{config['noise_probability']}` / `{config['jitter_probability']}` / `{config['dropout_probability']}`",
        "",
        "## Dataset Summary",
        "",
        f"- Labels: `{dataset['label_counts']}`",
        f"- Input shape: `{dataset['input_shape']}`",
        "",
        "## Classifier Metrics",
        "",
        "| Classifier | Accuracy | Precision | Recall | F1 | TP | TN | FP | FN |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for name, values in classifiers.items():
        lines.append(
            f"| {name} | {values['accuracy']:.4f} | {values['precision']:.4f} | "
            f"{values['recall']:.4f} | {values['f1']:.4f} | {values['tp']} | "
            f"{values['tn']} | {values['fp']} | {values['fn']} |"
        )
    lines.extend(
        [
            "",
            "## Activity Proxies",
            "",
            "> These values are software-estimated operation counts, not hardware power or energy measurements.",
            "",
            "| Classifier | Total Operations | Mean / Sample | Max / Sample |",
            "|---|---:|---:|---:|",
        ]
    )
    for name, values in classifiers.items():
        proxy = values["activity_proxy"]
        lines.append(
            f"| {name} | {proxy['software_proxy_total_operations']} | "
            f"{proxy['software_proxy_mean_operations']:.2f} | {proxy['software_proxy_max_operations']} |"
        )
    best_name = max(classifiers, key=lambda name: (classifiers[name]["f1"], classifiers[name]["accuracy"]))
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            f"`{best_name}` has the strongest F1 score in this run. Activity values only compare software work; "
            "RTL simulation and synthesis are required before drawing hardware power or area conclusions.",
            "",
        ]
    )
    return "\n".join(lines)
