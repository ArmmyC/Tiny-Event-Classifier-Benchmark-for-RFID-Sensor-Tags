from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from tinysnnrfid.baselines import (
    FSMClassifier,
    LUTLikeClassifier,
    ThresholdClassifier,
    active_ops_batch,
    predict_batch,
)
from tinysnnrfid.dataset import load_dataset
from tinysnnrfid.metrics import binary_metrics
from tinysnnrfid.snn import TinySNNClassifier


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate Python classifier candidates.")
    parser.add_argument("--dataset", type=Path, default=Path("data/generated/noisy_event_dataset.npz"))
    parser.add_argument("--out", type=Path, default=Path("results/accuracy/python_metrics.json"))
    args = parser.parse_args()

    x, y, config = load_dataset(args.dataset)
    models = {
        "threshold": ThresholdClassifier(),
        "fsm": FSMClassifier(timeout=int(config.get("max_gap", 5)) + 1),
        "lut_like": LUTLikeClassifier(),
        "tiny_snn": TinySNNClassifier(),
    }

    results: dict[str, object] = {"dataset_config": config, "models": {}}
    for name, model in models.items():
        y_pred = predict_batch(model, x)
        ops = active_ops_batch(model, x)
        model_result = binary_metrics(y, y_pred)
        model_result["active_ops_proxy_mean"] = float(np.mean(ops))
        model_result["active_ops_proxy_median"] = float(np.median(ops))
        results["models"][name] = model_result

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
