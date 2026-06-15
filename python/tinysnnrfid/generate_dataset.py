from __future__ import annotations

import argparse
from pathlib import Path
import sys

from .config import load_config
from .dataset import DatasetConfig, save_dataset


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate a synthetic sparse RFID event dataset.")
    parser.add_argument("--config", type=Path, default=Path("configs/default.json"))
    parser.add_argument("--output-dir", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        config = load_config(args.config)
        print(f"Dataset configuration loaded: {args.config}")
        output_dir = args.output_dir or Path(config["paths"]["data_dir"])
        save_dataset(
            output_dir,
            DatasetConfig.from_mapping(config["dataset"], config["scenario"], config.get("scenario_suite")),
            config,
        )
        print(f"Dataset generated: {output_dir}")
        return 0
    except (ValueError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
