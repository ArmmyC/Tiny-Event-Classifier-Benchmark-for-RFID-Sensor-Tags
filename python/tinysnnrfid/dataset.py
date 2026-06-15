from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

import numpy as np


LEGACY_SCENARIO_TAGS = (
    "clean_positive",
    "jittered_positive",
    "dropped_positive",
    "noise_negative",
    "accidental_pattern_negative",
    "dense_noise_negative",
)

TEMPORAL_HARD_SCENARIO_TAGS = (
    "clean_positive",
    "long_gap_positive",
    "distractor_positive",
    "dropout_positive",
    "reversed_negative",
    "partial_order_negative",
    "burst_noise_negative",
    "near_miss_negative",
)

SCENARIO_TAGS = tuple(dict.fromkeys((*LEGACY_SCENARIO_TAGS, *TEMPORAL_HARD_SCENARIO_TAGS)))

POSITIVE_TEMPORAL_TAGS = {
    "clean_positive",
    "long_gap_positive",
    "distractor_positive",
    "dropout_positive",
}

DEFAULT_TEMPORAL_HARD_MIX = {
    "clean_positive": 0.15,
    "long_gap_positive": 0.10,
    "distractor_positive": 0.10,
    "dropout_positive": 0.10,
    "reversed_negative": 0.15,
    "partial_order_negative": 0.15,
    "burst_noise_negative": 0.15,
    "near_miss_negative": 0.10,
}


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
    dense_noise_spike_threshold: int = 8
    scenario_suite_mode: str = "legacy"
    scenario_mix: dict[str, float] | None = None
    max_long_gap: int = 10
    burst_length: int = 4
    distractor_count: int = 2
    allow_legacy_tags: bool = True

    @classmethod
    def from_mapping(
        cls,
        values: dict[str, Any],
        scenario: dict[str, Any] | None = None,
        scenario_suite: dict[str, Any] | None = None,
    ) -> "DatasetConfig":
        scenario = scenario or {}
        scenario_suite = scenario_suite or {}
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
            dense_noise_spike_threshold=int(scenario.get("dense_noise_spike_threshold", 8)),
            scenario_suite_mode=str(scenario_suite.get("mode", "legacy")),
            scenario_mix=(
                {str(key): float(value) for key, value in scenario_suite.get("mix", {}).items()}
                if scenario_suite.get("mix") is not None
                else None
            ),
            max_long_gap=int(scenario_suite.get("max_long_gap", 10)),
            burst_length=int(scenario_suite.get("burst_length", 4)),
            distractor_count=int(scenario_suite.get("distractor_count", 2)),
            allow_legacy_tags=scenario_suite.get("allow_legacy_tags", True),
        )


def contains_ordered_pattern(
    sequence: np.ndarray, pattern: tuple[int, ...], max_gap: int | None = None
) -> bool:
    """Return whether a binary sequence contains the channel pattern in order."""
    if sequence.ndim != 2:
        raise ValueError(f"sequence must have shape [cycles, channels], got {sequence.shape}")
    if not pattern:
        return False
    if min(pattern) < 0 or max(pattern) >= sequence.shape[1]:
        raise ValueError("pattern contains a channel outside the sequence input width")
    if max_gap is not None and max_gap < 0:
        raise ValueError("max_gap must be non-negative or None")

    progress = 0
    last_match = -1
    for cycle, row in enumerate(sequence):
        if progress and max_gap is not None and cycle - last_match > max_gap:
            progress = 0
            last_match = -1
        if row[pattern[progress]]:
            progress += 1
            last_match = cycle
            if progress == len(pattern):
                return True
    return False


def _insert_motif(
    seq: np.ndarray, rng: np.random.Generator, config: DatasetConfig
) -> tuple[bool, bool]:
    """Insert a motif and return (event_dropped, event_jittered)."""
    gaps = [int(rng.integers(1, config.max_gap + 2)) for _ in config.motif[1:]]
    offsets = np.cumsum([0, *gaps])
    max_start = max(0, config.seq_len - int(offsets[-1]) - 1)
    start = int(rng.integers(0, max_start + 1))
    previous = -1
    event_dropped = False
    event_jittered = False
    for channel, offset in zip(config.motif, offsets):
        if rng.random() < config.dropout_prob:
            event_dropped = True
            continue
        cycle = start + int(offset)
        if config.max_jitter and rng.random() < config.jitter_prob:
            jitter = int(rng.integers(-config.max_jitter, config.max_jitter + 1))
            cycle += jitter
            event_jittered |= jitter != 0
        cycle = min(config.seq_len - 1, max(previous + 1, cycle))
        if cycle < config.seq_len:
            seq[cycle, channel] = 1
            previous = cycle
    return event_dropped, event_jittered


