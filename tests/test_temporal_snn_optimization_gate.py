from __future__ import annotations

import json
from pathlib import Path

from tinysnnrfid.build_temporal_snn_optimization_gate import (
    RECOMMENDATIONS,
    build_optimization_gate,
    render_optimization_gate,
)
from tinysnnrfid.config import load_config
from tinysnnrfid.run_snn_search import WEIGHT_VARIANTS, load_search_config


ROOT = Path(__file__).resolve().parents[1]


def _weights_for_variant(name: str) -> list[int]:
    variant = WEIGHT_VARIANTS[name]
    return [weight for row in variant["input_weights"] for weight in row] + variant["output_weights"]


def _write_search(path: Path, *, best_f1: float, competitive: int, candidates: int = 3) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "search": {"candidate_count": candidates},
                "decision": {
                    "best_candidate_f1": best_f1,
                    "competitive_candidate_count": competitive,
                    "f1_win_count": competitive,
                    "activity_win_within_tolerance_count": 0,
                },
                "runs": [],
            }
        ),
        encoding="utf-8",
    )


def test_optimized_temporal_search_config_loads_and_targets_temporal_hard() -> None:
    config = load_search_config("configs/snn_search_temporal_hard_optimized.json")
    assert config["base_config"] == "configs/temporal_hard.json"
    assert config["output_dir"] == "results/temporal_snn_optimized"
    assert config["dataset_output_root"] == "results/temporal_snn_optimized/generated"
    assert config["comparison"]["reference_classifier"] == "fsm"
    assert config["comparison"]["candidate_classifier"] == "tiny_snn_v2"
    assert config["selection"]["strategy"] == "balanced_round_robin"
    assert config["limits"]["max_candidates"] > 80
    assert load_config(config["base_config"])["scenario_suite"]["mode"] == "temporal_hard"


def test_optimized_config_includes_new_temporal_hard_variants() -> None:
    config = load_search_config("configs/snn_search_temporal_hard_optimized.json")
    assert {"temporal_gap_guard", "reversal_inhibitory_guard"} <= set(config["weight_variants"])

    temporal_gap_weights = _weights_for_variant("temporal_gap_guard")
    reversal_weights = _weights_for_variant("reversal_inhibitory_guard")
    assert set(temporal_gap_weights) <= {-1, 0, 1}
    assert all(-2 <= weight <= 2 for weight in reversal_weights)


def test_gate_recommends_rtl_candidate_for_competitive_input(tmp_path) -> None:
    optimized = tmp_path / "optimized" / "search_results.json"
    previous = tmp_path / "previous" / "search_results.json"
    _write_search(optimized, best_f1=0.82, competitive=1)
    _write_search(previous, best_f1=0.80, competitive=0)

    gate = build_optimization_gate(optimized, tmp_path / "out", previous)

    assert gate["recommendation"] == "continue_to_snn_rtl_candidate"
    assert gate["recommendation"] in RECOMMENDATIONS
    assert (tmp_path / "out" / "optimization_gate.json").is_file()
    assert (tmp_path / "out" / "optimization_gate.md").is_file()


def test_gate_recommends_software_search_for_improvement_without_competitiveness(tmp_path) -> None:
    optimized = tmp_path / "optimized" / "search_results.json"
    previous = tmp_path / "previous" / "search_results.json"
    _write_search(optimized, best_f1=0.81, competitive=0)
    _write_search(previous, best_f1=0.78, competitive=0)

    gate = build_optimization_gate(optimized, tmp_path / "out", previous)

    assert gate["recommendation"] == "continue_software_snn_search"
    assert gate["improved_over_previous"] is True


def test_gate_prioritizes_baseline_when_no_improvement_or_competitiveness(tmp_path) -> None:
    optimized = tmp_path / "optimized" / "search_results.json"
    previous = tmp_path / "previous" / "search_results.json"
    _write_search(optimized, best_f1=0.75, competitive=0)
    _write_search(previous, best_f1=0.78, competitive=0)

    gate = build_optimization_gate(optimized, tmp_path / "out", previous)

    assert gate["recommendation"] == "prioritize_fsm_or_lut_baseline"


def test_gate_reports_insufficient_data_for_missing_optimized_search(tmp_path) -> None:
    gate = build_optimization_gate(
        tmp_path / "missing" / "search_results.json",
        tmp_path / "out",
        tmp_path / "previous" / "search_results.json",
    )

    assert gate["recommendation"] == "insufficient_data"


def test_gate_markdown_contains_proxy_limitation_text() -> None:
    markdown = render_optimization_gate(
        {
            "recommendation": "continue_software_snn_search",
            "reason": "Synthetic reason.",
            "optimized": {
                "candidate_count": 2,
                "best_candidate_f1": 0.8,
                "competitive_candidate_count": 0,
                "f1_win_count": 0,
                "activity_win_within_tolerance_count": 0,
            },
            "previous": {
                "best_candidate_f1": 0.7,
                "competitive_candidate_count": 0,
            },
            "improved_over_previous": True,
            "activity_note": "Software activity is a proxy, not hardware power, measured silicon power, or energy.",
        }
    )
    assert "not hardware power" in markdown
    assert "does not justify hardware claims" in markdown


def test_makefile_contains_temporal_snn_optimize_without_evidence_integration() -> None:
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    assert "temporal-snn-optimize" in makefile
    assert "configs/snn_search_temporal_hard_optimized.json" in makefile
    assert "python python/build_temporal_snn_optimization_gate.py" in makefile
    evidence_header = next(line for line in makefile.splitlines() if line.startswith("evidence:"))
    assert "temporal-snn-optimize" not in evidence_header.split(":", 1)[1].split()


def test_clean_removes_temporal_snn_optimized_outputs() -> None:
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    for path in (
        "results/temporal_snn_optimized/search_results.json",
        "results/temporal_snn_optimized/search_summary.csv",
        "results/temporal_snn_optimized/search_report.md",
        "results/temporal_snn_optimized/optimization_gate.json",
        "results/temporal_snn_optimized/optimization_gate.md",
        "results/temporal_snn_optimized/generated",
        "results/temporal_snn_optimized/runs",
    ):
        assert path in makefile
