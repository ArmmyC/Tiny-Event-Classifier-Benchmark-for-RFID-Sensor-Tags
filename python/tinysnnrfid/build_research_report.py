from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Any


EXPECTED_INPUTS = {
    "legacy_benchmark": Path("results/benchmark_results.json"),
    "legacy_sweep": Path("results/sweeps/sweep_results.json"),
    "legacy_snn_search": Path("results/snn_search/search_results.json"),
    "temporal_sweep": Path("results/temporal_sweeps/sweep_results.json"),
    "temporal_snn_search": Path("results/temporal_snn_search/search_results.json"),
    "rtl_baselines": Path("results/rtl/rtl_summary.json"),
    "rtl_comparison": Path("results/rtl/rtl_comparison_summary.json"),
}

OPTIONAL_INPUTS = {"rtl_baselines", "rtl_comparison"}

RECOMMENDATIONS = {
    "continue_snn_optimization",
    "add_harder_temporal_scenarios",
    "prioritize_fsm_or_lut_rtl_baseline",
    "insufficient_data",
}

RTL_BASELINES = ("threshold", "fsm", "lut_like", "tiny_snn_v2", "tiny_snn_v2_sparse_activity")


def load_research_inputs(
    input_paths: dict[str, str | Path] | None = None,
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]], list[str]]:
    """Load available experiment outputs without rerunning any experiment."""
    paths = input_paths or EXPECTED_INPUTS
    inputs: dict[str, dict[str, Any]] = {}
    evidence: dict[str, dict[str, Any]] = {}
    missing: list[str] = []
    for name, raw_path in paths.items():
        path = Path(raw_path)
        found = path.is_file()
        inputs[name] = {"path": str(path), "found": found}
        if not found:
            missing.append(str(path))
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            raise ValueError(f"Could not read research input {path}: {exc}") from exc
        if not isinstance(payload, dict):
            raise ValueError(f"Research input root must be an object: {path}")
        evidence[name] = extract_evidence(name, payload)
    return inputs, evidence, missing


def extract_evidence(name: str, payload: dict[str, Any]) -> dict[str, Any]:
    if name == "legacy_benchmark":
        return extract_benchmark_evidence(payload)
    if name in {"legacy_sweep", "temporal_sweep"}:
        return extract_sweep_evidence(payload)
    if name in {"legacy_snn_search", "temporal_snn_search"}:
        return extract_search_evidence(payload)
    if name == "rtl_baselines":
        return extract_rtl_evidence(payload)
    if name == "rtl_comparison":
        return extract_rtl_comparison_evidence(payload)
    return {"kind": "unknown"}


def extract_rtl_evidence(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "kind": "rtl_baselines",
        "simulations": payload.get("simulations", {}),
        "synthesis": payload.get("synthesis", {}),
        "activity": payload.get("activity", {}),
        "recommendation_context": payload.get("recommendation_context", {}),
        "note": payload.get("note"),
    }


def extract_rtl_comparison_evidence(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "kind": "rtl_comparison",
        "recommendation": payload.get("recommendation"),
        "reason": payload.get("reason"),
        "reference_design": payload.get("reference_design"),
        "candidate_design": payload.get("candidate_design"),
        "legacy_snn_design": payload.get("legacy_snn_design"),
        "designs": payload.get("designs", {}),
        "tiny_snn_v2_context": payload.get("tiny_snn_v2_context", {}),
        "tiny_snn_v2_sparse_activity_context": payload.get("tiny_snn_v2_sparse_activity_context", {}),
        "note": payload.get("note"),
    }


