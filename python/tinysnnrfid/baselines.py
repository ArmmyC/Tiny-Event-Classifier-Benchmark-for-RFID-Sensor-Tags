from __future__ import annotations

import numpy as np


class ThresholdClassifier:
    """Count active cycles and classify once enough activity is seen."""

    def __init__(self, min_active_cycles: int = 3, min_total_spikes: int = 3):
        self.min_active_cycles = min_active_cycles
        self.min_total_spikes = min_total_spikes

    def predict_one(self, seq: np.ndarray) -> int:
        active_cycles = int(np.count_nonzero(seq.sum(axis=1)))
        total_spikes = int(seq.sum())
        return int(active_cycles >= self.min_active_cycles and total_spikes >= self.min_total_spikes)

    def active_ops_one(self, seq: np.ndarray) -> int:
        # Proxy: one check per cycle plus popcount work for active bits.
        return int(seq.shape[0] + seq.sum())


class FSMClassifier:
    """Detect channel 0, then channel 1, then channel 2 within a timeout."""

    def __init__(self, motif: tuple[int, ...] = (0, 1, 2), timeout: int = 5):
        self.motif = motif
        self.timeout = timeout

    def predict_one(self, seq: np.ndarray) -> int:
        state = 0
        age = 0
        for row in seq:
            if state > 0:
                age += 1
                if age > self.timeout:
                    state = 0
                    age = 0

            needed_channel = self.motif[state]
            if row[needed_channel]:
                state += 1
                age = 0
                if state == len(self.motif):
                    return 1
        return 0

    def active_ops_one(self, seq: np.ndarray) -> int:
        # Proxy: one state check per cycle, plus extra work on active cycles.
        return int(seq.shape[0] + np.count_nonzero(seq.sum(axis=1)))


class LUTLikeClassifier:
    """Small rule tree approximating a LUT or decision-tree classifier."""

    def __init__(self, min_distinct_channels: int = 3, max_total_spikes: int = 10):
        self.min_distinct_channels = min_distinct_channels
        self.max_total_spikes = max_total_spikes

    def predict_one(self, seq: np.ndarray) -> int:
        channel_seen = seq.any(axis=0)
        distinct = int(channel_seen.sum())
        total_spikes = int(seq.sum())
        ordered_score = int(_first_seen_order_score(seq, channels=(0, 1, 2)))
        return int(
            distinct >= self.min_distinct_channels
            and total_spikes <= self.max_total_spikes
            and ordered_score >= 2
        )

    def active_ops_one(self, seq: np.ndarray) -> int:
        # Proxy: small fixed tree plus checks on active cycles.
        return int(8 + seq.shape[0] + 2 * np.count_nonzero(seq.sum(axis=1)))


def _first_seen_order_score(seq: np.ndarray, channels: tuple[int, ...]) -> int:
    first_seen = []
    for ch in channels:
        hits = np.flatnonzero(seq[:, ch])
        first_seen.append(int(hits[0]) if hits.size else 10**9)
    score = 0
    for a, b in zip(first_seen, first_seen[1:]):
        if a < b:
            score += 1
    return score


def predict_batch(model, x: np.ndarray) -> np.ndarray:
    return np.array([model.predict_one(seq) for seq in x], dtype=np.uint8)


def active_ops_batch(model, x: np.ndarray) -> np.ndarray:
    return np.array([model.active_ops_one(seq) for seq in x], dtype=np.int64)
