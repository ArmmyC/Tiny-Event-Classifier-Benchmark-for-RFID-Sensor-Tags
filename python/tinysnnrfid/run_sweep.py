from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime, timezone
import json
from itertools import product
from pathlib import Path
import sys
from typing import Any

from .config import load_config, validate_config
from .dataset import DatasetConfig, save_dataset
from .run_benchmark import run_benchmark


SUPPORTED_SWEEP_PATHS = {
    "dataset.noise_probability",
    "dataset.jitter_probability",
    "dataset.dropout_probability",
    "scenario.dense_noise_spike_threshold",
    "classifiers.tiny_snn_v2.hidden_threshold",
    "classifiers.tiny_snn_v2.output_threshold",
    "classifiers.tiny_snn_v2.leak",
}

PROBABILITY_PATHS = {
    "dataset.noise_probability",
    "dataset.jitter_probability",
    "dataset.dropout_probability",
}


def load_sweep_config(path: str | Path) -> dict[str, Any]:
    """Load and validate a sweep JSON config."""
    config_path = Path(path)
    if not config_path.is_file():
        raise ValueError(f"Sweep config does not exist: {config_path}")
    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        raise ValueError(f"Could not read sweep config {config_path}: {exc}") from exc
    validate_sweep_config(config)
    return config


def validate_sweep_config(config: dict[str, Any]) -> None:
    """Validate sweep config structure and supported parameter paths."""
    for field in ("base_config", "output_dir", "dataset_output_root"):
        if not isinstance(config.get(field), str) or not config[field].strip():
            raise ValueError(f"{field} must be a non-empty string")
    if not Path(config["base_config"]).is_file():
        raise ValueError(f"base_config does not exist: {config['base_config']}")
    name = config.get("name", "sweep")
    if not isinstance(name, str) or not name.strip():
        raise ValueError("name must be a non-empty string")
    seeds = config.get("seeds")
    if not isinstance(seeds, list) or not seeds or any(not isinstance(seed, int) for seed in seeds):
        raise ValueError("seeds must be a non-empty list of integers")
    parameters = sweep_parameters(config)
    if not isinstance(parameters, dict) or not parameters:
        raise ValueError("parameters must be a non-empty object")
    for path, values in parameters.items():
        if path not in SUPPORTED_SWEEP_PATHS:
            raise ValueError(f"Unsupported sweep parameter path: {path}")
        if not isinstance(values, list) or not values:
            raise ValueError(f"Sweep parameter {path} must be a non-empty list")
        for value in values:
            _validate_sweep_value(path, value)
    overrides = config.get("overrides", {})
    if not isinstance(overrides, dict):
        raise ValueError("overrides must be an object when provided")
    comparison = config.get("comparison", {})
    if comparison:
        if not isinstance(comparison, dict):
            raise ValueError("comparison must be an object")
        for field in ("reference_classifier", "candidate_classifier"):
            if not isinstance(comparison.get(field), str) or not comparison[field].strip():
                raise ValueError(f"comparison.{field} must be a non-empty string")


def sweep_parameters(config: dict[str, Any]) -> dict[str, list[Any]]:
    """Return configured sweep parameters, accepting either 'parameters' or 'sweep'."""
    return config.get("parameters", config.get("sweep", {}))


def _validate_sweep_value(path: str, value: Any) -> None:
    if path in PROBABILITY_PATHS:
        if not isinstance(value, (int, float)) or isinstance(value, bool) or not 0.0 <= value <= 1.0:
            raise ValueError(f"{path} values must be probabilities in [0.0, 1.0]")
    elif path == "scenario.dense_noise_spike_threshold":
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise ValueError(f"{path} values must be non-negative integers")
    elif path in {"classifiers.tiny_snn_v2.hidden_threshold", "classifiers.tiny_snn_v2.output_threshold"}:
        if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
            raise ValueError(f"{path} values must be positive integers")
    elif path == "classifiers.tiny_snn_v2.leak":
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise ValueError(f"{path} values must be non-negative integers")


def set_dotted_path(config: dict[str, Any], path: str, value: Any) -> None:
    """Set an existing nested config field using a restricted dotted path."""
    parts = path.split(".")
    if not parts or any(not part for part in parts):
        raise ValueError(f"Invalid dotted path: {path}")
    current: Any = config
    for part in parts[:-1]:
        if not isinstance(current, dict) or part not in current:
            raise ValueError(f"Unknown config path: {path}")
        current = current[part]
    final = parts[-1]
    if not isinstance(current, dict) or final not in current:
        raise ValueError(f"Unknown config path: {path}")
    current[final] = value


