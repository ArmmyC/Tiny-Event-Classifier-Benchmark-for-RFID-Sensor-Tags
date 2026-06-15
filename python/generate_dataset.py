from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from tinysnnrfid.dataset import DatasetConfig, save_dataset


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate noisy event detector dataset.")
    parser.add_argument("--num-sequences", type=int, default=1000)
    parser.add_argument("--seq-len", type=int, default=32)
    parser.add_argument("--input-width", type=int, default=4)
    parser.add_argument("--positive-ratio", type=float, default=0.5)
    parser.add_argument("--noise-prob", type=float, default=0.03)
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--max-gap", type=int, default=5)
    parser.add_argument("--out-dir", type=Path, default=Path("data/generated"))
    args = parser.parse_args()

    config = DatasetConfig(
        num_sequences=args.num_sequences,
        seq_len=args.seq_len,
        input_width=args.input_width,
        positive_ratio=args.positive_ratio,
        noise_prob=args.noise_prob,
        seed=args.seed,
        max_gap=args.max_gap,
    )
    path = save_dataset(args.out_dir, config)
    print(f"Wrote {path}")


if __name__ == "__main__":
    main()
