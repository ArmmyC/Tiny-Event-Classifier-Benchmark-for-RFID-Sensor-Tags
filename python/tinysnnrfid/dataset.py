from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
import json
import numpy as np


@dataclass(frozen=True)
class DatasetConfig:
    num_sequences: int = 1000
    seq_len: int = 32
    input_width: int = 4
    positive_ratio: float = 0.5
    noise_prob: float = 0.03
    seed: int = 1
    motif: tuple[int, ...] = (0, 1, 2)
    max_gap: int = 5


def _insert_motif(seq: np.ndarray, rng: np.random.Generator, motif: tuple[int, ...], max_gap: int) -> None:
    """Insert an ordered motif into a sequence in-place."""
    seq_len = seq.shape[0]
    total_span = len(motif) + max_gap * (len(motif) - 1)
    start_high = max(1, seq_len - total_span)
    t = int(rng.integers(0, start_high))
    for i, channel in enumerate(motif):
        if i > 0:
            t += int(rng.integers(1, max_gap + 1))
        if t >= seq_len:
            break
        seq[t, channel] = 1


def generate_noisy_event_dataset(config: DatasetConfig) -> tuple[np.ndarray, np.ndarray]:
    """Generate binary event sequences and sequence-level labels.

    Returns:
        x: uint8 array with shape [num_sequences, seq_len, input_width]
        y: uint8 array with shape [num_sequences]
    """
    if not (0.0 <= config.positive_ratio <= 1.0):
        raise ValueError("positive_ratio must be in [0, 1]")
    if not (0.0 <= config.noise_prob <= 1.0):
        raise ValueError("noise_prob must be in [0, 1]")
    if config.input_width < max(config.motif) + 1:
        raise ValueError("input_width is too small for motif channels")

    rng = np.random.default_rng(config.seed)
    x = rng.random((config.num_sequences, config.seq_len, config.input_width)) < config.noise_prob
    x = x.astype(np.uint8)
    y = (rng.random(config.num_sequences) < config.positive_ratio).astype(np.uint8)

    for idx, label in enumerate(y):
        if label:
            _insert_motif(x[idx], rng, config.motif, config.max_gap)

    return x, y


def save_dataset(out_dir: Path, config: DatasetConfig) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    x, y = generate_noisy_event_dataset(config)
    dataset_path = out_dir / "noisy_event_dataset.npz"
    np.savez_compressed(dataset_path, x=x, y=y, config=json.dumps(asdict(config)))

    write_vector_text(out_dir / "test_vectors.txt", x, y)
    write_vector_hex(out_dir / "vectors.hex", x, y)
    (out_dir / "metadata.json").write_text(json.dumps(asdict(config), indent=2), encoding="utf-8")
    return dataset_path


def write_vector_text(path: Path, x: np.ndarray, y: np.ndarray) -> None:
    """Write readable vectors.

    Format per sequence:
        label=<0|1>
        <cycle> <4-bit-binary>
    """
    lines: list[str] = []
    for seq_idx in range(x.shape[0]):
        lines.append(f"# sequence {seq_idx}")
        lines.append(f"label={int(y[seq_idx])}")
        for cycle in range(x.shape[1]):
            bits = "".join(str(int(bit)) for bit in x[seq_idx, cycle][::-1])
            lines.append(f"{cycle:02d} {bits}")
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def write_vector_hex(path: Path, x: np.ndarray, y: np.ndarray) -> None:
    """Write compact vectors for simple scripts.

    Format per sequence:
        <label> <hex_digit_per_cycle_without_spaces>
    """
    lines: list[str] = []
    for seq_idx in range(x.shape[0]):
        hex_digits = []
        for cycle in range(x.shape[1]):
            value = 0
            for bit_idx, bit in enumerate(x[seq_idx, cycle]):
                value |= int(bit) << bit_idx
            hex_digits.append(f"{value:x}")
        lines.append(f"{int(y[seq_idx])} {''.join(hex_digits)}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def load_dataset(path: str | Path) -> tuple[np.ndarray, np.ndarray, dict]:
    data = np.load(path, allow_pickle=False)
    x = data["x"].astype(np.uint8)
    y = data["y"].astype(np.uint8)
    config = json.loads(str(data["config"]))
    return x, y, config
