from __future__ import annotations

from dataclasses import dataclass
import numpy as np


@dataclass
class TinySNNConfig:
    threshold: int = 2
    leak: int = 1
    membrane_min: int = 0
    membrane_max: int = 7
    output_threshold: int = 2


class TinySNNClassifier:
    """Hand-coded tiny integrate-and-fire network.

    This is intentionally simple and deterministic. It is a candidate baseline,
    not a trained SNN.

    Hidden neurons:
        h0 responds to channel 0
        h1 responds to channel 1
        h2 responds to channel 2
        h3 responds to weak combined activity

    Classification:
        output is positive when enough hidden spikes occur in a plausible order.
    """

    def __init__(self, config: TinySNNConfig | None = None):
        self.config = config or TinySNNConfig()
        self.weights = np.array(
            [
                [2, -1, 0, 0],
                [-1, 2, 0, 0],
                [0, -1, 2, 0],
                [1, 1, 1, -1],
            ],
            dtype=np.int16,
        )

    def predict_one(self, seq: np.ndarray) -> int:
        cfg = self.config
        mem = np.zeros(self.weights.shape[0], dtype=np.int16)
        spikes_seen = np.zeros(self.weights.shape[0], dtype=np.uint8)
        ordered_progress = 0
        last_progress_cycle = -1

        for cycle, row in enumerate(seq.astype(np.int16)):
            if row.sum() == 0:
                mem = np.maximum(cfg.membrane_min, mem - cfg.leak)
                continue

            drive = self.weights @ row
            mem = np.clip(mem + drive, cfg.membrane_min, cfg.membrane_max)
            spikes = mem >= cfg.threshold
            mem[spikes] = 0
            spikes_seen |= spikes.astype(np.uint8)

            # Tiny order-sensitive output: h0 -> h1 -> h2.
            if ordered_progress < 3 and spikes[ordered_progress]:
                if last_progress_cycle < 0 or cycle - last_progress_cycle <= 6:
                    ordered_progress += 1
                    last_progress_cycle = cycle
                else:
                    ordered_progress = 1 if spikes[0] else 0
                    last_progress_cycle = cycle if spikes[0] else -1

            if ordered_progress >= cfg.output_threshold and int(spikes_seen[:3].sum()) >= cfg.output_threshold:
                if ordered_progress == 3:
                    return 1

        return int(ordered_progress == 3)

    def active_ops_one(self, seq: np.ndarray) -> int:
        # Proxy: update cost only on active cycles plus leak cost on idle cycles.
        active_cycles = int(np.count_nonzero(seq.sum(axis=1)))
        idle_cycles = int(seq.shape[0] - active_cycles)
        synaptic_ops = int(seq.sum() * self.weights.shape[0])
        leak_ops = idle_cycles
        return synaptic_ops + leak_ops