def extract_benchmark_evidence(payload: dict[str, Any]) -> dict[str, Any]:
    classifiers = payload.get("classifiers", {})
    ranking = sorted(
        (
            {
                "classifier": name,
                "f1": float(values.get("f1", 0.0)),
                "accuracy": float(values.get("accuracy", 0.0)),
                "activity": float(values.get("activity_proxy", {}).get("software_proxy_mean_operations", 0.0)),
            }
            for name, values in classifiers.items()
        ),
        key=lambda row: (row["f1"], row["accuracy"], row["classifier"]),
        reverse=True,
    )
    scenarios: dict[str, dict[str, Any]] = {}
    scenario_names = sorted(
        {scenario for values in classifiers.values() for scenario in values.get("per_scenario", {})}
    )
    for scenario in scenario_names:
        candidates = []
        for classifier, values in classifiers.items():
            metrics = values.get("per_scenario", {}).get(scenario)
            if metrics:
                candidates.append((float(metrics.get("f1", 0.0)), float(metrics.get("accuracy", 0.0)), classifier))
        if candidates:
            best_f1, best_accuracy, best_classifier = max(candidates)
            scenarios[scenario] = {
                "classifier": best_classifier,
                "f1": best_f1,
                "accuracy": best_accuracy,
            }
    return {
        "kind": "benchmark",
        "ranking": ranking,
        "best_classifier": ranking[0]["classifier"] if ranking else None,
        "tiny_snn_v2": _classifier_metrics(classifiers.get("tiny_snn_v2")),
        "fsm": _classifier_metrics(classifiers.get("fsm")),
        "scenario_winners": scenarios,
    }


def _classifier_metrics(values: Any) -> dict[str, Any] | None:
    if not isinstance(values, dict):
        return None
    return {
        "f1": float(values.get("f1", 0.0)),
        "accuracy": float(values.get("accuracy", 0.0)),
        "activity": float(values.get("activity_proxy", {}).get("software_proxy_mean_operations", 0.0)),
    }


def extract_sweep_evidence(payload: dict[str, Any]) -> dict[str, Any]:
    decision = payload.get("decision", {})
    comparison = payload.get("comparison", {})
    return {
        "kind": "sweep",
        "recommendation": decision.get("recommendation"),
        "reason": decision.get("reason"),
        "best_overall_classifier": decision.get("best_overall_classifier"),
        "competitive_run_count": int(decision.get("competitive_run_count", len(comparison.get("competitive_runs", [])))),
        "candidate_f1_wins": int(comparison.get("candidate_f1_wins", 0)),
        "candidate_activity_wins_within_f1_tolerance": int(
            comparison.get("candidate_activity_wins_within_f1_tolerance", 0)
        ),
        "scenario_winners": payload.get("aggregate", {}).get("best_by_scenario", {}),
    }


def extract_search_evidence(payload: dict[str, Any]) -> dict[str, Any]:
    decision = payload.get("decision", {})
    selection = payload.get("selection", {})
    return {
        "kind": "search",
        "recommendation": decision.get("recommendation"),
        "reason": decision.get("reason"),
        "best_candidate_id": decision.get("best_candidate_id"),
        "best_weight_variant": decision.get("best_weight_variant"),
        "competitive_candidate_count": int(decision.get("competitive_candidate_count", 0)),
        "f1_win_count": int(decision.get("f1_win_count", 0)),
        "activity_win_within_tolerance_count": int(
            decision.get("activity_win_within_tolerance_count", 0)
        ),
        "selection": {
            "strategy": selection.get("strategy"),
            "full_grid_candidate_count": selection.get("full_grid_candidate_count"),
            "evaluated_candidate_count": selection.get("evaluated_candidate_count"),
            "coverage": selection.get("coverage", {}),
        },
        "scenario_winners": payload.get("aggregate", {}).get("best_candidate_by_scenario", {}),
    }


def choose_recommendation(
    evidence: dict[str, dict[str, Any]],
) -> tuple[str, str]:
    """Combine existing experiment recommendations using conservative research rules."""
    decision_sources = [
        evidence.get("legacy_sweep"),
        evidence.get("legacy_snn_search"),
        evidence.get("temporal_sweep"),
        evidence.get("temporal_snn_search"),
    ]
    available_decisions = [item for item in decision_sources if item]
    if not available_decisions:
        return "insufficient_data", "No sweep or SNN-search outputs were available."
    search_sources = [evidence.get("legacy_snn_search"), evidence.get("temporal_snn_search")]
    if any(item and item.get("recommendation") == "continue_snn_optimization" for item in search_sources):
        return (
            "continue_snn_optimization",
            "At least one SNN search found a true F1 win or lower-software-activity candidate within F1 tolerance.",
        )
    temporal_sources = [evidence.get("temporal_sweep"), evidence.get("temporal_snn_search")]
    if not any(temporal_sources):
        return (
            "add_harder_temporal_scenarios",
            "Legacy evidence is available, but temporal-hard sweep and search evidence are missing.",
        )
    available_temporal = [item for item in temporal_sources if item]
    if available_temporal and all(_temporal_favors_baseline(item) for item in available_temporal):
        return (
            "prioritize_fsm_or_lut_rtl_baseline",
            "All available temporal-hard sweep/search evidence favors FSM or LUT baselines over tiny_snn_v2.",
        )
    return (
        "add_harder_temporal_scenarios",
        "The available evidence is mixed or incomplete and does not yet support a stable implementation choice.",
    )


