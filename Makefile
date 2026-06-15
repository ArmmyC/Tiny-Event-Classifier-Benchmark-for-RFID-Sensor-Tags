.PHONY: data eval benchmark test clean

data:
	python python/generate_dataset.py --config configs/default.json

eval:
	python python/evaluate_python.py --config configs/default.json

benchmark: data eval
	@echo "Benchmark report: results/benchmark_report.md"

test:
	python -m pytest

clean:
	rm -f data/generated/*.npy data/generated/*.npz data/generated/*.txt data/generated/*.hex data/generated/metadata.json results/benchmark_results.json results/benchmark_report.md results/accuracy/*.json results/vcd/*.vcd sim.out
