.PHONY: data eval benchmark sweep snn-search temporal-benchmark test clean

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

test:
	python -m pytest

clean:
	rm -f data/generated/*.npy data/generated/*.npz data/generated/*.txt data/generated/*.hex data/generated/metadata.json results/benchmark_results.json results/benchmark_report.md results/sweeps/sweep_results.json results/sweeps/sweep_summary.csv results/sweeps/sweep_report.md results/snn_search/search_results.json results/snn_search/search_summary.csv results/snn_search/search_report.md results/accuracy/*.json results/vcd/*.vcd sim.out
	python -c "import pathlib, shutil; [shutil.rmtree(pathlib.Path(p), ignore_errors=True) for p in ('results/sweeps/generated', 'results/sweeps/runs', 'results/snn_search/generated', 'results/snn_search/runs')]"
