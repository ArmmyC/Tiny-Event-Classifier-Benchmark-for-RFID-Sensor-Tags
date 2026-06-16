from __future__ import annotations

import argparse
import csv
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
from .run_sweep import compare_candidate_to_reference, set_dotted_path


WEIGHT_VARIANTS: dict[str, dict[str, Any]] = {
    "current_default": {
        "description": "Existing small integer tiny_snn_v2 weights.",
        "hidden_neurons": 6,
        "input_weights": [
            [4, 0, 0, -1, 3, 0],
            [0, 3, 0, -1, 3, 3],
            [0, 0, 4, -1, 0, 3],
            [-1, -1, -1, 7, -2, -2],
        ],
        "output_weights": [-2, 0, 1, -3, 2, 2],
    },
    "ternary_event_order": {
        "description": "Ternary-only event-order detectors with a noise guard.",
        "hidden_neurons": 6,
        "input_weights": [
            [1, 0, 0, -1, 1, 0],
            [0, 1, 0, -1, 1, 1],
            [0, 0, 1, -1, 0, 1],
            [-1, -1, -1, 1, 0, 0],
        ],
        "output_weights": [1, 1, 1, -1, 1, 1],
    },
    "ternary_noise_guard": {
        "description": "Ternary-only variant with stronger inhibition for dense input activity.",
        "hidden_neurons": 6,
        "input_weights": [
            [1, 0, 0, -1, 1, -1],
            [0, 1, 0, -1, 1, 0],
            [0, 0, 1, -1, -1, 1],
            [-1, -1, -1, 1, -1, -1],
        ],
        "output_weights": [1, 1, 1, -1, 0, 1],
    },
    "low_activity_sparse": {
        "description": "Sparse ternary-weight variant intended to reduce software proxy activity.",
        "hidden_neurons": 4,
        "input_weights": [
            [1, 0, 0, -1],
            [0, 1, 0, -1],
            [0, 0, 1, -1],
            [0, 0, 0, 1],
        ],
        "output_weights": [1, 1, 1, -1],
    },
    "balanced_small_int": {
        "description": "Small signed integer weights limited to [-2, 2].",
        "hidden_neurons": 6,
        "input_weights": [
            [2, 0, 0, -1, 1, 0],
            [0, 2, 0, -1, 1, 1],
            [0, 0, 2, -1, 0, 1],
            [-1, -1, -1, 2, -1, -1],
        ],
        "output_weights": [1, 1, 2, -2, 1, 1],
    },
    "temporal_gap_guard": {
        "description": "Ternary-only temporal-hard guard for long gaps and partial-order ambiguity.",
        "hidden_neurons": 6,
        "input_weights": [
            [1, 0, 0, -1, 1, 0],
            [0, 1, 0, -1, 1, -1],
            [0, 0, 1, -1, 0, 1],
            [-1, 0, -1, 1, -1, -1],
        ],
        "output_weights": [1, 1, 1, -1, 1, 0],
    },
    "reversal_inhibitory_guard": {
        "description": "Small signed integer temporal-hard guard limited to [-2, 2] for reversed and noisy motifs.",
        "hidden_neurons": 6,
        "input_weights": [
            [2, -1, 0, -1, 1, 0],
            [-1, 2, -1, -1, 1, -1],
            [0, -1, 2, -1, -1, 1],
            [-2, -1, -2, 2, -2, -1],
        ],
        "output_weights": [2, 1, 2, -2, 1, -1],
    },
    "current_default_gap_tuned": {
        "description": "Current-default-derived weights with slightly stronger event-order support for long temporal gaps.",
        "hidden_neurons": 6,
        "input_weights": [
            [4, 0, 0, -1, 4, 0],
            [0, 3, 0, -1, 4, 2],
            [0, 0, 4, -1, 0, 4],
            [-1, -1, -1, 7, -2, -2],
        ],
        "output_weights": [-2, 1, 1, -3, 2, 2],
    },
    "current_default_output_rebalanced": {
        "description": "Current-default-derived weights with reduced inhibitory output magnitude and rebalanced positive drive.",
        "hidden_neurons": 6,
        "input_weights": [
            [4, 0, 0, -1, 3, 0],
            [0, 3, 0, -1, 3, 3],
            [0, 0, 4, -1, 0, 3],
            [-1, -1, -1, 7, -2, -2],
        ],
        "output_weights": [-1, 1, 1, -2, 2, 1],
    },
    "current_default_noise_inhibited": {
        "description": "Current-default-derived weights with stronger channel-3 inhibition for burst and reversed negatives.",
        "hidden_neurons": 6,
        "input_weights": [
            [4, 0, 0, -2, 3, 0],
            [0, 3, 0, -2, 3, 3],
            [0, 0, 4, -2, 0, 3],
            [-2, -2, -2, 8, -3, -3],
        ],
        "output_weights": [-2, 0, 1, -4, 2, 2],
    },
    "current_default_sparse_activity": {
        "description": "Current-default-derived sparse-output variant intended to reduce software activity proxy pressure.",
        "hidden_neurons": 6,
        "input_weights": [
            [4, 0, 0, -1, 2, 0],
            [0, 3, 0, -1, 2, 2],
            [0, 0, 4, -1, 0, 2],
            [-1, -1, -1, 6, -1, -1],
        ],
        "output_weights": [-1, 0, 1, -2, 1, 1],
    },
}

