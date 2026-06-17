from __future__ import annotations

import os
import json
from pathlib import Path
import subprocess

from tinysnnrfid.run_rtl_sim import DESIGNS as SIM_DESIGNS
from tinysnnrfid.run_rtl_sim import run_rtl_sim
from tinysnnrfid.run_rtl_synth import DESIGNS as SYNTH_DESIGNS
from tinysnnrfid.run_rtl_synth import run_rtl_synth
from tinysnnrfid.run_rtl_synth import yosys_environment
from tinysnnrfid.summarize_rtl_results import summarize_rtl_results
from tinysnnrfid.summarize_vcd_activity import summarize_vcd_activity


def _which_factory(paths: dict[str, str]):
    def which(name: str) -> str | None:
        return paths.get(name)

    return which


def test_rtl_sim_skips_by_default_when_tools_are_missing(tmp_path, capsys) -> None:
    result = run_rtl_sim(tmp_path, which=_which_factory({}))

    assert result == 0
    assert "skipped" in capsys.readouterr().out.lower()
    status = json.loads((tmp_path / "sim_status.json").read_text(encoding="utf-8"))
    assert status["step"] == "sim"
    assert status["status"] == "skipped"
    assert status["missing_tools"] == ["iverilog", "vvp"]
    assert status["outputs_written"] == {}
    assert "stale" in status["note"]


def test_rtl_sim_strict_fails_when_tools_are_missing(tmp_path) -> None:
    assert run_rtl_sim(tmp_path, strict=True, which=_which_factory({})) == 1
    status = json.loads((tmp_path / "sim_status.json").read_text(encoding="utf-8"))
    assert status["status"] == "skipped"


