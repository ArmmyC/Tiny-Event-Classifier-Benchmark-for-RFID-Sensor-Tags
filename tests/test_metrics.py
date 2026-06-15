import numpy as np

from tinysnnrfid.metrics import binary_metrics


def test_binary_metrics_and_confusion_matrix() -> None:
    metrics = binary_metrics(np.array([1, 1, 0, 0]), np.array([1, 0, 1, 0]))
    assert metrics["accuracy"] == 0.5
    assert metrics["precision"] == 0.5
    assert metrics["recall"] == 0.5
    assert metrics["f1"] == 0.5
    assert metrics["confusion_matrix"] == [[1, 1], [1, 1]]


def test_zero_division_metrics() -> None:
    metrics = binary_metrics(np.zeros(3, dtype=np.uint8), np.zeros(3, dtype=np.uint8))
    assert metrics["precision"] == 0.0
    assert metrics["recall"] == 0.0
    assert metrics["f1"] == 0.0
