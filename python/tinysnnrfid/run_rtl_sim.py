from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Callable


DESIGNS: tuple[tuple[str, str], ...] = (
    ("threshold", "DETECTOR_THRESHOLD"),
    ("fsm", "DETECTOR_FSM"),
    ("lut_like", "DETECTOR_LUT_LIKE"),
    ("tiny_snn_v2", "DETECTOR_TINY_SNN_V2"),
    ("tiny_snn_v2_sparse_activity", "DETECTOR_TINY_SNN_V2_SPARSE_ACTIVITY"),
)

SOURCES: tuple[str, ...] = (
    "rtl/baselines/threshold_detector.sv",
    "rtl/baselines/fsm_detector.sv",
    "rtl/baselines/lut_like_detector.sv",
    "rtl/snn/tiny_snn_v2_detector.sv",
    "rtl/snn/tiny_snn_v2_sparse_activity_detector.sv",
    "rtl/tb/tb_baseline_detector.sv",
)

WhichFunc = Callable[[str], str | None]
RunFunc = Callable[..., subprocess.CompletedProcess[str]]


def strict_enabled(value: bool = False) -> bool:
    return value or os.environ.get("STRICT") == "1"


def _combined_output(completed: subprocess.CompletedProcess[str]) -> str:
    return "".join(part for part in (completed.stdout, completed.stderr) if part)


def run_rtl_sim(
    output_dir: str | Path = "results/rtl",
    *,
    strict: bool = False,
    which: WhichFunc = shutil.which,
    run: RunFunc = subprocess.run,
) -> int:
    strict = strict_enabled(strict)
    iverilog = which("iverilog")
    vvp = which("vvp")
    missing = [name for name, path in (("iverilog", iverilog), ("vvp", vvp)) if path is None]
    if missing:
        print("RTL simulation skipped: iverilog and vvp are required. Set STRICT=1 or pass --strict to fail.")
        return 1 if strict else 0

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    status = 0
    for name, define in DESIGNS:
        executable = output_path / f"sim_{name}.out"
        log_path = output_path / f"sim_{name}.log"
        vcd_path = output_path / f"vcd_{name}.vcd"
        compile_command = [
            iverilog,
            "-g2012",
            "-Wall",
            "-I",
            str(output_path),
            "-D",
            define,
            "-o",
            str(executable),
            *SOURCES,
        ]
        compiled = run(compile_command, capture_output=True, text=True, check=False)
        compile_output = _combined_output(compiled)
        if compiled.returncode != 0:
            log_path.write_text(compile_output, encoding="utf-8")
            print(compile_output, end="")
            status = compiled.returncode or 1
            continue

        sim_command = [vvp, str(executable), f"+VCD_FILE={vcd_path}"]
        simulated = run(sim_command, capture_output=True, text=True, check=False)
        sim_output = _combined_output(simulated)
        log_path.write_text(sim_output, encoding="utf-8")
        print(sim_output, end="")
        if simulated.returncode != 0:
            status = simulated.returncode
    return status


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run RTL detector simulations without requiring Bash.")
    parser.add_argument("--output-dir", type=Path, default=Path("results/rtl"))
    parser.add_argument("--strict", action="store_true", help="Exit nonzero if required simulation tools are missing.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return run_rtl_sim(args.output_dir, strict=args.strict)
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
