from __future__ import annotations

import numpy as np

from .base import Classifier


class TinySNNClassifier(Classifier):
    """Integer integrate-and-fire pattern detector with reset on output spikes."""

    name = "tiny_snn"

    def __init__(
        self,
        pattern: tuple[int, ...] = (0, 1, 2),
        threshold: int = 2,
        leak: int = 1,
        membrane_max: int = 7,
        max_gap: int = 6,
    ):
        self.pattern = pattern
        self.threshold = threshold
        self.leak = leak
        self.membrane_max = membrane_max
        self.max_gap = max_gap

    def predict_one(self, sequence: np.ndarray) -> int:
        membrane = 0
        progress = 0
        last_spike = -1
        for cycle, row in enumerate(sequence):
            if progress and cycle - last_spike > self.max_gap:
                progress = 0
                membrane = 0
            drive = int(row[self.pattern[progress]]) * self.threshold
            inhibitory = int(row.sum()) - int(row[self.pattern[progress]])
            leaked = max(0, membrane - self.leak)
            membrane = min(self.membrane_max, max(0, leaked + drive - inhibitory))
            if membrane >= self.threshold:
                membrane = 0
                progress += 1
                last_spike = cycle
                if progress == len(self.pattern):
                    return 1
        return 0

    def active_ops_one(self, sequence: np.ndarray) -> int:
        active_cycles = int(np.count_nonzero(sequence.sum(axis=1)))
        return int(sequence.shape[0] * 4 + active_cycles * 2 + sequence.sum())
