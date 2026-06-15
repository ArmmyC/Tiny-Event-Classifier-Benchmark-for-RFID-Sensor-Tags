from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path


def count_vcd_toggles(path: Path) -> dict[str, int]:
    last_value: dict[str, str] = {}
    toggles: dict[str, int] = defaultdict(int)
    in_header = True

    with path.open("r", encoding="utf-8", errors="ignore") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line:
                continue
            if in_header:
                if line == "$enddefinitions $end":
                    in_header = False
                continue
            if line.startswith("#") or line.startswith("$"):
                continue

            if line[0] in "01xz":
                value = line[0]
                code = line[1:]
            elif line[0] in "bBrR":
                parts = line.split()
                if len(parts) != 2:
                    continue
                value, code = parts
            else:
                continue

            if code in last_value and last_value[code] != value:
                toggles[code] += 1
            last_value[code] = value

    return dict(toggles)


def main() -> None:
    parser = argparse.ArgumentParser(description="Count raw VCD value changes by identifier code.")
    parser.add_argument("vcd", type=Path)
    args = parser.parse_args()
    counts = count_vcd_toggles(args.vcd)
    total = sum(counts.values())
    print(f"signals={len(counts)} total_toggles={total}")
    for code, count in sorted(counts.items(), key=lambda item: item[1], reverse=True)[:20]:
        print(f"{code}: {count}")


if __name__ == "__main__":
    main()