def generate_noisy_event_dataset_with_scenarios(
    config: DatasetConfig,
) -> tuple[np.ndarray, np.ndarray, list[str]]:
    """Generate binary event data, labels, and diagnostic scenario tags."""
    _validate_dataset_config(config)
    if config.scenario_suite_mode == "temporal_hard":
        return generate_temporal_hard_dataset(config)
    rng = np.random.default_rng(config.seed)
    inputs = (
        rng.random((config.num_sequences, config.seq_len, config.input_width)) < config.noise_prob
    ).astype(np.uint8)
    positive_count = int(round(config.num_sequences * config.positive_ratio))
    labels = np.zeros(config.num_sequences, dtype=np.uint8)
    labels[:positive_count] = 1
    rng.shuffle(labels)
    scenario_tags: list[str] = []
    for index, label in enumerate(labels):
        if label:
            dropped, jittered = _insert_motif(inputs[index], rng, config)
            if dropped:
                scenario_tags.append("dropped_positive")
            elif jittered:
                scenario_tags.append("jittered_positive")
            else:
                scenario_tags.append("clean_positive")
        elif int(inputs[index].sum()) >= config.dense_noise_spike_threshold:
            scenario_tags.append("dense_noise_negative")
        elif contains_ordered_pattern(inputs[index], config.motif, config.max_gap + 1):
            scenario_tags.append("accidental_pattern_negative")
        else:
            scenario_tags.append("noise_negative")
    return inputs, labels, scenario_tags


def generate_temporal_hard_dataset(config: DatasetConfig) -> tuple[np.ndarray, np.ndarray, list[str]]:
    """Generate labels and temporal-hard scenario tags from the same sampled scenario."""
    rng = np.random.default_rng(config.seed)
    mix = _normalized_temporal_mix(config)
    scenario_tags = _sample_scenario_tags(rng, config.num_sequences, mix)
    inputs = np.zeros((config.num_sequences, config.seq_len, config.input_width), dtype=np.uint8)
    labels = np.zeros(config.num_sequences, dtype=np.uint8)
    for index, tag in enumerate(scenario_tags):
        labels[index] = 1 if tag in POSITIVE_TEMPORAL_TAGS else 0
        _build_temporal_sequence(inputs[index], tag, rng, config)
    return inputs, labels, scenario_tags


def _normalized_temporal_mix(config: DatasetConfig) -> dict[str, float]:
    mix = config.scenario_mix or DEFAULT_TEMPORAL_HARD_MIX
    total = sum(float(value) for value in mix.values())
    return {tag: float(weight) / total for tag, weight in mix.items() if weight > 0.0}


def _sample_scenario_tags(
    rng: np.random.Generator,
    count: int,
    mix: dict[str, float],
) -> list[str]:
    tags = list(mix)
    raw_counts = {tag: int(np.floor(count * mix[tag])) for tag in tags}
    remainder = count - sum(raw_counts.values())
    fractions = sorted(
        ((count * mix[tag] - raw_counts[tag], tag) for tag in tags),
        key=lambda item: (-item[0], item[1]),
    )
    for _fraction, tag in fractions[:remainder]:
        raw_counts[tag] += 1
    scenario_tags = [tag for tag in tags for _ in range(raw_counts[tag])]
    rng.shuffle(scenario_tags)
    return scenario_tags


