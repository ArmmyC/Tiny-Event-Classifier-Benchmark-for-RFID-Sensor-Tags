from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Callable

from tinysnnrfid.rtl_status import utc_now, write_status


DESIGNS: tuple[tuple[str, str, str], ...] = (
    ("threshold", "threshold_detector", "rtl/baselines/threshold_detector.sv"),
    ("fsm", "fsm_detector", "rtl/baselines/fsm_detector.sv"),
    ("lut_like", "lut_like_detector", "rtl/baselines/lut_like_detector.sv"),
    ("tiny_snn_v2", "tiny_snn_v2_detector", "rtl/snn/tiny_snn_v2_detector.sv"),
    (
        "tiny_snn_v2_sparse_activity",
        "tiny_snn_v2_sparse_activity_detector",
        "rtl/snn/tiny_snn_v2_sparse_activity_detector.sv",
    ),
)

WhichFunc = Callable[[str], str | None]
RunFunc = Callable[..., subprocess.CompletedProcess[str]]


def strict_enabled(value: bool = False) -> bool:
    return value or os.environ.get("STRICT") == "1"


def _combined_output(completed: subprocess.CompletedProcess[str]) -> str:
    return "".join(part for part in (completed.stdout, completed.stderr) if part)


def _remove_stale_outputs(paths: tuple[Path, ...]) -> None:
    for path in paths:
        path.unlink(missing_ok=True)


def _techmap_command(yosys_path: str) -> str:
    bundled_techmap = Path(yosys_path).parent.parent / "share" / "yosys" / "techmap.v"
    if bundled_techmap.is_file():
        return f"techmap -map {bundled_techmap.as_posix()}"
    return "techmap"


def _yosys_script(source: str, top: str, json_path: Path, yosys_path: str) -> str:
    return (
        f"read_verilog -sv {source}; "
        f"hierarchy -top {top}; "
        f"proc; opt; fsm; opt; {_techmap_command(yosys_path)}; opt; stat; "
        f"write_json {json_path}"
    )


def yosys_environment(yosys_path: str, base_env: dict[str, str] | None = None) -> dict[str, str]:
    env = dict(os.environ if base_env is None else base_env)
    executable = Path(yosys_path)
    suite_share = executable.parent.parent / "share" / "yosys"
    if "YOSYS_DATDIR" not in env and (suite_share / "techmap.v").is_file():
        env["YOSYS_DATDIR"] = str(suite_share)
    return env


def run_rtl_synth(
    output_dir: str | Path = "results/rtl",
    *,
    strict: bool = False,
    which: WhichFunc = shutil.which,
    run: RunFunc = subprocess.run,
) -> int:
    started_at = utc_now()
    strict = strict_enabled(strict)
    output_path = Path(output_dir)
    yosys = which("yosys")
    if yosys is None:
        output_path.mkdir(parents=True, exist_ok=True)
        write_status(
            output_path,
            "synth",
            started_at=started_at,
            status="skipped",
            missing_tools=["yosys"],
            outputs_written={},
            return_codes={},
            note=(
                "RTL synthesis was skipped in the current run because yosys was missing. "
                "Previous synthesis JSON and logs must be ignored as stale."
            ),
        )
        print("RTL synthesis skipped: yosys is required. Set STRICT=1 or pass --strict to fail.")
        return 1 if strict else 0

    output_path.mkdir(parents=True, exist_ok=True)
    status = 0
    outputs_written: dict[str, list[str]] = {}
    return_codes: dict[str, int] = {}
    env = yosys_environment(yosys)
    for name, top, source in DESIGNS:
        json_path = output_path / f"synth_{name}.json"
        log_path = output_path / f"synth_{name}.log"
        _remove_stale_outputs((json_path, log_path))
        command = [yosys, "-q", "-p", _yosys_script(source, top, json_path, yosys)]
        completed = run(command, capture_output=True, text=True, check=False, env=env)
        output = _combined_output(completed)
        return_codes[name] = completed.returncode
        log_path.write_text(output, encoding="utf-8")
        outputs_written.setdefault(name, []).append(log_path.name)
        if json_path.is_file():
            outputs_written.setdefault(name, []).append(json_path.name)
        elif completed.returncode == 0:
            status = 1
        print(output, end="")
        if completed.returncode != 0:
            status = completed.returncode
    write_status(
        output_path,
        "synth",
        started_at=started_at,
        status="pass" if status == 0 else "fail",
        missing_tools=[],
        outputs_written=outputs_written,
        return_codes=return_codes,
        note=(
            "RTL synthesis completed in the current run."
            if status == 0
            else (
                "RTL synthesis failed or was incomplete in the current run; "
                "only outputs listed here are current."
            )
        ),
    )
    return status


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run RTL detector synthesis without requiring Bash.")
    parser.add_argument("--output-dir", type=Path, default=Path("results/rtl"))
    parser.add_argument("--strict", action="store_true", help="Exit nonzero if Yosys is missing.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return run_rtl_synth(args.output_dir, strict=args.strict)
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
