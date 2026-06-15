from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

import numpy as np


@dataclass(frozen=True)
class DatasetConfig:
    """Configuration for deterministic sparse event-sequence generation."""

    num_sequences: int = 1000
    seq_len: int = 32
    input_width: int = 4
    positive_ratio: float = 0.5
    noise_prob: float = 0.03
    seed: int = 1234
    motif: tuple[int, ...] = (0, 1, 2)
    max_gap: int = 5
    jitter_prob: float = 0.2
    dropout_prob: float = 0.1
    max_jitter: int = 1

    @classmethod
    def from_mapping(cls, values: dict[str, Any]) -> "DatasetConfig":
        return cls(
            num_sequences=int(values["num_samples"]),
            seq_len=int(values["sequence_length"]),
            input_width=int(values["input_width"]),
            positive_ratio=float(values["positive_ratio"]),
            noise_prob=float(values["noise_probability"]),
            seed=int(values["random_seed"]),
            motif=tuple(int(value) for value in values["valid_pattern"]),
            max_gap=int(values["max_gap"]),
            jitter_prob=float(values["jitter_probability"]),
            dropout_prob=float(values["dropout_probability"]),
            max_jitter=int(values["max_jitter"]),
        )


def _insert_motif(seq: np.ndarray, rng: np.random.Generator, config: DatasetConfig) -> None:
    gaps = [int(rng.integers(1, config.max_gap + 2)) for _ in config.motif[1:]]
    offsets = np.cumsum([0, *gaps])
    max_start = max(0, config.seq_len - int(offsets[-1]) - 1)
    start = int(rng.integers(0, max_start + 1))
    previous = -1
    for channel, offset in zip(config.motif, offsets):
        if rng.random() < config.dropout_prob:
            continue
        cycle = start + int(offset)
        if config.max_jitter and rng.random() < config.jitter_prob:
            cycle += int(rng.integers(-config.max_jitter, config.max_jitter + 1))
        cycle = min(config.seq_len - 1, max(previous + 1, cycle))
        if cycle < config.seq_len:
            seq[cycle, channel] = 1
            previous = cycle


def generate_noisy_event_dataset(config: DatasetConfig) -> tuple[np.ndarray, np.ndarray]:
    """Generate inputs shaped [samples, cycles, channels] and binary labels."""
    if config.num_sequences <= 0 or config.seq_len <= 0 or config.input_width <= 0:
        raise ValueError("Dataset dimensions must be greater than 0")
    for name, value in (
        ("positive_ratio", config.positive_ratio),
        ("noise_prob", config.noise_prob),
        ("jitter_prob", config.jitter_prob),
        ("dropout_prob", config.dropout_prob),
    ):
        if not 0.0 <= value <= 1.0:
            raise ValueError(f"{name} must be in [0, 1]")
    if not config.motif or min(config.motif) < 0 or max(config.motif) >= config.input_width:
        raise ValueError("input_width is too small for motif channels")

    rng = np.random.default_rng(config.seed)
    inputs = (rng.random((config.num_sequences, config.seq_len, config.input_width)) < config.noise_prob).astype(np.uint8)
    positive_count = int(round(config.num_sequences * config.positive_ratio))
    labels = np.zeros(config.num_sequences, dtype=np.uint8)
    labels[:positive_count] = 1
    rng.shuffle(labels)
    for index in np.flatnonzero(labels):
        _insert_motif(inputs[index], rng, config)
    return inputs, labels


def save_dataset(out_dir: Path, config: DatasetConfig, effective_config: dict[str, Any] | None = None) -> Path:
    """Generate and save NumPy arrays, metadata, and RTL-friendly vectors."""
    out_dir.mkdir(parents=True, exist_ok=True)
    inputs, labels = generate_noisy_event_dataset(config)
    np.save(out_dir / "inputs.npy", inputs)
    np.save(out_dir / "labels.npy", labels)
    legacy_path = out_dir / "noisy_event_dataset.npz"
    np.savez_compressed(legacy_path, x=inputs, y=labels, config=json.dumps(asdict(config)))
    write_vector_text(out_dir / "test_vectors.txt", inputs, labels)
    write_vector_hex(out_dir / "vectors.hex", inputs, labels)
    metadata = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "seed": config.seed,
        "num_samples": config.num_sequences,
        "sequence_length": config.seq_len,
        "input_width": config.input_width,
        "input_shape": list(inputs.shape),
        "label_counts": {"0": int(np.sum(labels == 0)), "1": int(np.sum(labels == 1))},
        "valid_pattern": list(config.motif),
        "config": effective_config or asdict(config),
    }
    (out_dir / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return legacy_path


def write_vector_text(path: Path, inputs: np.ndarray, labels: np.ndarray) -> None:
    """Write one sample per line for future RTL testbenches."""
    lines = ["# sample_index label sequence_length input_width"]
    for index, sequence in enumerate(inputs):
        tokens = ["".join(str(int(bit)) for bit in row[::-1]) for row in sequence]
        lines.append(f"{index} {int(labels[index])} {inputs.shape[1]} {inputs.shape[2]} {' '.join(tokens)}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_vector_hex(path: Path, inputs: np.ndarray, labels: np.ndarray) -> None:
    lines: list[str] = []
    digits = max(1, (inputs.shape[2] + 3) // 4)
    for index, sequence in enumerate(inputs):
        values = [sum(int(bit) << bit_index for bit_index, bit in enumerate(row)) for row in sequence]
        lines.append(f"{int(labels[index])} {''.join(f'{value:0{digits}x}' for value in values)}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def load_generated_dataset(data_dir: str | Path) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
    """Load and validate generated dataset artifacts from a directory."""
    directory = Path(data_dir)
    required = [directory / "inputs.npy", directory / "labels.npy", directory / "metadata.json"]
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise ValueError(f"Missing dataset file(s): {', '.join(missing)}. Run dataset generation first.")
    inputs = np.load(required[0], allow_pickle=False)
    labels = np.load(required[1], allow_pickle=False)
    metadata = json.loads(required[2].read_text(encoding="utf-8"))
    if inputs.ndim != 3:
        raise ValueError(f"Dataset shape mismatch in {required[0]}: expected 3 dimensions, got {inputs.shape}")
    if labels.shape != (inputs.shape[0],):
        raise ValueError(f"Inconsistent labels and sample counts: {labels.shape} versus {inputs.shape[0]}")
    expected = tuple(metadata.get("input_shape", inputs.shape))
    if inputs.shape != expected:
        raise ValueError(f"Dataset shape mismatch with {required[2]}: {inputs.shape} versus {expected}")
    if not np.isin(inputs, [0, 1]).all() or not np.isin(labels, [0, 1]).all():
        raise ValueError(f"Dataset values must be binary in {directory}")
    return inputs.astype(np.uint8), labels.astype(np.uint8), metadata


def load_dataset(path: str | Path) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
    data = np.load(path, allow_pickle=False)
    return data["x"].astype(np.uint8), data["y"].astype(np.uint8), json.loads(str(data["config"]))
