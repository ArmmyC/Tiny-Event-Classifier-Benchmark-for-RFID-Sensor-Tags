from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from .base import Classifier


DEFAULT_INPUT_WEIGHTS: tuple[tuple[int, ...], ...] = (
    (4, 0, 0, -1, 3, 0),
    (0, 3, 0, -1, 3, 3),
    (0, 0, 4, -1, 0, 3),
    (-1, -1, -1, 7, -2, -2),
)
DEFAULT_OUTPUT_WEIGHTS: tuple[int, ...] = (-2, 0, 1, -3, 2, 2)


@dataclass(frozen=True)
class TinySNNV2Trace:
    prediction: int
    input_spike_processing: int
    hidden_updates: int
    output_updates: int
    hidden_spikes: int
    output_spikes: int

    @property
    def operations(self) -> int:
        return (
            self.input_spike_processing
            + self.hidden_updates
            + self.output_updates
            + self.hidden_spikes
            + self.output_spikes
        )


class TinySNNV2Classifier(Classifier):
    """Small hidden-layer integer IF/LIF classifier with fixed weights.

    Hidden neurons are hand-designed rather than trained:
    h0/h2 detect channels 0 and 2, h4/h5 act as short temporal-memory
    detectors for nearby 0->1 and 1->2 pairs, and h3 inhibits dense/noisy
    activity. The model intentionally has no direct FSM progress counter.
    """

    name = "tiny_snn_v2"

    def __init__(
        self,
        hidden_neurons: int = 6,
        hidden_threshold: int = 4,
        output_threshold: int = 3,
        leak: int = 1,
        membrane_min: int = 0,
        membrane_max: int = 7,
        reset_on_spike: bool = True,
        input_weights: list[list[int]] | tuple[tuple[int, ...], ...] = DEFAULT_INPUT_WEIGHTS,
        output_weights: list[int] | tuple[int, ...] = DEFAULT_OUTPUT_WEIGHTS,
    ):
        self.hidden_neurons = hidden_neurons
        self.hidden_threshold = hidden_threshold
        self.output_threshold = output_threshold
        self.leak = leak
        self.membrane_min = membrane_min
        self.membrane_max = membrane_max
        self.reset_on_spike = reset_on_spike
        self.input_weights = _as_integer_matrix(input_weights, "input_weights")
        self.output_weights = _as_integer_vector(output_weights, "output_weights")
        self._validate()

    def _validate(self) -> None:
        for field in ("hidden_neurons", "hidden_threshold", "output_threshold"):
            value = getattr(self, field)
            if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
                raise ValueError(f"{field} must be a positive integer")
        if not isinstance(self.leak, int) or isinstance(self.leak, bool) or self.leak < 0:
            raise ValueError("leak must be a non-negative integer")
        if (
            not isinstance(self.membrane_min, int)
            or isinstance(self.membrane_min, bool)
            or not isinstance(self.membrane_max, int)
            or isinstance(self.membrane_max, bool)
            or self.membrane_min >= self.membrane_max
        ):
            raise ValueError("membrane_min and membrane_max must be integers with membrane_min < membrane_max")
        if not isinstance(self.reset_on_spike, bool):
            raise ValueError("reset_on_spike must be a boolean")
        if self.input_weights.ndim != 2 or self.input_weights.shape[1] != self.hidden_neurons:
            raise ValueError(
                "input_weights must have shape [input_width, hidden_neurons]; "
                f"got {self.input_weights.shape} for hidden_neurons={self.hidden_neurons}"
            )
        if self.output_weights.shape != (self.hidden_neurons,):
            raise ValueError(
                f"output_weights must have length {self.hidden_neurons}; got {self.output_weights.shape}"
            )

    def predict_one(self, sequence: np.ndarray) -> int:
        return self._run_sequence(sequence).prediction

    def _run_sequence(self, sequence: np.ndarray) -> TinySNNV2Trace:
        if sequence.ndim != 2:
            raise ValueError(f"sequence must have shape [cycles, channels], got {sequence.shape}")
        if sequence.shape[1] != self.input_weights.shape[0]:
            raise ValueError(
                f"input width {sequence.shape[1]} does not match input_weights width {self.input_weights.shape[0]}"
            )

        hidden_membrane = np.zeros(self.hidden_neurons, dtype=np.int16)
        output_membrane = 0
        input_spike_processing = 0
        hidden_updates = 0
        output_updates = 0
        hidden_spike_count = 0

        for row in sequence.astype(np.int16, copy=False):
            has_input = bool(np.any(row))
            if self.leak:
                hidden_membrane = np.maximum(self.membrane_min, hidden_membrane - self.leak)
                output_membrane = max(self.membrane_min, output_membrane - self.leak)
                hidden_updates += self.hidden_neurons
                output_updates += 1
            elif not has_input:
                continue

            if has_input:
                input_spike_processing += int(row.sum())
                hidden_membrane = hidden_membrane + row @ self.input_weights
                hidden_membrane = np.clip(hidden_membrane, self.membrane_min, self.membrane_max)
                hidden_updates += self.hidden_neurons

            hidden_spikes = hidden_membrane >= self.hidden_threshold
            if np.any(hidden_spikes):
                hidden_spike_total = int(hidden_spikes.sum())
                hidden_spike_count += hidden_spike_total
                if self.reset_on_spike:
                    hidden_membrane[hidden_spikes] = self.membrane_min
                output_drive = int(hidden_spikes.astype(np.int16) @ self.output_weights)
                output_membrane = int(np.clip(output_membrane + output_drive, self.membrane_min, self.membrane_max))
                output_updates += self.hidden_neurons
                if output_membrane >= self.output_threshold:
                    return TinySNNV2Trace(
                        prediction=1,
                        input_spike_processing=input_spike_processing,
                        hidden_updates=hidden_updates,
                        output_updates=output_updates,
                        hidden_spikes=hidden_spike_count,
                        output_spikes=1,
                    )

        return TinySNNV2Trace(
            prediction=0,
            input_spike_processing=input_spike_processing,
            hidden_updates=hidden_updates,
            output_updates=output_updates,
            hidden_spikes=hidden_spike_count,
            output_spikes=0,
        )

    def active_ops_one(self, sequence: np.ndarray) -> int:
        return self._run_sequence(sequence).operations

    def activity_proxy(self, inputs: np.ndarray) -> dict[str, int | float]:
        """Return software proxy counts, not hardware power or energy."""
        traces = [self._run_sequence(sequence) for sequence in inputs]
        operations = np.asarray([trace.operations for trace in traces], dtype=np.int64)
        return {
            "software_proxy_total_operations": int(operations.sum()),
            "software_proxy_mean_operations": float(operations.mean()) if operations.size else 0.0,
            "software_proxy_max_operations": int(operations.max()) if operations.size else 0,
            "input_spike_processing": int(sum(trace.input_spike_processing for trace in traces)),
            "hidden_updates": int(sum(trace.hidden_updates for trace in traces)),
            "output_updates": int(sum(trace.output_updates for trace in traces)),
            "hidden_spikes": int(sum(trace.hidden_spikes for trace in traces)),
            "output_spikes": int(sum(trace.output_spikes for trace in traces)),
        }


def _as_integer_matrix(values: Any, field: str) -> np.ndarray:
    array = np.asarray(values)
    if not np.issubdtype(array.dtype, np.integer):
        raise ValueError(f"{field} must contain only integers")
    return array.astype(np.int16)


def _as_integer_vector(values: Any, field: str) -> np.ndarray:
    array = np.asarray(values)
    if not np.issubdtype(array.dtype, np.integer):
        raise ValueError(f"{field} must contain only integers")
    return array.astype(np.int16)