def _build_temporal_sequence(
    seq: np.ndarray,
    tag: str,
    rng: np.random.Generator,
    config: DatasetConfig,
) -> None:
    if tag == "clean_positive":
        _place_pattern(seq, config.motif, _motif_positions(config, gap=2))
    elif tag == "long_gap_positive":
        gap = max(config.max_gap + 2, min(config.max_long_gap, max(2, config.seq_len // 4)))
        _place_pattern(seq, config.motif, _motif_positions(config, gap=gap))
    elif tag == "distractor_positive":
        _place_pattern(seq, config.motif, _motif_positions(config, gap=3))
        _add_distractors(seq, rng, config, count=config.distractor_count)
    elif tag == "dropout_positive":
        positions = _motif_positions(config, gap=3)
        drop_index = len(config.motif) // 2
        for index, (cycle, channel) in enumerate(zip(positions, config.motif)):
            if index != drop_index:
                seq[cycle, channel] = 1
        _add_distractors(seq, rng, config, count=1)
    elif tag == "reversed_negative":
        _place_pattern(seq, tuple(reversed(config.motif)), _motif_positions(config, gap=2))
    elif tag == "partial_order_negative":
        positions = _motif_positions(config, gap=3)
        seq[positions[0], config.motif[0]] = 1
        seq[positions[-1], config.motif[-1]] = 1
    elif tag == "burst_noise_negative":
        _add_burst_noise(seq, rng, config)
    elif tag == "near_miss_negative":
        positions = _motif_positions(config, gap=max(config.max_gap + 2, config.max_long_gap))
        _place_pattern(seq, config.motif, positions)
    else:
        raise ValueError(f"Unsupported temporal hard scenario tag: {tag}")


def _motif_positions(config: DatasetConfig, gap: int) -> list[int]:
    span = gap * (len(config.motif) - 1)
    max_start = max(0, config.seq_len - span - 1)
    start = min(max(1, config.seq_len // 6), max_start)
    return [min(config.seq_len - 1, start + gap * index) for index in range(len(config.motif))]


def _place_pattern(seq: np.ndarray, pattern: tuple[int, ...], positions: list[int]) -> None:
    for cycle, channel in zip(positions, pattern):
        seq[cycle, channel] = 1


def _add_distractors(
    seq: np.ndarray,
    rng: np.random.Generator,
    config: DatasetConfig,
    count: int,
) -> None:
    for _ in range(count):
        cycle = int(rng.integers(0, config.seq_len))
        channel = int(rng.integers(0, config.input_width))
        seq[cycle, channel] = 1


def _add_burst_noise(seq: np.ndarray, rng: np.random.Generator, config: DatasetConfig) -> None:
    safe_channels = [channel for channel in range(config.input_width) if channel != config.motif[1]]
    if not safe_channels:
        safe_channels = list(range(config.input_width))
    max_start = max(0, config.seq_len - config.burst_length)
    start = int(rng.integers(0, max_start + 1))
    for offset in range(config.burst_length):
        cycle = start + offset
        for channel in safe_channels:
            if (offset + channel) % 2 == 0:
                seq[cycle, channel] = 1


def _validate_dataset_config(config: DatasetConfig) -> None:
    """Validate the direct dataclass API used by tests and compatibility scripts."""
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
    if config.dense_noise_spike_threshold < 0:
        raise ValueError("dense_noise_spike_threshold must be non-negative")
    if config.scenario_suite_mode not in {"legacy", "temporal_hard"}:
        raise ValueError("scenario_suite mode must be legacy or temporal_hard")
    if config.scenario_suite_mode == "temporal_hard":
        mix = config.scenario_mix or DEFAULT_TEMPORAL_HARD_MIX
        unknown = sorted(set(mix) - set(TEMPORAL_HARD_SCENARIO_TAGS))
        if unknown:
            raise ValueError(f"Unknown temporal hard scenario tag(s): {', '.join(unknown)}")
        if not mix or any(value < 0 for value in mix.values()) or sum(mix.values()) <= 0:
            raise ValueError("temporal_hard scenario mix weights must be non-negative with sum > 0")
        if config.max_long_gap < 0:
            raise ValueError("max_long_gap must be non-negative")
        if config.burst_length <= 0:
            raise ValueError("burst_length must be positive")
        if config.distractor_count < 0:
            raise ValueError("distractor_count must be non-negative")
    if not isinstance(config.allow_legacy_tags, bool):
        raise ValueError("allow_legacy_tags must be a boolean")


def generate_noisy_event_dataset(config: DatasetConfig) -> tuple[np.ndarray, np.ndarray]:
    """Generate inputs shaped [samples, cycles, channels] and binary labels."""
    inputs, labels, _ = generate_noisy_event_dataset_with_scenarios(config)
    return inputs, labels


def save_dataset(out_dir: Path, config: DatasetConfig, effective_config: dict[str, Any] | None = None) -> Path:
    """Generate and save NumPy arrays, metadata, and RTL-friendly vectors."""
    out_dir.mkdir(parents=True, exist_ok=True)
    inputs, labels, scenario_tags = generate_noisy_event_dataset_with_scenarios(config)
    np.save(out_dir / "inputs.npy", inputs)
    np.save(out_dir / "labels.npy", labels)
    legacy_path = out_dir / "noisy_event_dataset.npz"
    np.savez_compressed(legacy_path, x=inputs, y=labels, config=json.dumps(asdict(config)))
    write_vector_text(out_dir / "test_vectors.txt", inputs, labels)
    write_vector_hex(out_dir / "vectors.hex", inputs, labels)
    (out_dir / "scenario_tags.json").write_text(
        json.dumps(scenario_tags, indent=2), encoding="utf-8"
    )
    scenario_counts = {scenario: scenario_tags.count(scenario) for scenario in SCENARIO_TAGS}
    scenario_counts = {scenario: count for scenario, count in scenario_counts.items() if count or scenario in set(scenario_tags)}
    scenario_suite = {
        "mode": config.scenario_suite_mode,
        "mix": config.scenario_mix or (DEFAULT_TEMPORAL_HARD_MIX if config.scenario_suite_mode == "temporal_hard" else {}),
        "effective_counts": scenario_counts,
    }
    metadata = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "seed": config.seed,
        "num_samples": config.num_sequences,
        "sequence_length": config.seq_len,
        "input_width": config.input_width,
        "input_shape": list(inputs.shape),
        "label_counts": {"0": int(np.sum(labels == 0)), "1": int(np.sum(labels == 1))},
        "scenario_counts": scenario_counts,
        "scenario_suite": scenario_suite,
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


def load_generated_dataset(
    data_dir: str | Path,
) -> tuple[np.ndarray, np.ndarray, dict[str, Any], list[str]]:
    """Load and validate generated dataset artifacts from a directory."""
    directory = Path(data_dir)
    required = [
        directory / "inputs.npy",
        directory / "labels.npy",
        directory / "metadata.json",
        directory / "scenario_tags.json",
    ]
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise ValueError(f"Missing dataset file(s): {', '.join(missing)}. Run dataset generation first.")
    inputs = np.load(required[0], allow_pickle=False)
    labels = np.load(required[1], allow_pickle=False)
    metadata = json.loads(required[2].read_text(encoding="utf-8"))
    scenario_tags = json.loads(required[3].read_text(encoding="utf-8"))
    if inputs.ndim != 3:
        raise ValueError(f"Dataset shape mismatch in {required[0]}: expected 3 dimensions, got {inputs.shape}")
    if labels.shape != (inputs.shape[0],):
        raise ValueError(f"Inconsistent labels and sample counts: {labels.shape} versus {inputs.shape[0]}")
    expected = tuple(metadata.get("input_shape", inputs.shape))
    if inputs.shape != expected:
        raise ValueError(f"Dataset shape mismatch with {required[2]}: {inputs.shape} versus {expected}")
    if not np.isin(inputs, [0, 1]).all() or not np.isin(labels, [0, 1]).all():
        raise ValueError(f"Dataset values must be binary in {directory}")
    if not isinstance(scenario_tags, list) or len(scenario_tags) != inputs.shape[0]:
        raise ValueError(
            f"Scenario tag count mismatch in {required[3]}: expected {inputs.shape[0]}"
        )
    if any(not isinstance(tag, str) for tag in scenario_tags):
        raise ValueError(f"Scenario tags must be strings in {required[3]}")
    unknown_tags = sorted(set(scenario_tags) - set(SCENARIO_TAGS))
    if unknown_tags:
        raise ValueError(f"Unknown scenario tag(s) in {required[3]}: {', '.join(unknown_tags)}")
    actual_counts = {scenario: scenario_tags.count(scenario) for scenario in SCENARIO_TAGS if scenario_tags.count(scenario)}
    if metadata.get("scenario_counts") != actual_counts:
        raise ValueError(
            f"Scenario counts in {required[2]} do not match tags in {required[3]}"
        )
    return inputs.astype(np.uint8), labels.astype(np.uint8), metadata, scenario_tags


def load_dataset(path: str | Path) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
    data = np.load(path, allow_pickle=False)
    return data["x"].astype(np.uint8), data["y"].astype(np.uint8), json.loads(str(data["config"]))
