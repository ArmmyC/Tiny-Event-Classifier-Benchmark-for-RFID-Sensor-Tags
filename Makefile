.PHONY: data eval benchmark sweep snn-search temporal-benchmark temporal-sweep temporal-snn-search temporal-snn-optimize temporal-snn-v2-search software-evidence research-report research-writeup rtl-doctor rtl-vectors rtl-sim rtl-synth rtl-activity rtl-report rtl-compare rtl-evidence evidence evidence-manifest artifact-card evidence-smoke test clean

data:
	python python/generate_dataset.py --config configs/default.json

eval:
	python python/evaluate_python.py --config configs/default.json

benchmark:
	python python/generate_dataset.py --config configs/default.json
	python python/evaluate_python.py --config configs/default.json
	python -c "print('Benchmark report: results/benchmark_report.md')"

sweep:
	python python/run_sweep.py --config configs/sweep_default.json

snn-search:
	python python/run_snn_search.py --config configs/snn_search_default.json

temporal-benchmark:
	python python/generate_dataset.py --config configs/temporal_hard.json
	python python/evaluate_python.py --config configs/temporal_hard.json

temporal-sweep:
	python python/run_sweep.py --config configs/sweep_temporal_hard.json

temporal-snn-search:
	python python/run_snn_search.py --config configs/snn_search_temporal_hard.json

temporal-snn-optimize:
	python python/run_snn_search.py --config configs/snn_search_temporal_hard_optimized.json
	python python/build_temporal_snn_optimization_gate.py --search-results results/temporal_snn_optimized/search_results.json --previous-search-results results/temporal_snn_search/search_results.json --output-dir results/temporal_snn_optimized

temporal-snn-v2-search:
	python python/run_snn_search.py --config configs/snn_search_temporal_hard_v2.json
	python python/build_temporal_snn_optimization_gate.py --search-results results/temporal_snn_v2_search/search_results.json --previous-search-results results/temporal_snn_optimized/search_results.json --output-dir results/temporal_snn_v2_search

software-evidence: benchmark sweep snn-search temporal-benchmark temporal-sweep temporal-snn-search

research-report:
	python python/build_research_report.py

research-writeup:
	python python/build_research_writeup.py --input-root results --output-dir results

rtl-doctor:
	python python/check_rtl_toolchain.py

rtl-vectors:
	python python/export_rtl_vectors.py --config configs/temporal_hard.json

rtl-sim: rtl-vectors
	bash scripts/run_rtl_sim.sh

rtl-synth:
	bash scripts/run_rtl_synth.sh

rtl-activity:
	python python/summarize_vcd_activity.py

rtl-report:
	python python/summarize_rtl_results.py

rtl-compare:
	python python/compare_rtl_designs.py

rtl-evidence: rtl-vectors rtl-sim rtl-synth rtl-activity rtl-report rtl-compare

evidence: software-evidence rtl-evidence research-report evidence-manifest artifact-card research-writeup

evidence-manifest:
	python python/build_evidence_manifest.py

artifact-card:
	python python/build_artifact_card.py --input-root results --output-dir results

evidence-smoke:
	python python/run_evidence_smoke.py

test:
	python -m pytest

clean:
	rm -f data/generated/*.npy data/generated/*.npz data/generated/*.txt data/generated/*.hex data/generated/metadata.json results/benchmark_results.json results/benchmark_report.md results/research_decision_report.md results/research_decision_summary.json results/evidence_manifest.json results/evidence_manifest.md results/artifact_card.json results/artifact_card.md results/research_writeup.md results/research_writeup_summary.json results/rtl/toolchain_status.json results/rtl/toolchain_status.md results/sweeps/sweep_results.json results/sweeps/sweep_summary.csv results/sweeps/sweep_report.md results/snn_search/search_results.json results/snn_search/search_summary.csv results/snn_search/search_report.md results/temporal_sweeps/sweep_results.json results/temporal_sweeps/sweep_summary.csv results/temporal_sweeps/sweep_report.md results/temporal_snn_search/search_results.json results/temporal_snn_search/search_summary.csv results/temporal_snn_search/search_report.md results/temporal_snn_optimized/search_results.json results/temporal_snn_optimized/search_summary.csv results/temporal_snn_optimized/search_report.md results/temporal_snn_optimized/optimization_gate.json results/temporal_snn_optimized/optimization_gate.md results/temporal_snn_v2_search/search_results.json results/temporal_snn_v2_search/search_summary.csv results/temporal_snn_v2_search/search_report.md results/temporal_snn_v2_search/optimization_gate.json results/temporal_snn_v2_search/optimization_gate.md results/accuracy/*.json results/vcd/*.vcd sim.out
	python -c "import pathlib, shutil; [shutil.rmtree(pathlib.Path(p), ignore_errors=True) for p in ('results/sweeps/generated', 'results/sweeps/runs', 'results/snn_search/generated', 'results/snn_search/runs', 'results/temporal_sweeps/generated', 'results/temporal_sweeps/runs', 'results/temporal_snn_search/generated', 'results/temporal_snn_search/runs', 'results/temporal_snn_optimized/generated', 'results/temporal_snn_optimized/runs', 'results/temporal_snn_v2_search/generated', 'results/temporal_snn_v2_search/runs', 'results/rtl', 'results/smoke')]"