DATASET_PARAMETER_PATHS = {
    "dataset.noise_probability",
    "dataset.jitter_probability",
    "dataset.dropout_probability",
}

SNN_PARAMETER_PATHS = {
    "classifiers.tiny_snn_v2.hidden_threshold",
    "classifiers.tiny_snn_v2.output_threshold",
    "classifiers.tiny_snn_v2.leak",
    "classifiers.tiny_snn_v2.reset_on_spike",
}

RECOMMENDATIONS = {
    "continue_snn_optimization",
    "add_harder_temporal_scenarios",
    "prioritize_fsm_or_lut_rtl_baseline",
}

SELECTION_STRATEGIES = {"full_grid", "prefix", "balanced_round_robin"}


def load_search_config(path: str | Path) -> dict[str, Any]:
    """Load and validate an SNN search JSON config."""
    config_path = Path(path)
    if not config_path.is_file():
        raise ValueError(f"SNN search config does not exist: {config_path}")
    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        raise ValueError(f"Could not read SNN search config {config_path}: {exc}") from exc
    validate_search_config(config)
    return config


def validate_search_config(config: dict[str, Any]) -> None:
    """Validate search config shape and deterministic parameter domains."""
    for field in ("base_config", "output_dir", "dataset_output_root"):
        if not isinstance(config.get(field), str) or not config[field].strip():
            raise ValueError(f"{field} must be a non-empty string")
    if not Path(config["base_config"]).is_file():
        raise ValueError(f"base_config does not exist: {config['base_config']}")
    name = config.get("name", "snn_search")
    if not isinstance(name, str) or not name.strip():
        raise ValueError("name must be a non-empty string")
    seeds = config.get("seeds")
    if not isinstance(seeds, list) or not seeds or any(not isinstance(seed, int) for seed in seeds):
        raise ValueError("seeds must be a non-empty list of integers")
    _validate_dotted_mapping(config.get("dataset_overrides", {}), allow_empty=True)
    dataset_parameters = config.get("dataset_parameters", {})
    if not isinstance(dataset_parameters, dict):
        raise ValueError("dataset_parameters must be an object")
    for path, values in dataset_parameters.items():
        if path not in DATASET_PARAMETER_PATHS:
            raise ValueError(f"Unsupported dataset parameter path: {path}")
        _validate_non_empty_values(path, values)
        for value in values:
            _validate_probability(path, value)
    snn_parameters = config.get("snn_parameters")
    if not isinstance(snn_parameters, dict) or not snn_parameters:
        raise ValueError("snn_parameters must be a non-empty object")
    for path, values in snn_parameters.items():
        if path not in SNN_PARAMETER_PATHS:
            raise ValueError(f"Unsupported SNN parameter path: {path}")
        _validate_non_empty_values(path, values)
        for value in values:
            _validate_snn_parameter_value(path, value)
    variants = config.get("weight_variants")
    if not isinstance(variants, list) or not variants:
        raise ValueError("weight_variants must be a non-empty list")
    unknown = [variant for variant in variants if variant not in WEIGHT_VARIANTS]
    if unknown:
        raise ValueError(f"Unknown weight variant(s): {', '.join(unknown)}")
    comparison = config.get("comparison", {})
    if not isinstance(comparison, dict):
        raise ValueError("comparison must be an object")
    for field in ("reference_classifier", "candidate_classifier"):
        if not isinstance(comparison.get(field), str) or not comparison[field].strip():
            raise ValueError(f"comparison.{field} must be a non-empty string")
    tolerance = comparison.get("f1_tolerance", 0.0)
    if not isinstance(tolerance, (int, float)) or isinstance(tolerance, bool) or tolerance < 0.0:
        raise ValueError("comparison.f1_tolerance must be a non-negative number")
    limits = config.get("limits", {})
    if limits:
        if not isinstance(limits, dict):
            raise ValueError("limits must be an object")
        max_candidates = limits.get("max_candidates")
        if max_candidates is not None and (
            not isinstance(max_candidates, int) or isinstance(max_candidates, bool) or max_candidates <= 0
        ):
            raise ValueError("limits.max_candidates must be a positive integer")
    selection = config.get("selection", {"strategy": "balanced_round_robin"})
    if not isinstance(selection, dict):
        raise ValueError("selection must be an object")
    strategy = selection.get("strategy", "balanced_round_robin")
    if strategy not in SELECTION_STRATEGIES:
        raise ValueError(f"Unsupported selection strategy: {strategy}")
    _validate_weight_variants()


