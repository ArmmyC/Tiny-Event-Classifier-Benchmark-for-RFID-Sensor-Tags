"""Backward-compatible tiny SNN imports."""

from dataclasses import dataclass

from .classifiers import TinySNNClassifier as _TinySNNClassifier


@dataclass
class TinySNNConfig:
    threshold: int = 2
    leak: int = 1
    membrane_min: int = 0
    membrane_max: int = 7
    output_threshold: int = 2


class TinySNNClassifier(_TinySNNClassifier):
    def __init__(self, config: TinySNNConfig | None = None):
        cfg = config or TinySNNConfig()
        super().__init__(threshold=cfg.threshold, leak=cfg.leak, membrane_max=cfg.membrane_max)
