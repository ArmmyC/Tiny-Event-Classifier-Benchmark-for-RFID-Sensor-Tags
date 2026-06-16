from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Any


RECOMMENDATIONS = {
    "continue_to_snn_rtl_candidate",
    "continue_software_snn_search",
    "prioritize_fsm_or_lut_baseline",
    "insufficient_data",
}


def _load_json(path: Path) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    info: dict[str, Any] = {"path": str(path), "found": path.is_file()}
    if not path.is_file():
        return None, info
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        info["error"] = str(exc)
        return None, info
    return payload, info


def _best_candidate_f1(payload: dict[str, Any] | None) -> float | None:
    if not payload:
        return None
    decision = payload.get("decision", {})
    value = decision.get("best_candidate_f1")
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    runs = payload.get("runs", [])
    values = [
        float(run.get("comparison", {}).get("candidate_f1"))
        for run in runs
        if isinstance(run.get("comparison", {}).get("candidate_f1"), (int, float))
    ]
    return max(values) if values else None


def _competitive_count(payload: dict[str, Any] | None) -> int | None:
    if not payload:
        return None
    decision = payload.get("decision", {})
    value = decision.get("competitive_candidate_count")
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    runs = payload.get("runs", [])
    return sum(1 for run in runs if run.get("comparison", {}).get("competitive") is True)


def _f1_win_count(payload: dict[str, Any] | None) -> int:
    if not payload:
        return 0
    decision = payload.get("decision", {})
    value = decision.get("f1_win_count")
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    runs = payload.get("runs", [])
    return sum(1 for run in runs if run.get("comparison", {}).get("competitive_reason") == "f1_win")


def _activity_win_count(payload: dict[str, Any] | None) -> int:
    if not payload:
        return 0
    decision = payload.get("decision", {})
    value = decision.get("activity_win_within_tolerance_count")
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    runs = payload.get("runs", [])
    return sum(
        1
        for run in runs
        if run.get("comparison", {}).get("competitive_reason") == "activity_win_within_f1_tolerance"
    )


def _candidate_count(payload: dict[str, Any] | None) -> int:
    if not payload:
        return 0
    search = payload.get("search", {})
    value = search.get("candidate_count")
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    runs = payload.get("runs", [])
    return len(runs) if isinstance(runs, list) else 0


def build_optimization_gate(
    search_results_path: str | Path,
    output_dir: str | Path,
    previous_search_results_path: str | Path | None = None,
) -> dict[str, Any]:
    """Build the temporal-hard SNN optimization gate from generated search outputs."""
    search_path = Path(search_results_path)
    previous_path = Path(previous_search_results_path) if previous_search_results_path else None
    output_root = Path(output_dir)
    payload, search_info = _load_json(search_path)
    previous_payload, previous_info = (
        _load_json(previous_path) if previous_path is not None else (None, {"path": None, "found": False})
    )

    candidate_count = _candidate_count(payload)
    competitive_count = _competitive_count(payload)
    best_f1 = _best_candidate_f1(payload)
    previous_best_f1 = _best_candidate_f1(previous_payload)
    improved_over_previous = (
        best_f1 is not None and previous_best_f1 is not None and best_f1 > previous_best_f1
    )

    if payload is None or candidate_count == 0 or competitive_count is None or best_f1 is None:
        recommendation = "insufficient_data"
        reason = "Optimized temporal-hard search results are missing or incomplete."
    elif competitive_count > 0:
        recommendation = "continue_to_snn_rtl_candidate"
        reason = "At least one optimized temporal-hard SNN candidate is competitive against the FSM reference."
    elif improved_over_previous:
        recommendation = "continue_software_snn_search"
        reason = "The optimized search improves best temporal-hard SNN F1 versus the previous search but is not yet competitive."
    else:
        recommendation = "prioritize_fsm_or_lut_baseline"
        reason = "The optimized temporal-hard search found no competitive candidate and no measured improvement over the previous search."

    gate = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "recommendation": recommendation,
        "reason": reason,
        "inputs": {
            "optimized_search": search_info,
            "previous_temporal_search": previous_info,
        },
        "optimized": {
            "candidate_count": candidate_count,
            "best_candidate_f1": best_f1,
            "competitive_candidate_count": competitive_count,
            "f1_win_count": _f1_win_count(payload),
            "activity_win_within_tolerance_count": _activity_win_count(payload),
        },
        "previous": {
            "best_candidate_f1": previous_best_f1,
            "competitive_candidate_count": _competitive_count(previous_payload),
        },
        "improved_over_previous": improved_over_previous,
        "activity_note": "Software activity is a proxy, not hardware power, measured silicon power, or energy.",
    }
    output_root.mkdir(parents=True, exist_ok=True)
    json_path = output_root / "optimization_gate.json"
    markdown_path = output_root / "optimization_gate.md"
    json_path.write_text(json.dumps(gate, indent=2), encoding="utf-8")
    markdown_path.write_text(render_optimization_gate(gate), encoding="utf-8")
    print(f"Optimization gate written: {json_path}")
    print(f"Optimization gate report written: {markdown_path}")
    return gate


def _fmt(value: Any) -> str:
    if value is None:
        return "-"
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def render_optimization_gate(gate: dict[str, Any]) -> str:
    """Render the optimization gate as Markdown."""
    optimized = gate["optimized"]
    previous = gate["previous"]
    lines = [
        "# Temporal-Hard SNN Optimization Gate",
        "",
        "## Recommendation",
        "",
        f"- Recommendation: `{gate['recommendation']}`.",
        f"- Reason: {gate['reason']}",
        "",
        "## Optimized Search Evidence",
        "",
        f"- Candidate count: `{optimized['candidate_count']}`.",
        f"- Best candidate F1: `{_fmt(optimized['best_candidate_f1'])}`.",
        f"- Competitive candidates: `{optimized['competitive_candidate_count']}`.",
        f"- F1 wins: `{optimized['f1_win_count']}`.",
        f"- Activity wins within F1 tolerance: `{optimized['activity_win_within_tolerance_count']}`.",
        "",
        "## Previous Temporal-Hard Context",
        "",
        f"- Previous best candidate F1: `{_fmt(previous['best_candidate_f1'])}`.",
        f"- Previous competitive candidates: `{_fmt(previous['competitive_candidate_count'])}`.",
        f"- Improved over previous: `{gate['improved_over_previous']}`.",
        "",
        "## Notes and Limitations",
        "",
        f"- {gate['activity_note']}",
        "- This gate is software/search evidence only and does not justify hardware claims by itself.",
        "- RTL simulation, synthesis, and signoff evidence are still required before any hardware conclusion.",
        "",
    ]
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build temporal-hard SNN optimization gate report.")
    parser.add_argument(
        "--search-results",
        type=Path,
        default=Path("results/temporal_snn_optimized/search_results.json"),
    )
    parser.add_argument(
        "--previous-search-results",
        type=Path,
        default=Path("results/temporal_snn_search/search_results.json"),
    )
    parser.add_argument("--output-dir", type=Path, default=Path("results/temporal_snn_optimized"))
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        build_optimization_gate(args.search_results, args.output_dir, args.previous_search_results)
        return 0
    except (OSError, KeyError, TypeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
