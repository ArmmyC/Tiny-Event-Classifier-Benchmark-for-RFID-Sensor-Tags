from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from tinysnnrfid.classifiers.tiny_snn_v2 import (
    DEFAULT_INPUT_WEIGHTS,
    DEFAULT_OUTPUT_WEIGHTS,
    TinySNNV2Classifier,
)


ROOT = Path(__file__).resolve().parents[1]
INPUT_WEIGHTS = np.asarray(DEFAULT_INPUT_WEIGHTS, dtype=np.int16)
OUTPUT_WEIGHTS = np.asarray(DEFAULT_OUTPUT_WEIGHTS, dtype=np.int16)


def clip(value: int) -> int:
    return max(0, min(7, int(value)))


def rtl_arithmetic_model(sequence: np.ndarray) -> tuple[int, list[list[int]]]:
    hidden = np.zeros(6, dtype=np.int16)
    output = 0
    hidden_spike_history: list[list[int]] = []
    latched_prediction = 0
    for row in sequence.astype(np.int16, copy=False):
        hidden = np.maximum(0, hidden - 1)
        output = max(0, output - 1)
        hidden = np.clip(hidden + row @ INPUT_WEIGHTS, 0, 7)
        spikes = hidden >= 4
        hidden_spike_history.append([int(value) for value in spikes])
        if np.any(spikes):
            hidden[spikes] = 0
            output = clip(output + int(spikes.astype(np.int16) @ OUTPUT_WEIGHTS))
            if output >= 3:
                latched_prediction = 1
    return latched_prediction, hidden_spike_history


def wrong_leak_order_model(sequence: np.ndarray) -> tuple[int, list[list[int]]]:
    hidden = np.zeros(6, dtype=np.int16)
    output = 0
    hidden_spike_history: list[list[int]] = []
    latched_prediction = 0
    for row in sequence.astype(np.int16, copy=False):
        hidden = np.clip(hidden - 1 + row @ INPUT_WEIGHTS, 0, 7)
        spikes = hidden >= 4
        hidden_spike_history.append([int(value) for value in spikes])
        if np.any(spikes):
            hidden[spikes] = 0
            output = clip(output - 1 + int(spikes.astype(np.int16) @ OUTPUT_WEIGHTS))
            if output >= 3:
                latched_prediction = 1
    return latched_prediction, hidden_spike_history


def row(*channels: int) -> np.ndarray:
    values = np.zeros(4, dtype=np.uint8)
    for channel in channels:
        values[channel] = 1
    return values


def sequence(*rows: np.ndarray) -> np.ndarray:
    return np.stack(rows).astype(np.uint8)


@pytest.mark.parametrize(
    "case",
    [
        np.zeros((4, 4), dtype=np.uint8),
        sequence(row(2)),
        sequence(row(), row(), row(0), row(), row(1), row(), row(2)),
        sequence(row(0), row(1), row(2)),
        sequence(row(3), row(3), row(0), row(1), row(2)),
    ],
)
def test_rtl_arithmetic_model_matches_python_default_prediction(case: np.ndarray) -> None:
    model = TinySNNV2Classifier()
    rtl_prediction, _ = rtl_arithmetic_model(case)
    assert rtl_prediction == model.predict_one(case)


def test_single_threshold_drive_spikes_after_leak_clip() -> None:
    case = sequence(row(2))
    prediction, spikes = rtl_arithmetic_model(case)
    wrong_prediction, wrong_spikes = wrong_leak_order_model(case)
    assert prediction == TinySNNV2Classifier().predict_one(case)
    assert spikes[0][2] == 1
    assert wrong_prediction == prediction
    assert wrong_spikes[0][2] == 0


def test_prediction_edge_case_fails_with_wrong_leak_order() -> None:
    case = sequence(row(1, 2))
    prediction, spikes = rtl_arithmetic_model(case)
    wrong_prediction, wrong_spikes = wrong_leak_order_model(case)
    assert prediction == TinySNNV2Classifier().predict_one(case) == 1
    assert spikes[0][2] == 1
    assert spikes[0][5] == 1
    assert wrong_spikes[0][2] == 0
    assert wrong_prediction == 0


def test_rtl_source_clips_after_leak_before_adding_drive() -> None:
    source = (ROOT / "rtl" / "snn" / "tiny_snn_v2_detector.sv").read_text(encoding="utf-8")
    hidden_leak = "hidden_value = clip_membrane(hidden_membrane[neuron] - LEAK);"
    hidden_drive = "hidden_value = clip_membrane(hidden_value + drive);"
    output_leak = "output_value = clip_membrane(output_membrane - LEAK);"
    output_drive = "next_output_membrane = clip_membrane(output_value + drive);"
    assert hidden_leak in source
    assert hidden_drive in source
    assert source.index(hidden_leak) < source.index(hidden_drive)
    assert output_leak in source
    assert output_drive in source
    assert source.index(output_leak) < source.index(output_drive)