def expand_sweep_grid(config: dict[str, Any]) -> list[dict[str, Any]]:
    """Expand sweep parameters and seeds into deterministic run points."""
    parameters = sweep_parameters(config)
    keys = list(parameters)
    points: list[dict[str, Any]] = []
    for seed in config["seeds"]:
        for index_values in product(*(parameters[key] for key in keys)):
            values = dict(zip(keys, index_values))
            points.append({"seed": seed, "parameters": values})
    if not points:
        raise ValueError("Sweep expands to zero runs")
    for index, point in enumerate(points):
        point["run_id"] = f"run_{index:04d}"
    return points


def apply_sweep_config(base_config: dict[str, Any], point: dict[str, Any], overrides: dict[str, Any]) -> dict[str, Any]:
    """Return a validated benchmark config for one sweep point."""
    config = deepcopy(base_config)
    for path, value in overrides.items():
        set_dotted_path(config, path, value)
    for path, value in point["parameters"].items():
        set_dotted_path(config, path, value)
    set_dotted_path(config, "dataset.random_seed", point["seed"])
    validate_config(config)
    return config


def run_sweep(
    sweep_config: dict[str, Any],
    output_dir: str | Path | None = None,
    max_runs: int | None = None,
) -> dict[str, Any]:
    """Run all sweep points and write JSON plus Markdown summaries."""
    base_config = load_config(sweep_config["base_config"])
    points = expand_sweep_grid(sweep_config)
    if max_runs is not None:
        if max_runs <= 0:
            raise ValueError("max_runs must be greater than 0")
        points = points[:max_runs]

    output_root = Path(output_dir or sweep_config["output_dir"])
    dataset_root = Path(sweep_config["dataset_output_root"])
    runs_root = output_root / "runs"
    output_root.mkdir(parents=True, exist_ok=True)
    dataset_root.mkdir(parents=True, exist_ok=True)
    runs_root.mkdir(parents=True, exist_ok=True)

    overrides = sweep_config.get("overrides", {})
    run_results: list[dict[str, Any]] = []
    print(f"Running {len(points)} sweep point(s)...")
    for point in points:
        run_config = apply_sweep_config(base_config, point, overrides)
        data_dir = dataset_root / point["run_id"]
        result_dir = runs_root / point["run_id"]
        run_config["paths"]["data_dir"] = str(data_dir)
        run_config["paths"]["results_dir"] = str(result_dir)
        print(f"[{len(run_results) + 1}/{len(points)}] {_format_point(point)}")
        save_dataset(
            data_dir,
            DatasetConfig.from_mapping(run_config["dataset"], run_config["scenario"]),
            run_config,
        )
        result = run_benchmark(run_config, data_dir, result_dir)
        run_results.append(
            {
                "run_id": point["run_id"],
                "seed": point["seed"],
                "parameters": point["parameters"],
                "dataset": result["dataset"],
                "classifiers": result["classifiers"],
            }
        )

    aggregate = aggregate_results(run_results)
    comparison = compare_candidate_to_reference(
        run_results,
        sweep_config.get("comparison", {}).get("candidate_classifier", "tiny_snn_v2"),
        sweep_config.get("comparison", {}).get("reference_classifier", "fsm"),
    )
    results = {
        "sweep": {
            "name": sweep_config.get("name", "sweep"),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "run_count": len(run_results),
            "parameters": sweep_parameters(sweep_config),
            "seeds": sweep_config["seeds"],
        },
        "sweep_config": sweep_config,
        "runs": run_results,
        "aggregate": aggregate,
        "comparison": comparison,
    }
    write_sweep_outputs(output_root, results)
    return results


def _format_point(point: dict[str, Any]) -> str:
    values = [f"{key}={value}" for key, value in point["parameters"].items()]
    values.append(f"seed={point['seed']}")
    return ", ".join(values)