def _validate_dotted_mapping(values: Any, allow_empty: bool = False) -> None:
    if allow_empty and values == {}:
        return
    if not isinstance(values, dict):
        raise ValueError("dotted overrides must be an object")
    for path in values:
        if not isinstance(path, str) or "." not in path:
            raise ValueError(f"Invalid dotted path: {path}")


def _validate_non_empty_values(path: str, values: Any) -> None:
    if not isinstance(values, list) or not values:
        raise ValueError(f"{path} must be a non-empty list")


def _validate_probability(path: str, value: Any) -> None:
    if not isinstance(value, (int, float)) or isinstance(value, bool) or not 0.0 <= value <= 1.0:
        raise ValueError(f"{path} values must be probabilities in [0.0, 1.0]")


def _validate_snn_parameter_value(path: str, value: Any) -> None:
    if path in {"classifiers.tiny_snn_v2.hidden_threshold", "classifiers.tiny_snn_v2.output_threshold"}:
        if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
            raise ValueError(f"{path} values must be positive integers")
    elif path == "classifiers.tiny_snn_v2.leak":
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise ValueError(f"{path} values must be non-negative integers")
    elif path == "classifiers.tiny_snn_v2.reset_on_spike":
        if not isinstance(value, bool):
            raise ValueError(f"{path} values must be booleans")


def _validate_weight_variants() -> None:
    for name, variant in WEIGHT_VARIANTS.items():
        hidden_neurons = variant.get("hidden_neurons")
        input_weights = variant.get("input_weights")
        output_weights = variant.get("output_weights")
        if not isinstance(hidden_neurons, int) or hidden_neurons <= 0:
            raise ValueError(f"Weight variant {name} hidden_neurons must be positive")
        if (
            not isinstance(input_weights, list)
            or not input_weights
            or any(not isinstance(row, list) or len(row) != hidden_neurons for row in input_weights)
        ):
            raise ValueError(f"Weight variant {name} input_weights shape is invalid")
        if not isinstance(output_weights, list) or len(output_weights) != hidden_neurons:
            raise ValueError(f"Weight variant {name} output_weights length is invalid")
        weights = [weight for row in input_weights for weight in row] + list(output_weights)
        if any(not isinstance(weight, int) or isinstance(weight, bool) for weight in weights):
            raise ValueError(f"Weight variant {name} must contain only integer weights")


def expand_full_candidate_grid(config: dict[str, Any]) -> list[dict[str, Any]]:
    """Expand every deterministic search dimension without applying selection limits."""
    dataset_parameters = config.get("dataset_parameters", {})
    dataset_keys = list(dataset_parameters)
    dataset_points = [
        dict(zip(dataset_keys, values))
        for values in product(*(dataset_parameters[key] for key in dataset_keys))
    ] or [{}]
    snn_parameters = config["snn_parameters"]
    snn_keys = list(snn_parameters)
    snn_points = [
        dict(zip(snn_keys, values))
        for values in product(*(snn_parameters[key] for key in snn_keys))
    ]
    candidates: list[dict[str, Any]] = []
    for seed in config["seeds"]:
        for dataset_point in dataset_points:
            for snn_point in snn_points:
                for variant in config["weight_variants"]:
                    parameters = {**dataset_point, **snn_point}
                    candidates.append(
                        {
                            "seed": seed,
                            "weight_variant": variant,
                            "parameters": parameters,
                            "dataset_parameters": dataset_point,
                            "snn_parameters": snn_point,
                        }
                    )
    return candidates


