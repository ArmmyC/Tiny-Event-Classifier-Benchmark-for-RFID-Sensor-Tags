"""Backward-compatible imports for the original benchmark scripts."""

from __future__ import annotations

import numpy as np

from .classifiers import FSMClassifier, LUTLikeClassifier, ThresholdClassifier


def predict_batch(model: object, inputs: np.ndarray) -> np.ndarray:
    return model.predict(inputs)  # type: ignore[attr-defined,no-any-return]


def active_ops_batch(model: object, inputs: np.ndarray) -> np.ndarray:
    return np.asarray([model.active_ops_one(sequence) for sequence in inputs], dtype=np.int64)  # type: ignore[attr-defined]


__all__ = ["FSMClassifier", "LUTLikeClassifier", "ThresholdClassifier", "predict_batch", "active_ops_batch"]
