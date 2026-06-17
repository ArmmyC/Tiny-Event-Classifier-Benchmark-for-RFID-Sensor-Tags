from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def status_path(directory: str | Path, step: str) -> Path:
    return Path(directory) / f"{step}_status.json"


def write_status(
    directory: str | Path,
    step: str,
    *,
    started_at: str,
    status: str,
    missing_tools: list[str] | None = None,
    outputs_written: dict[str, list[str]] | list[str] | None = None,
    return_codes: dict[str, Any] | None = None,
    note: str = "",
) -> dict[str, Any]:
    path = status_path(directory, step)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {
        "step": step,
        "started_at": started_at,
        "finished_at": utc_now(),
        "status": status,
        "missing_tools": missing_tools or [],
        "outputs_written": outputs_written or {},
        "return_codes": return_codes or {},
        "note": note,
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def load_status(directory: str | Path, step: str) -> dict[str, Any] | None:
    path = status_path(directory, step)
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    return payload if isinstance(payload, dict) else None


def status_allows_step(status: dict[str, Any] | None) -> bool:
    return isinstance(status, dict) and status.get("status") == "pass"


def design_output_was_written(
    status: dict[str, Any] | None,
    design: str,
    filename: str,
) -> bool:
    if not isinstance(status, dict):
        return False
    outputs = status.get("outputs_written")
    if isinstance(outputs, dict):
        design_outputs = outputs.get(design, [])
        if isinstance(design_outputs, list):
            return filename in {str(item) for item in design_outputs}
    if isinstance(outputs, list):
        return filename in {str(item) for item in outputs}
    return False


def stale_result(path: str | Path, *, reason: str) -> dict[str, Any]:
    file_path = Path(path)
    return {
        "found": file_path.is_file(),
        "status": "stale" if file_path.is_file() else "missing",
        "stale": file_path.is_file(),
        "reason": reason,
    }
