import numpy as np

from tinysnnrfid.classifiers import FSMClassifier, LUTLikeClassifier, ThresholdClassifier, TinySNNClassifier


def sequences() -> np.ndarray:
    positive = np.zeros((8, 4), dtype=np.uint8)
    positive[1, 0] = 1
    positive[3, 1] = 1
    positive[5, 2] = 1
    negative = np.zeros((8, 4), dtype=np.uint8)
    negative[1, 2] = 1
    negative[3, 1] = 1
    negative[5, 0] = 1
    return np.stack([positive, negative])


def test_classifier_predictions() -> None:
    inputs = sequences()
    assert ThresholdClassifier().predict(inputs).tolist() == [1, 1]
    assert FSMClassifier(max_gap=3).predict(inputs).tolist() == [1, 0]
    assert LUTLikeClassifier().predict(inputs).tolist() == [1, 0]
    assert TinySNNClassifier(max_gap=3).predict(inputs).tolist() == [1, 0]


def test_tiny_snn_reset_allows_ordered_output() -> None:
    inputs = sequences()[:1]
    model = TinySNNClassifier(threshold=2, leak=1, membrane_max=3, max_gap=3)
    assert model.predict(inputs).tolist() == [1]
    assert model.activity_proxy(inputs)["software_proxy_total_operations"] > 0
