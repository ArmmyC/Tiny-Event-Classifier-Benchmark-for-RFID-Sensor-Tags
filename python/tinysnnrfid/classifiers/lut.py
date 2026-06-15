from __future__ import annotations

import numpy as np

from .base import Classifier


class LUTLikeClassifier(Classifier):
    """Map compact binary sequence features through a deterministic lookup table."""

    name = "lut_like"

    def __init__(self, pattern: tuple[int, ...] = (0, 1, 2), max_total_spikes: int = 10):
        self.pattern = pattern
        self.max_total_spikes = max_total_spikes
        self._table = {
            (seen_all, ordered, sparse): int(seen_all and ordered and sparse)
            for seen_all in (False, True)
            for ordered in (False, True)
            for sparse in (False, True)
        }

    def predict_one(self, sequence: np.ndarray) -> int:
        first_hits: list[int] = []
        for channel in self.pattern:
            hits = np.flatnonzero(sequence[:, channel])
            first_hits.append(int(hits[0]) if hits.size else sequence.shape[0] + 1)
        seen_all = all(hit <= sequence.shape[0] for hit in first_hits)
        ordered = all(left < right for left, right in zip(first_hits, first_hits[1:]))
        sparse = int(sequence.sum()) <= self.max_total_spikes
        return self._table[(seen_all, ordered, sparse)]

    def active_ops_one(self, sequence: np.ndarray) -> int:
        return int(sequence.shape[0] * len(self.pattern) + sequence.size + 1)
