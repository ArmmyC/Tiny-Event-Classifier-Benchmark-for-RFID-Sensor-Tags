from __future__ import annotations

import numpy as np

from .base import Classifier


class FSMClassifier(Classifier):
    """Detect an ordered channel pattern while tolerating bounded gaps."""

    name = "fsm"

    def __init__(self, pattern: tuple[int, ...] = (0, 1, 2), max_gap: int = 6):
        self.pattern = pattern
        self.max_gap = max_gap

    def predict_one(self, sequence: np.ndarray) -> int:
        progress = 0
        last_match = -1
        for cycle, row in enumerate(sequence):
            if progress and cycle - last_match > self.max_gap:
                progress = 0
                last_match = -1
            if row[self.pattern[progress]]:
                progress += 1
                last_match = cycle
                if progress == len(self.pattern):
                    return 1
        return 0

    def active_ops_one(self, sequence: np.ndarray) -> int:
        return int(sequence.shape[0] * 2 + np.count_nonzero(sequence.sum(axis=1)))