def test_rtl_sim_respects_strict_environment(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("STRICT", "1")
    assert run_rtl_sim(tmp_path, which=_which_factory({})) == 1


def test_rtl_sim_runs_all_designs_and_writes_logs(tmp_path) -> None:
    commands: list[list[str]] = []

    def run(command, **kwargs):
        commands.append(command)
        if command[0] == "/tools/iverilog":
            Path(command[command.index("-o") + 1]).write_text("compiled\n", encoding="utf-8")
            return subprocess.CompletedProcess(command, 0, stdout="", stderr="")
        vcd_arg = next(arg for arg in command if str(arg).startswith("+VCD_FILE="))
        Path(vcd_arg.split("=", 1)[1]).write_text("$enddefinitions $end\n", encoding="utf-8")
        return subprocess.CompletedProcess(command, 0, stdout="5 passed, 0 failed\n", stderr="")

    result = run_rtl_sim(
        tmp_path,
        which=_which_factory({"iverilog": "/tools/iverilog", "vvp": "/tools/vvp"}),
        run=run,
    )

    assert result == 0
    assert len([cmd for cmd in commands if cmd[0] == "/tools/iverilog"]) == len(SIM_DESIGNS)
    assert len([cmd for cmd in commands if cmd[0] == "/tools/vvp"]) == len(SIM_DESIGNS)
    for name, define in SIM_DESIGNS:
        assert (tmp_path / f"sim_{name}.log").read_text(encoding="utf-8") == "5 passed, 0 failed\n"
        assert any(define in command for command in commands if command[0] == "/tools/iverilog")
        assert any(f"+VCD_FILE={tmp_path / f'vcd_{name}.vcd'}" in command for command in commands)
    status = json.loads((tmp_path / "sim_status.json").read_text(encoding="utf-8"))
    assert status["status"] == "pass"
    assert set(status["return_codes"]) == {name for name, _define in SIM_DESIGNS}
    assert "vcd_tiny_snn_v2_sparse_activity.vcd" in status["outputs_written"]["tiny_snn_v2_sparse_activity"]
    activity = summarize_vcd_activity(tmp_path)
    assert activity["baselines"]["tiny_snn_v2_sparse_activity"]["status"] == "available"


def test_rtl_sim_does_not_whitelist_old_vcd_when_vvp_does_not_recreate_it(tmp_path) -> None:
    old_vcd = tmp_path / "vcd_tiny_snn_v2_sparse_activity.vcd"
    old_vcd.write_text("old stale vcd\n", encoding="utf-8")

    def run(command, **kwargs):
        if command[0] == "/tools/iverilog":
            Path(command[command.index("-o") + 1]).write_text("compiled\n", encoding="utf-8")
            return subprocess.CompletedProcess(command, 0, stdout="", stderr="")
        return subprocess.CompletedProcess(command, 0, stdout="5 passed, 0 failed\n", stderr="")

    result = run_rtl_sim(
        tmp_path,
        which=_which_factory({"iverilog": "/tools/iverilog", "vvp": "/tools/vvp"}),
        run=run,
    )

    status = json.loads((tmp_path / "sim_status.json").read_text(encoding="utf-8"))
    sparse_outputs = status["outputs_written"]["tiny_snn_v2_sparse_activity"]
    assert result == 1
    assert status["status"] == "fail"
    assert "vcd_tiny_snn_v2_sparse_activity.vcd" not in sparse_outputs
    assert not old_vcd.exists()
    activity = summarize_vcd_activity(tmp_path)
    assert activity["baselines"]["tiny_snn_v2_sparse_activity"]["status"] == "missing"
    assert "total_toggles" not in activity["baselines"]["tiny_snn_v2_sparse_activity"]


def test_rtl_synth_skips_by_default_when_yosys_is_missing(tmp_path, capsys) -> None:
    result = run_rtl_synth(tmp_path, which=_which_factory({}))

    assert result == 0
    assert "skipped" in capsys.readouterr().out.lower()
    status = json.loads((tmp_path / "synth_status.json").read_text(encoding="utf-8"))
    assert status["step"] == "synth"
    assert status["status"] == "skipped"
    assert status["missing_tools"] == ["yosys"]
    assert status["outputs_written"] == {}
    assert "stale" in status["note"]


def test_rtl_synth_strict_fails_when_yosys_is_missing(tmp_path) -> None:
    assert run_rtl_synth(tmp_path, strict=True, which=_which_factory({})) == 1
    status = json.loads((tmp_path / "synth_status.json").read_text(encoding="utf-8"))
    assert status["status"] == "skipped"


def test_rtl_synth_respects_strict_environment(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("STRICT", "1")
    assert run_rtl_synth(tmp_path, which=_which_factory({})) == 1


def test_rtl_synth_runs_all_designs_and_writes_logs(tmp_path) -> None:
    commands: list[list[str]] = []
    envs: list[dict[str, str] | None] = []

    def run(command, **kwargs):
        commands.append(command)
        envs.append(kwargs.get("env"))
        json_path = Path(command[-1].rsplit("write_json ", 1)[1])
        json_path.write_text(json.dumps({"num_cells": 3}), encoding="utf-8")
        return subprocess.CompletedProcess(command, 0, stdout="synth ok\n", stderr="")

    result = run_rtl_synth(tmp_path, which=_which_factory({"yosys": "/tools/yosys"}), run=run)

    assert result == 0
    assert len(commands) == len(SYNTH_DESIGNS)
    assert all(env is not None for env in envs)
    for name, top, source in SYNTH_DESIGNS:
        assert (tmp_path / f"synth_{name}.log").read_text(encoding="utf-8") == "synth ok\n"
        command = next(cmd for cmd in commands if f"synth_{name}.json" in cmd[-1])
        assert command[:3] == ["/tools/yosys", "-q", "-p"]
        assert f"read_verilog -sv {source}" in command[-1]
        assert f"hierarchy -top {top}" in command[-1]
    status = json.loads((tmp_path / "synth_status.json").read_text(encoding="utf-8"))
    assert status["status"] == "pass"
    assert set(status["return_codes"]) == {name for name, _top, _source in SYNTH_DESIGNS}
    assert "synth_tiny_snn_v2_sparse_activity.json" in status["outputs_written"]["tiny_snn_v2_sparse_activity"]
    summary = summarize_rtl_results(tmp_path)
    assert summary["synthesis"]["tiny_snn_v2_sparse_activity"]["cell_count"] == 3


def test_rtl_synth_does_not_whitelist_old_json_when_yosys_does_not_recreate_it(tmp_path) -> None:
    old_json = tmp_path / "synth_tiny_snn_v2_sparse_activity.json"
    old_json.write_text(json.dumps({"num_cells": 610}), encoding="utf-8")

    def run(command, **kwargs):
        return subprocess.CompletedProcess(command, 0, stdout="synth ok\n", stderr="")

    result = run_rtl_synth(tmp_path, which=_which_factory({"yosys": "/tools/yosys"}), run=run)

    status = json.loads((tmp_path / "synth_status.json").read_text(encoding="utf-8"))
    sparse_outputs = status["outputs_written"]["tiny_snn_v2_sparse_activity"]
    assert result == 1
    assert status["status"] == "fail"
    assert "synth_tiny_snn_v2_sparse_activity.json" not in sparse_outputs
    assert not old_json.exists()
    summary = summarize_rtl_results(tmp_path)
    assert summary["synthesis"]["tiny_snn_v2_sparse_activity"]["status"] == "missing"
    assert "cell_count" not in summary["synthesis"]["tiny_snn_v2_sparse_activity"]


def test_yosys_environment_sets_datdir_for_oss_cad_suite_layout(tmp_path) -> None:
    yosys = tmp_path / "oss-cad-suite" / "bin" / "yosys.exe"
    datdir = tmp_path / "oss-cad-suite" / "share" / "yosys"
    yosys.parent.mkdir(parents=True)
    datdir.mkdir(parents=True)
    (datdir / "techmap.v").write_text("// techmap\n", encoding="utf-8")

    env = yosys_environment(str(yosys), base_env={})

    assert env["YOSYS_DATDIR"] == str(datdir)


def test_rtl_synth_uses_bundled_techmap_when_available(tmp_path) -> None:
    yosys = tmp_path / "oss-cad-suite" / "bin" / "yosys.exe"
    datdir = tmp_path / "oss-cad-suite" / "share" / "yosys"
    yosys.parent.mkdir(parents=True)
    datdir.mkdir(parents=True)
    (datdir / "techmap.v").write_text("// techmap\n", encoding="utf-8")
    commands: list[list[str]] = []

    def run(command, **kwargs):
        commands.append(command)
        json_path = Path(command[-1].rsplit("write_json ", 1)[1])
        json_path.write_text(json.dumps({"num_cells": 3}), encoding="utf-8")
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    assert run_rtl_synth(tmp_path / "out", which=_which_factory({"yosys": str(yosys)}), run=run) == 0
    assert f"techmap -map {(datdir / 'techmap.v').as_posix()}" in commands[0][-1]


def test_strict_environment_helper_does_not_mutate_environment(monkeypatch) -> None:
    monkeypatch.delenv("STRICT", raising=False)
    assert os.environ.get("STRICT") is None