def aggregate_results(runs: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate overall and per-scenario classifier metrics across runs."""
    by_classifier: dict[str, list[dict[str, Any]]] = {}
    scenario_scores: dict[str, dict[str, dict[str, list[float]]]] = {}
    for run in runs:
        for name, metrics in run["classifiers"].items():
            by_classifier.setdefault(name, []).append(metrics)
            for scenario, scenario_metrics in metrics["per_scenario"].items():
                scenario_scores.setdefault(scenario, {}).setdefault(name, {"f1": [], "accuracy": []})
                scenario_scores[scenario][name]["f1"].append(float(scenario_metrics["f1"]))
                scenario_scores[scenario][name]["accuracy"].append(float(scenario_metrics["accuracy"]))

    classifier_summary: dict[str, Any] = {}
    for name, metrics_list in by_classifier.items():
        f1_values = [float(metrics["f1"]) for metrics in metrics_list]
        accuracy_values = [float(metrics["accuracy"]) for metrics in metrics_list]
        activity_values = [
            float(metrics["activity_proxy"].get("software_proxy_mean_operations", 0.0))
            for metrics in metrics_list
        ]
        classifier_summary[name] = {
            "runs": len(metrics_list),
            "mean_f1": _mean(f1_values),
            "best_f1": max(f1_values),
            "worst_f1": min(f1_values),
            "mean_accuracy": _mean(accuracy_values),
            "mean_activity_proxy": _mean(activity_values),
        }

    best_by_scenario: dict[str, Any] = {}
    for scenario, classifier_values in scenario_scores.items():
        scenario_means = {
            name: {"mean_f1": _mean(values["f1"]), "mean_accuracy": _mean(values["accuracy"])}
            for name, values in classifier_values.items()
        }
        best_name = max(
            scenario_means,
            key=lambda name: (
                scenario_means[name]["mean_f1"],
                scenario_means[name]["mean_accuracy"],
                name,
            ),
        )
        best_by_scenario[scenario] = {
            "classifier": best_name,
            "mean_f1": scenario_means[best_name]["mean_f1"],
            "mean_accuracy": scenario_means[best_name]["mean_accuracy"],
        }

    return {
        "by_classifier": classifier_summary,
        "best_by_scenario": best_by_scenario,
    }


def compare_candidate_to_reference(
    runs: list[dict[str, Any]], candidate: str, reference: str
) -> dict[str, Any]:
    """Compare a candidate classifier against a reference classifier by run."""
    wins: list[dict[str, Any]] = []
    losses: list[dict[str, Any]] = []
    rows: list[dict[str, Any]] = []
    for run in runs:
        classifiers = run["classifiers"]
        if candidate not in classifiers or reference not in classifiers:
            continue
        candidate_metrics = classifiers[candidate]
        reference_metrics = classifiers[reference]
        delta = float(candidate_metrics["f1"]) - float(reference_metrics["f1"])
        row = {
            "run_id": run["run_id"],
            "seed": run["seed"],
            "parameters": run["parameters"],
            "candidate_f1": float(candidate_metrics["f1"]),
            "reference_f1": float(reference_metrics["f1"]),
            "f1_delta": delta,
            "candidate_activity": float(
                candidate_metrics["activity_proxy"].get("software_proxy_mean_operations", 0.0)
            ),
            "reference_activity": float(
                reference_metrics["activity_proxy"].get("software_proxy_mean_operations", 0.0)
            ),
        }
        rows.append(row)
        if delta > 0:
            wins.append(row)
        elif delta < 0:
            losses.append(row)
    return {
        "candidate_classifier": candidate,
        "reference_classifier": reference,
        "candidate_f1_wins": len(wins),
        "candidate_f1_losses": len(losses),
        "rows": rows,
        "wins": sorted(wins, key=lambda row: row["f1_delta"], reverse=True),
        "losses": sorted(losses, key=lambda row: row["f1_delta"]),
    }


def write_sweep_outputs(output_dir: Path, results: dict[str, Any]) -> tuple[Path, Path]:
    """Write sweep JSON and Markdown report."""
    json_path = output_dir / "sweep_results.json"
    markdown_path = output_dir / "sweep_report.md"
    json_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    markdown_path.write_text(render_sweep_report(results), encoding="utf-8")
    print(f"Sweep results written: {json_path}")
    print(f"Sweep report written: {markdown_path}")
    return json_path, markdown_path


def render_sweep_report(results: dict[str, Any]) -> str:
    """Render a human-readable Markdown sweep report."""
    sweep = results["sweep"]
    aggregate = results["aggregate"]
    comparison = results["comparison"]
    lines = [
        f"# Experiment Sweep Report: {sweep['name']}",
        "",
        "## Sweep Setup",
        "",
        f"- Runs: `{sweep['run_count']}`",
        f"- Seeds: `{sweep['seeds']}`",
        f"- Parameters: `{sweep['parameters']}`",
        "",
        "## Best Classifier By Sweep Point",
        "",
        "| Run | Seed | Best Classifier | F1 | Parameters |",
        "|---|---:|---|---:|---|",
    ]
    for run in results["runs"]:
        best_name = max(
            run["classifiers"],
            key=lambda name: (run["classifiers"][name]["f1"], run["classifiers"][name]["accuracy"], name),
        )
        lines.append(
            f"| {run['run_id']} | {run['seed']} | {best_name} | "
            f"{run['classifiers'][best_name]['f1']:.4f} | `{run['parameters']}` |"
        )

    lines.extend(
        [
            "",
            "## Aggregate Classifier Summary",
            "",
            "| Classifier | Runs | Mean F1 | Best F1 | Worst F1 | Mean Accuracy | Mean Activity Proxy |",
            "|---|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for name, values in aggregate["by_classifier"].items():
        lines.append(
            f"| {name} | {values['runs']} | {values['mean_f1']:.4f} | {values['best_f1']:.4f} | "
            f"{values['worst_f1']:.4f} | {values['mean_accuracy']:.4f} | {values['mean_activity_proxy']:.2f} |"
        )

    lines.extend(
        [
            "",
            "## Best Classifier By Scenario",
            "",
            "| Scenario | Best Classifier | Mean F1 | Mean Accuracy |",
            "|---|---|---:|---:|",
        ]
    )
    for scenario, values in aggregate["best_by_scenario"].items():
        lines.append(
            f"| {scenario} | {values['classifier']} | {values['mean_f1']:.4f} | "
            f"{values['mean_accuracy']:.4f} |"
        )

    candidate = comparison["candidate_classifier"]
    reference = comparison["reference_classifier"]
    lines.extend(
        [
            "",
            f"## {candidate} vs {reference}",
            "",
            f"- `{candidate}` F1 wins: `{comparison['candidate_f1_wins']}`",
            f"- `{candidate}` F1 losses: `{comparison['candidate_f1_losses']}`",
            "",
            "| Run | Seed | Candidate F1 | Reference F1 | Delta | Candidate Activity | Reference Activity |",
            "|---|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in sorted(comparison["rows"], key=lambda item: item["f1_delta"], reverse=True)[:10]:
        lines.append(
            f"| {row['run_id']} | {row['seed']} | {row['candidate_f1']:.4f} | "
            f"{row['reference_f1']:.4f} | {row['f1_delta']:.4f} | "
            f"{row['candidate_activity']:.2f} | {row['reference_activity']:.2f} |"
        )

    lines.extend(["", f"## Cases Where {candidate} Wins", ""])
    if comparison["wins"]:
        for row in comparison["wins"][:10]:
            lines.append(f"- `{row['run_id']}` delta `{row['f1_delta']:.4f}` with `{row['parameters']}`")
    else:
        lines.append(f"- No F1 wins for `{candidate}` in this sweep.")

    lines.extend(["", f"## Cases Where {candidate} Loses", ""])
    if comparison["losses"]:
        for row in comparison["losses"][:10]:
            lines.append(f"- `{row['run_id']}` delta `{row['f1_delta']:.4f}` with `{row['parameters']}`")
    else:
        lines.append(f"- No F1 losses for `{candidate}` in this sweep.")

    lines.extend(
        [
            "",
            "## Notes and Limitations",
            "",
            "Activity proxy metrics are software operation proxies, not hardware power or energy. "
            "RTL implementation, simulation, and synthesis are required before making hardware conclusions.",
            "",
        ]
    )
    return "\n".join(lines)


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run deterministic benchmark parameter sweeps.")
    parser.add_argument("--config", type=Path, default=Path("configs/sweep_default.json"))
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--max-runs", type=int)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        config = load_sweep_config(args.config)
        print(f"Sweep configuration loaded: {args.config}")
        run_sweep(config, output_dir=args.output_dir, max_runs=args.max_runs)
        return 0
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
