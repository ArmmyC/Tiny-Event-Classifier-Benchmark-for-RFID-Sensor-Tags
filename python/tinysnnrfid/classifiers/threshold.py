from __future__ import annotations

import numpy as np

from .base import Classifier


class ThresholdClassifier(Classifier):
    """Classify from active-cycle and total-spike counts."""

    name = "threshold"

    def __init__(self, min_active_cycles: int = 3, min_total_spikes: int = 3):
        self.min_active_cycles = min_active_cycles
        self.min_total_spikes = min_total_spikes

    def predict_one(self, sequence: np.ndarray) -> int:
        active_cycles = int(np.count_nonzero(sequence.sum(axis=1)))
        return int(active_cycles >= self.min_active_cycles and int(sequence.sum()) >= self.min_total_spikes)

    def active_ops_one(self, sequence: np.ndarray) -> int:
        return int(sequence.shape[0] + sequence.size + sequence.sum())