def _temporal_favors_baseline(item: dict[str, Any]) -> bool:
    recommendation = item.get("recommendation")
    if recommendation == "prioritize_fsm_or_lut_rtl_baseline":
        return True
    if item.get("kind") == "sweep":
        return (
            item.get("best_overall_classifier") in {"fsm", "lut_like"}
            and item.get("competitive_run_count", 0) == 0
        )
    return False


def build_summary(
    inputs: dict[str, dict[str, Any]],
    evidence: dict[str, dict[str, Any]],
    missing_inputs: list[str],
) -> dict[str, Any]:
    recommendation, reason = choose_recommendation(evidence)
    highlights = build_highlights(evidence)
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": inputs,
        "recommendation": recommendation,
        "reason": reason,
        "highlights": highlights,
        "missing_inputs": missing_inputs,
        "evidence": evidence,
        "activity_note": "Activity metrics are software operation proxies, not hardware power or energy.",
    }


def build_highlights(evidence: dict[str, dict[str, Any]]) -> list[str]:
    highlights: list[str] = []
    benchmark = evidence.get("legacy_benchmark")
    if benchmark and benchmark.get("best_classifier"):
        highlights.append(f"Benchmark best classifier by F1: {benchmark['best_classifier']}.")
    for name, label in (
        ("legacy_sweep", "Legacy sweep"),
        ("legacy_snn_search", "Legacy SNN search"),
        ("temporal_sweep", "Temporal-hard sweep"),
        ("temporal_snn_search", "Temporal-hard SNN search"),
    ):
        item = evidence.get(name)
        if item and item.get("recommendation"):
            highlights.append(f"{label} recommendation: {item['recommendation']}.")
    return highlights


def build_research_report(
    output_dir: str | Path = "results",
    strict: bool = False,
    input_paths: dict[str, str | Path] | None = None,
) -> dict[str, Any]:
    """Read existing outputs and write consolidated JSON and Markdown reports."""
    inputs, evidence, missing = load_research_inputs(input_paths)
    required_missing = [
        values["path"]
        for name, values in inputs.items()
        if name not in OPTIONAL_INPUTS and not values["found"]
    ]
    if strict and required_missing:
        raise ValueError(f"Missing required research input(s): {', '.join(required_missing)}")
    summary = build_summary(inputs, evidence, missing)
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    json_path = directory / "research_decision_summary.json"
    markdown_path = directory / "research_decision_report.md"
    json_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    markdown_path.write_text(render_research_report(summary), encoding="utf-8")
    print(f"Research decision summary written: {json_path}")
    print(f"Research decision report written: {markdown_path}")
    return summary


