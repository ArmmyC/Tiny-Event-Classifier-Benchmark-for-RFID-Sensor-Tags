from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np


class Classifier(ABC):
    """Shared interface for benchmark classifier implementations."""

    name: str

    @abstractmethod
    def predict_one(self, sequence: np.ndarray) -> int:
        """Return one binary prediction for a [cycles, channels] sequence."""

    def predict(self, inputs: np.ndarray) -> np.ndarray:
        """Return binary predictions with shape [num_samples]."""
        if inputs.ndim != 3:
            raise ValueError(f"Classifier input must have 3 dimensions, got {inputs.shape}")
        return np.asarray([self.predict_one(sequence) for sequence in inputs], dtype=np.uint8)

    def activity_proxy(self, inputs: np.ndarray) -> dict[str, int | float]:
        """Return software operation proxies; these are not hardware power measurements."""
        operations = np.asarray([self.active_ops_one(sequence) for sequence in inputs], dtype=np.int64)
        return {
            "software_proxy_total_operations": int(operations.sum()),
            "software_proxy_mean_operations": float(operations.mean()) if operations.size else 0.0,
            "software_proxy_max_operations": int(operations.max()) if operations.size else 0,
        }

    @abstractmethod
    def active_ops_one(self, sequence: np.ndarray) -> int:
        """Estimate software operations for one sequence."""