def expand_candidate_grid(config: dict[str, Any]) -> list[dict[str, Any]]:
    """Expand and select deterministic candidate points, preserving legacy call sites."""
    candidates, _metadata = select_candidates(expand_full_candidate_grid(config), config)
    return candidates


def select_candidates(candidates: list[dict[str, Any]], config: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Select candidates according to configured deterministic strategy and report coverage."""
    strategy = config.get("selection", {}).get("strategy", "balanced_round_robin")
    max_candidates = config.get("limits", {}).get("max_candidates")
    if strategy == "full_grid" or max_candidates is None:
        selected = list(candidates)
    elif strategy == "prefix":
        selected = list(candidates[:max_candidates])
    elif strategy == "balanced_round_robin":
        selected = _select_balanced_round_robin(candidates, max_candidates)
    else:
        raise ValueError(f"Unsupported selection strategy: {strategy}")
    for index, candidate in enumerate(candidates):
        candidate.pop("candidate_id", None)
    for index, candidate in enumerate(selected):
        candidate["candidate_id"] = f"candidate_{index:04d}"
    metadata = build_selection_metadata(strategy, candidates, selected)
    return selected, metadata


def _select_balanced_round_robin(candidates: list[dict[str, Any]], max_candidates: int) -> list[dict[str, Any]]:
    groups: dict[tuple[Any, ...], list[dict[str, Any]]] = {}
    for candidate in candidates:
        groups.setdefault(_candidate_group_key(candidate), []).append(candidate)
    group_keys = sorted(groups)
    selected: list[dict[str, Any]] = []
    while len(selected) < max_candidates and group_keys:
        next_keys: list[tuple[Any, ...]] = []
        for key in group_keys:
            group = groups[key]
            if group and len(selected) < max_candidates:
                selected.append(group.pop(0))
            if group:
                next_keys.append(key)
        group_keys = next_keys
    return selected


def _candidate_group_key(candidate: dict[str, Any]) -> tuple[Any, ...]:
    dataset = candidate["dataset_parameters"]
    return (
        candidate["seed"],
        dataset.get("dataset.noise_probability", ""),
        dataset.get("dataset.jitter_probability", ""),
        dataset.get("dataset.dropout_probability", ""),
        candidate["weight_variant"],
    )


def _dataset_condition_key(candidate: dict[str, Any]) -> str:
    dataset = candidate["dataset_parameters"]
    return (
        f"noise={dataset.get('dataset.noise_probability', '')},"
        f"jitter={dataset.get('dataset.jitter_probability', '')},"
        f"dropout={dataset.get('dataset.dropout_probability', '')}"
    )


def build_selection_metadata(
    strategy: str,
    full_grid: list[dict[str, Any]],
    selected: list[dict[str, Any]],
) -> dict[str, Any]:
    """Summarize selected candidate coverage for machine and report output."""
    return {
        "strategy": strategy,
        "full_grid_candidate_count": len(full_grid),
        "evaluated_candidate_count": len(selected),
        "skipped_candidate_count": len(full_grid) - len(selected),
        "coverage": {
            "weight_variants": _count_by(selected, lambda candidate: candidate["weight_variant"]),
            "dataset_conditions": _count_by(selected, _dataset_condition_key),
            "seeds": _count_by(selected, lambda candidate: str(candidate["seed"])),
        },
    }


def _count_by(candidates: list[dict[str, Any]], key_fn: Any) -> dict[str, int]:
    counts: dict[str, int] = {}
    for candidate in candidates:
        key = key_fn(candidate)
        counts[str(key)] = counts.get(str(key), 0) + 1
    return dict(sorted(counts.items()))


def apply_candidate_config(
    base_config: dict[str, Any],
    search_config: dict[str, Any],
    candidate: dict[str, Any],
) -> dict[str, Any]:
    """Build a validated benchmark config for one SNN search candidate."""
    config = deepcopy(base_config)
    for path, value in search_config.get("dataset_overrides", {}).items():
        set_dotted_path(config, path, value)
    for path, value in candidate["parameters"].items():
        set_dotted_path(config, path, value)
    set_dotted_path(config, "dataset.random_seed", candidate["seed"])
    variant = WEIGHT_VARIANTS[candidate["weight_variant"]]
    set_dotted_path(config, "classifiers.tiny_snn_v2.hidden_neurons", variant["hidden_neurons"])
    set_dotted_path(config, "classifiers.tiny_snn_v2.input_weights", deepcopy(variant["input_weights"]))
    set_dotted_path(config, "classifiers.tiny_snn_v2.output_weights", deepcopy(variant["output_weights"]))
    validate_config(config)
    return config


def run_snn_search(
    search_config: dict[str, Any],
    output_dir: str | Path | None = None,
    max_candidates: int | None = None,
) -> dict[str, Any]:
    """Evaluate deterministic tiny_snn_v2 parameter and precision candidates."""
    base_config = load_config(search_config["base_config"])
    full_grid = expand_full_candidate_grid(search_config)
    candidates, selection_metadata = select_candidates(full_grid, search_config)
    if max_candidates is not None:
        if max_candidates <= 0:
            raise ValueError("max_candidates must be greater than 0")
        candidates = candidates[:max_candidates]
        for index, candidate in enumerate(candidates):
            candidate["candidate_id"] = f"candidate_{index:04d}"
        selection_metadata = build_selection_metadata(
            f"{selection_metadata['strategy']}_cli_limit",
            full_grid,
            candidates,
        )

    output_root = Path(output_dir or search_config["output_dir"])
    dataset_root = Path(search_config["dataset_output_root"])
    runs_root = output_root / "runs"
    output_root.mkdir(parents=True, exist_ok=True)
    dataset_root.mkdir(parents=True, exist_ok=True)
    runs_root.mkdir(parents=True, exist_ok=True)

    reference = search_config.get("comparison", {}).get("reference_classifier", "fsm")
    candidate_name = search_config.get("comparison", {}).get("candidate_classifier", "tiny_snn_v2")
    f1_tolerance = float(search_config.get("comparison", {}).get("f1_tolerance", 0.0))

    print(f"Running {len(candidates)} candidate configurations...")
    run_results: list[dict[str, Any]] = []
    for index, candidate in enumerate(candidates, start=1):
        run_config = apply_candidate_config(base_config, search_config, candidate)
        data_dir = dataset_root / candidate["candidate_id"]
        result_dir = runs_root / candidate["candidate_id"]
        run_config["paths"]["data_dir"] = str(data_dir)
        run_config["paths"]["results_dir"] = str(result_dir)
        print(f"[{index}/{len(candidates)}] {candidate['candidate_id']} {candidate['weight_variant']}")
        save_dataset(
            data_dir,
            DatasetConfig.from_mapping(run_config["dataset"], run_config["scenario"], run_config.get("scenario_suite")),
            run_config,
        )
        result = run_benchmark(run_config, data_dir, result_dir)
        comparison = compare_candidate_to_reference(
            [
                {
                    "run_id": candidate["candidate_id"],
                    "seed": candidate["seed"],
                    "parameters": candidate["parameters"],
                    "classifiers": result["classifiers"],
                }
            ],
            candidate_name,
            reference,
            f1_tolerance=f1_tolerance,
        )
        comparison_row = comparison["rows"][0]
        run_results.append(
            {
                "candidate_id": candidate["candidate_id"],
                "seed": candidate["seed"],
                "weight_variant": candidate["weight_variant"],
                "weight_variant_description": WEIGHT_VARIANTS[candidate["weight_variant"]]["description"],
                "parameters": candidate["parameters"],
                "dataset": result["dataset"],
                "classifiers": result["classifiers"],
                "comparison": comparison_row,
            }
        )

    aggregate = aggregate_search_results(run_results, candidate_name)
    decision = build_search_decision(run_results, aggregate, f1_tolerance)
    results = {
        "search": {
            "name": search_config.get("name", "snn_search"),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "candidate_count": len(run_results),
            "weight_variants": search_config["weight_variants"],
            "seeds": search_config["seeds"],
            "dataset_parameters": search_config.get("dataset_parameters", {}),
            "snn_parameters": search_config["snn_parameters"],
        },
        "search_config": search_config,
        "selection": selection_metadata,
        "weight_variants": WEIGHT_VARIANTS,
        "runs": sorted_search_runs(run_results),
        "aggregate": aggregate,
        "decision": decision,
    }
    write_search_outputs(output_root, results)
    return results


def aggregate_search_results(runs: list[dict[str, Any]], candidate_name: str) -> dict[str, Any]:
    """Aggregate SNN search runs by variant and scenario."""
    by_variant: dict[str, list[dict[str, Any]]] = {}
    scenario_candidates: dict[str, list[dict[str, Any]]] = {}
    for run in runs:
        by_variant.setdefault(run["weight_variant"], []).append(run)
        candidate_metrics = run["classifiers"][candidate_name]
        for scenario, scenario_metrics in candidate_metrics["per_scenario"].items():
            scenario_candidates.setdefault(scenario, []).append(
                {
                    "candidate_id": run["candidate_id"],
                    "weight_variant": run["weight_variant"],
                    "f1": float(scenario_metrics["f1"]),
                    "accuracy": float(scenario_metrics["accuracy"]),
                }
            )
    variant_summary: dict[str, Any] = {}
    for variant, variant_runs in by_variant.items():
        f1_values = [float(run["comparison"]["candidate_f1"]) for run in variant_runs]
        activity_values = [float(run["comparison"]["candidate_activity"]) for run in variant_runs]
        competitive_count = sum(1 for run in variant_runs if run["comparison"]["competitive"])
        variant_summary[variant] = {
            "runs": len(variant_runs),
            "mean_candidate_f1": _mean(f1_values),
            "best_candidate_f1": max(f1_values),
            "mean_candidate_activity": _mean(activity_values),
            "competitive_runs": competitive_count,
        }
    best_by_scenario: dict[str, Any] = {}
    for scenario, values in scenario_candidates.items():
        best = max(values, key=lambda item: (item["f1"], item["accuracy"], item["candidate_id"]))
        best_by_scenario[scenario] = best
    return {
        "by_weight_variant": variant_summary,
        "best_candidate_by_scenario": best_by_scenario,
    }


def build_search_decision(
    runs: list[dict[str, Any]],
    aggregate: dict[str, Any],
    f1_tolerance: float,
) -> dict[str, Any]:
    """Build a stable enum recommendation for the SNN search."""
    competitive = [run for run in runs if run["comparison"]["competitive"]]
    f1_wins = [run for run in competitive if run["comparison"]["competitive_reason"] == "f1_win"]
    activity_wins = [
        run
        for run in competitive
        if run["comparison"]["competitive_reason"] == "activity_win_within_f1_tolerance"
    ]
    best_run = sorted_search_runs(runs)[0] if runs else None
    if f1_wins:
        recommendation = "continue_snn_optimization"
        reason = "At least one tiny_snn_v2 candidate beats the FSM reference on F1."
    elif activity_wins:
        recommendation = "continue_snn_optimization"
        reason = "At least one tiny_snn_v2 candidate has lower software activity while staying within F1 tolerance."
    elif best_run and best_run["comparison"]["f1_delta"] >= -f1_tolerance:
        recommendation = "add_harder_temporal_scenarios"
        reason = "The best tiny_snn_v2 candidate is close to FSM F1 but lacks a software activity advantage."
    else:
        recommendation = "prioritize_fsm_or_lut_rtl_baseline"
        reason = "No searched tiny_snn_v2 candidate is F1-competitive or lower-activity within tolerance."
    return {
        "recommendation": recommendation,
        "reason": reason,
        "best_candidate_id": best_run["candidate_id"] if best_run else None,
        "best_weight_variant": best_run["weight_variant"] if best_run else None,
        "best_candidate_f1": best_run["comparison"]["candidate_f1"] if best_run else 0.0,
        "best_reference_f1": best_run["comparison"]["reference_f1"] if best_run else 0.0,
        "competitive_candidate_count": len(competitive),
        "f1_win_count": len(f1_wins),
        "activity_win_within_tolerance_count": len(activity_wins),
        "f1_tolerance": f1_tolerance,
        "activity_note": "Activity metrics are software operation proxies, not hardware power or energy.",
        "scenario_count": len(aggregate.get("best_candidate_by_scenario", {})),
    }


def sorted_search_runs(runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Rank candidates by F1, accuracy, lower activity, and competitive status."""
    reason_rank = {
        "f1_win": 2,
        "activity_win_within_f1_tolerance": 1,
        "not_competitive": 0,
        "missing_classifier": -1,
    }
    return sorted(
        runs,
        key=lambda run: (
            float(run["comparison"]["candidate_f1"] or 0.0),
            float(run["classifiers"]["tiny_snn_v2"]["accuracy"]),
            -float(run["comparison"]["candidate_activity"] or 0.0),
            reason_rank.get(run["comparison"]["competitive_reason"], -1),
        ),
        reverse=True,
    )


def write_search_outputs(output_dir: Path, results: dict[str, Any]) -> tuple[Path, Path, Path]:
    """Write search JSON, CSV, and Markdown outputs."""
    json_path = output_dir / "search_results.json"
    csv_path = output_dir / "search_summary.csv"
    markdown_path = output_dir / "search_report.md"
    json_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    write_search_summary_csv(csv_path, results)
    markdown_path.write_text(render_search_report(results), encoding="utf-8")
    print(f"Search results written: {json_path}")
    print(f"Search CSV written: {csv_path}")
    print(f"Search report written: {markdown_path}")
    return json_path, csv_path, markdown_path


def write_search_summary_csv(path: Path, results: dict[str, Any]) -> None:
    """Write one summary row per candidate run."""
    fieldnames = [
        "candidate_id",
        "seed",
        "weight_variant",
        "hidden_threshold",
        "output_threshold",
        "leak",
        "reset_on_spike",
        "noise_probability",
        "jitter_probability",
        "dropout_probability",
        "candidate_f1",
        "reference_f1",
        "f1_delta",
        "candidate_accuracy",
        "reference_accuracy",
        "candidate_activity",
        "reference_activity",
        "activity_delta",
        "competitive_reason",
        "recommendation",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for run in results["runs"]:
            row = search_csv_row(run, results["decision"]["recommendation"])
            writer.writerow(row)


def search_csv_row(run: dict[str, Any], recommendation: str) -> dict[str, Any]:
    parameters = run["parameters"]
    comparison = run["comparison"]
    return {
        "candidate_id": run["candidate_id"],
        "seed": run["seed"],
        "weight_variant": run["weight_variant"],
        "hidden_threshold": parameters.get("classifiers.tiny_snn_v2.hidden_threshold", ""),
        "output_threshold": parameters.get("classifiers.tiny_snn_v2.output_threshold", ""),
        "leak": parameters.get("classifiers.tiny_snn_v2.leak", ""),
        "reset_on_spike": parameters.get("classifiers.tiny_snn_v2.reset_on_spike", ""),
        "noise_probability": parameters.get("dataset.noise_probability", ""),
        "jitter_probability": parameters.get("dataset.jitter_probability", ""),
        "dropout_probability": parameters.get("dataset.dropout_probability", ""),
        "candidate_f1": comparison["candidate_f1"],
        "reference_f1": comparison["reference_f1"],
        "f1_delta": comparison["f1_delta"],
        "candidate_accuracy": run["classifiers"]["tiny_snn_v2"]["accuracy"],
        "reference_accuracy": run["classifiers"]["fsm"]["accuracy"],
        "candidate_activity": comparison["candidate_activity"],
        "reference_activity": comparison["reference_activity"],
        "activity_delta": comparison["activity_delta"],
        "competitive_reason": comparison["competitive_reason"],
        "recommendation": recommendation,
    }


def render_search_report(results: dict[str, Any]) -> str:
    """Render a Markdown report for SNN parameter search."""
    search = results["search"]
    selection = results["selection"]
    decision = results["decision"]
    lines = [
        "# Tiny SNN v2 Parameter Search Report",
        "",
        "## Search Setup",
        "",
        f"- Name: `{search['name']}`",
        f"- Candidate runs: `{search['candidate_count']}`",
        f"- Seeds: `{search['seeds']}`",
        f"- Weight variants: `{search['weight_variants']}`",
        f"- Dataset parameters: `{search['dataset_parameters']}`",
        f"- SNN parameters: `{search['snn_parameters']}`",
        "",
        "## Candidate Selection Coverage",
        "",
        f"- Strategy: `{selection['strategy']}`",
        f"- Full grid candidates: `{selection['full_grid_candidate_count']}`",
        f"- Evaluated candidates: `{selection['evaluated_candidate_count']}`",
        f"- Skipped candidates: `{selection['skipped_candidate_count']}`",
        "",
        "### Weight Variants",
        "",
        "| Weight Variant | Count |",
        "|---|---:|",
    ]
    for variant, count in selection["coverage"]["weight_variants"].items():
        lines.append(f"| {variant} | {count} |")
    lines.extend(
        [
            "",
            "### Seeds",
            "",
            "| Seed | Count |",
            "|---|---:|",
        ]
    )
    for seed, count in selection["coverage"]["seeds"].items():
        lines.append(f"| {seed} | {count} |")
    lines.extend(
        [
            "",
            "### Dataset Conditions",
            "",
            "| Dataset Condition | Count |",
            "|---|---:|",
        ]
    )
    for condition, count in selection["coverage"]["dataset_conditions"].items():
        lines.append(f"| `{condition}` | {count} |")
    lines.extend(
        [
            "",
            "## Top Candidates By F1",
            "",
            "| Candidate | Variant | Seed | Candidate F1 | Reference F1 | Delta | Activity Delta | Reason |",
            "|---|---|---:|---:|---:|---:|---:|---|",
        ]
    )
    for run in results["runs"][:10]:
        row = run["comparison"]
        lines.append(
            f"| {run['candidate_id']} | {run['weight_variant']} | {run['seed']} | "
            f"{row['candidate_f1']:.4f} | {row['reference_f1']:.4f} | {row['f1_delta']:.4f} | "
            f"{row['activity_delta']:.2f} | {row['competitive_reason']} |"
        )

    lines.extend(
        [
            "",
            "## Lower-Activity Competitive Candidates",
            "",
        ]
    )
    activity_candidates = [
        run
        for run in results["runs"]
        if run["comparison"]["competitive_reason"] == "activity_win_within_f1_tolerance"
    ]
    if activity_candidates:
        lines.extend(
            [
                "| Candidate | Variant | F1 Delta | Activity Delta | Parameters |",
                "|---|---|---:|---:|---|",
            ]
        )
        for run in sorted(activity_candidates, key=lambda item: item["comparison"]["activity_delta"])[:10]:
            row = run["comparison"]
            lines.append(
                f"| {run['candidate_id']} | {run['weight_variant']} | {row['f1_delta']:.4f} | "
                f"{row['activity_delta']:.2f} | `{run['parameters']}` |"
            )
    else:
        lines.append("- No candidate had lower software activity while staying within the F1 tolerance.")

    lines.extend(
        [
            "",
            "## Best Candidate By Scenario",
            "",
            "| Scenario | Candidate | Variant | F1 | Accuracy |",
            "|---|---|---|---:|---:|",
        ]
    )
    for scenario, row in results["aggregate"]["best_candidate_by_scenario"].items():
        lines.append(
            f"| {scenario} | {row['candidate_id']} | {row['weight_variant']} | "
            f"{row['f1']:.4f} | {row['accuracy']:.4f} |"
        )

    lines.extend(
        [
            "",
            "## Weight Variant Summary",
            "",
            "| Variant | Runs | Mean F1 | Best F1 | Mean Activity | Competitive Runs |",
            "|---|---:|---:|---:|---:|---:|",
        ]
    )
    for variant, summary in results["aggregate"]["by_weight_variant"].items():
        lines.append(
            f"| {variant} | {summary['runs']} | {summary['mean_candidate_f1']:.4f} | "
            f"{summary['best_candidate_f1']:.4f} | {summary['mean_candidate_activity']:.2f} | "
            f"{summary['competitive_runs']} |"
        )

    lines.extend(
        [
            "",
            "## Decision Summary",
            "",
            f"- Recommendation: `{decision['recommendation']}`.",
            f"- Reason: {decision['reason']}",
            f"- Best candidate: `{decision['best_candidate_id']}` using `{decision['best_weight_variant']}`.",
            f"- Competitive candidates: `{decision['competitive_candidate_count']}`.",
            f"- F1 wins: `{decision['f1_win_count']}`.",
            f"- Activity wins within F1 tolerance: `{decision['activity_win_within_tolerance_count']}`.",
            f"- {decision['activity_note']}",
            "",
            "## Notes and Limitations",
            "",
            "This is deterministic parameter search over fixed low-precision weights, not training. "
            "Activity metrics are software operation proxies, not hardware power or energy. "
            "RTL simulation and synthesis are required before making hardware conclusions.",
            "",
        ]
    )
    return "\n".join(lines)


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run deterministic tiny_snn_v2 parameter search.")
    parser.add_argument("--config", type=Path, default=Path("configs/snn_search_default.json"))
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--max-candidates", type=int)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        config = load_search_config(args.config)
        print(f"SNN search configuration loaded: {args.config}")
        run_snn_search(config, output_dir=args.output_dir, max_candidates=args.max_candidates)
        return 0
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