def render_research_report(summary: dict[str, Any]) -> str:
    evidence = summary["evidence"]
    lines = [
        "# Tiny SNN RFID Research Decision Report",
        "",
        "## Inputs Found",
        "",
        "| Input | Path | Found |",
        "|---|---|---|",
    ]
    for name, values in summary["inputs"].items():
        lines.append(f"| {name} | `{values['path']}` | {'yes' if values['found'] else 'no'} |")
    if summary["missing_inputs"]:
        lines.extend(["", "Missing inputs:"])
        lines.extend(f"- `{path}`" for path in summary["missing_inputs"])
    lines.extend(
        [
            "",
            "## Executive Recommendation",
            "",
            f"- Recommendation: `{summary['recommendation']}`.",
            f"- Reason: {summary['reason']}",
            "",
        ]
    )
    _append_evidence_section(lines, "Legacy Benchmark Evidence", evidence.get("legacy_benchmark"))
    _append_evidence_section(lines, "Legacy Sweep Evidence", evidence.get("legacy_sweep"))
    _append_evidence_section(lines, "Legacy SNN Search Evidence", evidence.get("legacy_snn_search"))
    _append_evidence_section(lines, "Temporal-Hard Sweep Evidence", evidence.get("temporal_sweep"))
    _append_evidence_section(lines, "Temporal-Hard SNN Search Evidence", evidence.get("temporal_snn_search"))
    _append_rtl_evidence_section(lines, evidence.get("rtl_baselines"))
    _append_rtl_comparison_section(lines, evidence.get("rtl_comparison"))
    lines.extend(["## Scenario-Level Findings", ""])
    scenario_rows = _scenario_findings(evidence)
    if scenario_rows:
        lines.extend(["| Source | Scenario | Best Classifier/Candidate | F1 |", "|---|---|---|---:|"])
        lines.extend(scenario_rows)
    else:
        lines.append("- No scenario-level evidence was available.")
    lines.extend(
        [
            "",
            "## Decision Matrix",
            "",
            "| Evidence Source | Recommendation | Competitive Cases |",
            "|---|---|---:|",
        ]
    )
    for name in ("legacy_sweep", "legacy_snn_search", "temporal_sweep", "temporal_snn_search"):
        item = evidence.get(name)
        if not item:
            lines.append(f"| {name} | missing | 0 |")
            continue
        competitive = item.get("competitive_run_count", item.get("competitive_candidate_count", 0))
        lines.append(f"| {name} | {item.get('recommendation') or 'unknown'} | {competitive} |")
    lines.extend(
        [
            "",
            "## Notes and Limitations",
            "",
            "This report only aggregates existing generated outputs; it does not rerun experiments. "
            "Activity metrics are software operation proxies, not hardware power or energy. "
            "RTL simulation and synthesis are still required before making hardware conclusions. "
            "Open-source RTL simulation and synthesis results are not silicon signoff and do not report measured silicon power.",
            "",
        ]
    )
    return "\n".join(lines)


def _append_evidence_section(lines: list[str], title: str, item: dict[str, Any] | None) -> None:
    lines.extend([f"## {title}", ""])
    if not item:
        lines.extend(["- Input not available.", ""])
        return
    if item["kind"] == "benchmark":
        lines.append(f"- Best classifier by F1: `{item.get('best_classifier')}`.")
        if item.get("tiny_snn_v2"):
            lines.append(f"- `tiny_snn_v2` F1: `{item['tiny_snn_v2']['f1']:.4f}`.")
        if item.get("fsm"):
            lines.append(f"- `fsm` F1: `{item['fsm']['f1']:.4f}`.")
    else:
        lines.append(f"- Recommendation: `{item.get('recommendation') or 'unknown'}`.")
        if item.get("reason"):
            lines.append(f"- Reason: {item['reason']}")
        if item["kind"] == "sweep":
            lines.append(f"- Competitive runs: `{item['competitive_run_count']}`.")
            lines.append(f"- Best overall classifier: `{item.get('best_overall_classifier')}`.")
        else:
            lines.append(f"- Best candidate: `{item.get('best_candidate_id')}` using `{item.get('best_weight_variant')}`.")
            lines.append(f"- Competitive candidates: `{item['competitive_candidate_count']}`.")
    lines.append("")


def _scenario_findings(evidence: dict[str, dict[str, Any]]) -> list[str]:
    rows: list[str] = []
    for source, item in evidence.items():
        for scenario, values in item.get("scenario_winners", {}).items():
            winner = values.get("classifier") or values.get("candidate_id") or "unknown"
            f1 = float(values.get("mean_f1", values.get("f1", 0.0)))
            rows.append(f"| {source} | {scenario} | {winner} | {f1:.4f} |")
    return rows


