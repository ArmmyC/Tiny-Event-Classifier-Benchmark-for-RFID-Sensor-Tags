.PHONY: data eval clean

data:
	python python/generate_dataset.py --num-sequences 1000 --seq-len 32 --noise-prob 0.03 --out-dir data/generated

eval:
	python python/evaluate_python.py --dataset data/generated/noisy_event_dataset.npz --out results/accuracy/python_metrics.json

clean:
	rm -rf data/generated/*.npz data/generated/*.txt results/accuracy/*.json results/vcd/*.vcd sim.out
