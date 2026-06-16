from __future__ import annotations

import subprocess
from pathlib import Path

from tinysnnrfid.check_rtl_toolchain import (
    PROXY_LIMITATION,
    check_tool,
    main,
    render_markdown,
    write_toolchain_status,
)


ROOT = Path(__file__).resolve().parents[1]


def _which_factory(paths: dict[str, str]):
    def which(name: str) -> str | None:
        return paths.get(name)

    return which


def _successful_run(command, **kwargs):
    return subprocess.CompletedProcess(command, 0, stdout="Tool version 1.2.3\n", stderr="")


def test_check_tool_handles_found_tool_with_version() -> None:
    status = check_tool(
        "iverilog",
        {
            "version_args": ["-V"],
            "role": "compile simulations",
            "required_for": ["rtl-sim"],
        },
        which=_which_factory({"iverilog": "/tools/iverilog"}),
        run=_successful_run,
    )

    assert status["found"] is True
    assert status["path"] == "/tools/iverilog"
    assert status["version_available"] is True
    assert status["version"] == "Tool version 1.2.3"
    assert status["role"] == "compile simulations"
    assert status["required_for"] == ["rtl-sim"]


def test_check_tool_handles_missing_tool_without_running_version() -> None:
    calls: list[object] = []

    def run(command, **kwargs):
        calls.append(command)
        return _successful_run(command, **kwargs)

    status = check_tool(
        "yosys",
        {
            "version_args": ["-V"],
            "role": "synthesize",
            "required_for": ["rtl-synth"],
        },
        which=_which_factory({}),
        run=run,
    )

    assert status["found"] is False
    assert status["path"] is None
    assert status["version_available"] is False
    assert status["version"] is None
    assert calls == []


def test_check_tool_reports_version_failure_but_keeps_found_true() -> None:
    def failing_run(command, **kwargs):
        return subprocess.CompletedProcess(command, 1, stdout="", stderr="bad option\n")

    status = check_tool(
        "bash",
        {
            "version_args": ["--version"],
            "role": "run scripts",
            "required_for": ["rtl-sim"],
        },
        which=_which_factory({"bash": "/bin/bash"}),
        run=failing_run,
    )

    assert status["found"] is True
    assert status["version_available"] is False
    assert status["version"] == "version check failed: bad option"


def test_outputs_are_written_and_missing_tools_are_clear(tmp_path) -> None:
    status = write_toolchain_status(
        tmp_path,
        which=_which_factory({"bash": "/bin/bash"}),
        run=_successful_run,
    )

    assert (tmp_path / "toolchain_status.json").is_file()
    assert (tmp_path / "toolchain_status.md").is_file()
    assert status["all_required_found"] is False
    assert status["missing_required_tools"] == ["iverilog", "vvp", "yosys"]
    markdown = (tmp_path / "toolchain_status.md").read_text(encoding="utf-8")
    assert "## Missing Tools" in markdown
    assert "`iverilog` is missing; required for rtl-sim." in markdown
    assert "`vvp` is missing; required for rtl-sim, rtl-activity." in markdown
    assert "`yosys` is missing; required for rtl-synth." in markdown
    assert PROXY_LIMITATION in markdown


def test_bash_is_optional_for_required_tool_status(tmp_path) -> None:
    status = write_toolchain_status(
        tmp_path,
        which=_which_factory({"iverilog": "/tools/iverilog", "vvp": "/tools/vvp", "yosys": "/tools/yosys"}),
        run=_successful_run,
    )

    assert status["all_required_found"] is True
    assert status["missing_required_tools"] == []
    assert status["tools"]["bash"]["found"] is False
    assert status["tools"]["bash"]["required"] is False
    markdown = (tmp_path / "toolchain_status.md").read_text(encoding="utf-8")
    assert "| bash | no | no |" in markdown


def test_strict_mode_returns_nonzero_when_tools_are_missing(tmp_path, monkeypatch) -> None:
    import tinysnnrfid.check_rtl_toolchain as doctor

    monkeypatch.setattr(
        doctor,
        "write_toolchain_status",
        lambda output_dir: {
            "all_required_found": False,
            "missing_required_tools": ["iverilog"],
        },
    )

    assert main(["--strict", "--output-dir", str(tmp_path)]) == 1


def test_non_strict_mode_allows_missing_tools(tmp_path, monkeypatch) -> None:
    import tinysnnrfid.check_rtl_toolchain as doctor

    monkeypatch.setattr(
        doctor,
        "write_toolchain_status",
        lambda output_dir: {
            "all_required_found": False,
            "missing_required_tools": ["iverilog"],
        },
    )

    assert main(["--output-dir", str(tmp_path)]) == 0


def test_makefile_contains_rtl_doctor_without_evidence_dependency() -> None:
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    assert "rtl-doctor" in next(line for line in makefile.splitlines() if line.startswith(".PHONY:"))
    assert "rtl-doctor:" in makefile
    assert "\tpython python/check_rtl_toolchain.py" in makefile
    evidence_header = next(line for line in makefile.splitlines() if line.startswith("evidence:"))
    assert "rtl-doctor" not in evidence_header.split(":", 1)[1].split()


def test_readme_mentions_rtl_doctor_and_limitations() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "make rtl-doctor" in readme
    assert "bash" in readme
    assert "iverilog" in readme
    assert "vvp" in readme
    assert "yosys" in readme
    assert "may skip by design" in readme


def test_rendered_text_includes_proxy_signoff_limitation() -> None:
    markdown = render_markdown(
        {
            "all_required_found": True,
            "missing_required_tools": [],
            "tools": {},
            "note": PROXY_LIMITATION,
        }
    )
    assert "not silicon signoff" in markdown
    assert "measured power" in markdown