def _append_rtl_evidence_section(lines: list[str], item: dict[str, Any] | None) -> None:
    lines.extend(["## RTL Baseline Evidence", ""])
    if not item:
        lines.extend(["- RTL summary not available. Run `make rtl-report` to summarize optional local tool outputs.", ""])
        return
    simulations = item.get("simulations", {})
    synthesis = item.get("synthesis", {})
    lines.extend(["| Baseline | Simulation | Cell Count Proxy |", "|---|---|---:|"])
    for name in RTL_BASELINES:
        sim_status = simulations.get(name, {}).get("status", "missing")
        cell_count = synthesis.get(name, {}).get("cell_count", "-")
        lines.append(f"| {name} | {sim_status} | {cell_count} |")
    lowest = item.get("recommendation_context", {}).get("lowest_cell_count_baseline")
    if lowest:
        lines.append(f"\n- Lowest available cell-count baseline: `{lowest}`.")
    activity = item.get("activity", {})
    activity_baselines = activity.get("baselines", {}) if isinstance(activity, dict) else {}
    if activity_baselines:
        lines.extend(["", "### RTL Activity Context", "", "| Baseline | Toggle Status | Total Toggles |", "|---|---|---:|"])
        for name in RTL_BASELINES:
            values = activity_baselines.get(name, {})
            if not isinstance(values, dict):
                values = {}
            lines.append(f"| {name} | {values.get('status', 'missing')} | {values.get('total_toggles', '-')} |")
        lowest_toggle = activity.get("recommendation_context", {}).get("lowest_toggle_baseline")
        if lowest_toggle:
            lines.append(f"\n- Lowest available toggle-count baseline: `{lowest_toggle}`.")
        else:
            lines.append("")
        lines.append("- Toggle counts are simulation activity proxies and are not measured silicon power or energy.")
    lines.extend([
        "",
        "Open-source RTL simulation and synthesis results are not silicon signoff. "
        "Cell counts are synthesis proxies, and no measured silicon power is claimed.",
        "",
    ])


def _append_rtl_comparison_section(lines: list[str], item: dict[str, Any] | None) -> None:
    lines.extend(["## RTL SNN-vs-Baseline Comparison", ""])
    if not item:
        lines.extend(["- RTL comparison summary not available. Run `make rtl-compare` after generating RTL summaries.", ""])
        return
    context = item.get("tiny_snn_v2_context", {})
    sparse_context = item.get("tiny_snn_v2_sparse_activity_context", {})
    lines.append(f"- Recommendation: `{item.get('recommendation') or 'unknown'}`.")
    if item.get("reason"):
        lines.append(f"- Reason: {item['reason']}")
    lines.append(f"- Candidate design: `{item.get('candidate_design') or 'tiny_snn_v2_sparse_activity'}`.")
    lines.append(f"- Reference baseline: `{item.get('reference_design') or 'fsm'}`.")
    lines.append(f"- Legacy/default SNN context: `{item.get('legacy_snn_design') or 'tiny_snn_v2'}`.")
    if sparse_context:
        lines.append(
            "- `tiny_snn_v2_sparse_activity` cell ratio vs FSM: "
            f"`{_format_optional(sparse_context.get('cell_ratio_vs_fsm'))}`."
        )
        lines.append(
            "- `tiny_snn_v2_sparse_activity` toggle ratio vs FSM: "
            f"`{_format_optional(sparse_context.get('toggle_ratio_vs_fsm'))}`."
        )
    lines.append(f"- `tiny_snn_v2` legacy cell ratio vs FSM: `{_format_optional(context.get('cell_ratio_vs_fsm'))}`.")
    lines.append(f"- `tiny_snn_v2` legacy toggle ratio vs FSM: `{_format_optional(context.get('toggle_ratio_vs_fsm'))}`.")
    lines.extend([
        "",
        item.get("note")
        or "Cell counts and toggle counts are local-tool proxies, not silicon area or measured power.",
        "",
    ])


def _format_optional(value: Any) -> str:
    if value is None:
        return "-"
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build a consolidated research decision report.")
    parser.add_argument("--output-dir", type=Path, default=Path("results"))
    parser.add_argument("--strict", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        summary = build_research_report(args.output_dir, strict=args.strict)
        if summary["missing_inputs"]:
            print(f"Missing research inputs: {', '.join(summary['missing_inputs'])}")
        print(f"Recommendation: {summary['recommendation']}")
        return 0
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
