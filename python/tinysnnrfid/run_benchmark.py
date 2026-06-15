from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Any

import numpy as np

from .classifiers import FSMClassifier, LUTLikeClassifier, ThresholdClassifier, TinySNNClassifier
from .config import load_config
from .dataset import load_generated_dataset
from .metrics import binary_metrics
from .report import write_reports


def build_classifiers(config: dict[str, Any]) -> dict[str, Any]:
    """Construct enabled classifiers from validated configuration."""
    dataset = config["dataset"]
    settings = config["classifiers"]
    pattern = tuple(dataset["valid_pattern"])
    available = {
        "threshold": ThresholdClassifier(**settings.get("threshold", {})),
        "fsm": FSMClassifier(pattern=pattern, **settings.get("fsm", {})),
        "lut_like": LUTLikeClassifier(pattern=pattern, **settings.get("lut_like", {})),
        "tiny_snn": TinySNNClassifier(pattern=pattern, **settings.get("tiny_snn", {})),
    }
    return {name: available[name] for name in settings["enabled"]}


def run_benchmark(config: dict[str, Any], data_dir: Path, results_dir: Path) -> dict[str, Any]:
    """Evaluate all configured classifiers on one generated dataset and write reports."""
    inputs, labels, metadata, scenario_tags = load_generated_dataset(data_dir)
    expected = config["dataset"]
    expected_shape = (expected["num_samples"], expected["sequence_length"], expected["input_width"])
    if inputs.shape != expected_shape:
        raise ValueError(f"Dataset shape mismatch for {data_dir}: expected {expected_shape}, got {inputs.shape}")
    classifier_results: dict[str, Any] = {}
    for name, classifier in build_classifiers(config).items():
        predictions = classifier.predict(inputs)
        if predictions.shape != labels.shape:
            raise ValueError(f"Classifier {name} returned shape {predictions.shape}; expected {labels.shape}")
        per_scenario: dict[str, Any] = {}
        tags = np.asarray(scenario_tags)
        for scenario in sorted(set(scenario_tags)):
            mask = tags == scenario
            per_scenario[scenario] = {
                "count": int(mask.sum()),
                **binary_metrics(labels[mask], predictions[mask]),
            }
        classifier_results[name] = {
            **binary_metrics(labels, predictions),
            "activity_proxy": classifier.activity_proxy(inputs),
            "per_scenario": per_scenario,
        }
    results = {
        "config": config,
        "seed": expected["random_seed"],
        "dataset": {
            "num_samples": int(inputs.shape[0]),
            "sequence_length": int(inputs.shape[1]),
            "input_width": int(inputs.shape[2]),
            "input_shape": list(inputs.shape),
            "label_counts": metadata["label_counts"],
            "scenario_counts": metadata["scenario_counts"],
        },
        "classifiers": classifier_results,
    }
    write_reports(results_dir, results)
    return results


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the Tiny SNN RFID classifier benchmark.")
    parser.add_argument("--config", type=Path, default=Path("configs/default.json"))
    parser.add_argument("--data-dir", type=Path)
    parser.add_argument("--results-dir", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        config = load_config(args.config)
        print(f"Dataset configuration loaded: {args.config}")
        data_dir = args.data_dir or Path(config["paths"]["data_dir"])
        results_dir = args.results_dir or Path(config["paths"]["results_dir"])
        run_benchmark(config, data_dir, results_dir)
        print("Classifiers evaluated.")
        print(f"Reports written: {results_dir / 'benchmark_results.json'}, {results_dir / 'benchmark_report.md'}")
        return 0
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
