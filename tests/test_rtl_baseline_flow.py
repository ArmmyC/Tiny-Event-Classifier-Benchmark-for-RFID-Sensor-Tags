from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess

from tinysnnrfid.export_rtl_vectors import export_rtl_vectors
from tinysnnrfid.run_snn_search import WEIGHT_VARIANTS


ROOT = Path(__file__).resolve().parents[1]


def test_rtl_sources_and_modules_exist() -> None:
    expected = {
        "threshold_detector.sv": "module threshold_detector",
        "fsm_detector.sv": "module fsm_detector",
        "lut_like_detector.sv": "module lut_like_detector",
    }
    for filename, module_name in expected.items():
        source = ROOT / "rtl" / "baselines" / filename
        assert source.is_file()
        text = source.read_text(encoding="utf-8")
        assert module_name in text
        for port in ("clk", "rst_n", "start", "sample_valid", "sample_bits", "done", "prediction"):
            assert port in text
    assert (ROOT / "rtl" / "tb" / "tb_baseline_detector.sv").is_file()
    snn_source = ROOT / "rtl" / "snn" / "tiny_snn_v2_detector.sv"
    assert snn_source.is_file()
    snn_text = snn_source.read_text(encoding="utf-8")
    assert "module tiny_snn_v2_detector" in snn_text
    for port in ("clk", "rst_n", "start", "sample_valid", "sample_bits", "done", "prediction"):
        assert port in snn_text
    for fixed_weight_marker in ("input_weight", "output_weight", "HIDDEN_THRESHOLD", "OUTPUT_THRESHOLD"):
        assert fixed_weight_marker in snn_text
    sparse_source = ROOT / "rtl" / "snn" / "tiny_snn_v2_sparse_activity_detector.sv"
    assert sparse_source.is_file()
    sparse_text = sparse_source.read_text(encoding="utf-8")
    assert "module tiny_snn_v2_sparse_activity_detector" in sparse_text
    for port in ("clk", "rst_n", "start", "sample_valid", "sample_bits", "done", "prediction"):
        assert port in sparse_text
    for fixed_weight_marker in ("input_weight", "output_weight", "HIDDEN_THRESHOLD", "OUTPUT_THRESHOLD"):
        assert fixed_weight_marker in sparse_text


def test_sparse_activity_rtl_weights_match_search_variant() -> None:
    source = (ROOT / "rtl" / "snn" / "tiny_snn_v2_sparse_activity_detector.sv").read_text(encoding="utf-8")
    variant = WEIGHT_VARIANTS["current_default_sparse_activity"]
    expected_input_weights = [
        [4, 0, 0, -1, 2, 0],
        [0, 3, 0, -1, 2, 2],
        [0, 0, 4, -1, 0, 2],
        [-1, -1, -1, 6, -1, -1],
    ]
    expected_output_weights = [-1, 0, 1, -2, 1, 1]
    assert variant["input_weights"] == expected_input_weights
    assert variant["output_weights"] == expected_output_weights
    for channel, row in enumerate(expected_input_weights):
        assert f"{channel}: begin" in source
        for neuron, weight in enumerate(row):
            if weight:
                assert f"{neuron}: input_weight = {weight};" in source
    for neuron, weight in enumerate(expected_output_weights):
        assert f"{neuron}: output_weight = {weight};" in source


def test_makefile_and_scripts_cover_rtl_flow() -> None:
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    for target in ("rtl-vectors:", "rtl-sim:", "rtl-synth:", "rtl-activity:", "rtl-report:"):
        assert target in makefile
    assert "results/rtl" in makefile
    tb = (ROOT / "rtl" / "tb" / "tb_baseline_detector.sv").read_text(encoding="utf-8")
    assert "VCD_FILE=%s" in tb
    assert "$dumpvars" in tb
    assert "DETECTOR_TINY_SNN_V2" in tb
    assert "expected_tiny_snn_v2" in tb
    assert "DETECTOR_TINY_SNN_V2_SPARSE_ACTIVITY" in tb
    assert "expected_tiny_snn_v2_sparse_activity" in tb
    sim_script = (ROOT / "scripts" / "run_rtl_sim.sh").read_text(encoding="utf-8")
    assert "rtl/snn/tiny_snn_v2_detector.sv" in sim_script
    assert "rtl/snn/tiny_snn_v2_sparse_activity_detector.sv" in sim_script
    assert "DETECTOR_TINY_SNN_V2" in sim_script
    assert "DETECTOR_TINY_SNN_V2_SPARSE_ACTIVITY" in sim_script
    assert "sim_${name}.log" in sim_script
    assert "vcd_${name}.vcd" in sim_script
    assert "tiny_snn_v2_sparse_activity" in sim_script
    synth_script = (ROOT / "scripts" / "run_rtl_synth.sh").read_text(encoding="utf-8")
    assert "rtl/snn/tiny_snn_v2_detector.sv" in synth_script
    assert "rtl/snn/tiny_snn_v2_sparse_activity_detector.sv" in synth_script
    assert "synth_${name}.json" in synth_script
    assert "synth_${name}.log" in synth_script
    assert "tiny_snn_v2_sparse_activity" in synth_script
    for filename in ("run_rtl_sim.sh", "run_rtl_synth.sh"):
        script = ROOT / "scripts" / filename
        assert script.is_file()
        text = script.read_text(encoding="utf-8")
        assert "STRICT" in text
        assert "exit 0" in text


def test_export_rtl_vectors_for_tiny_config(tmp_path: Path) -> None:
    raw = json.loads((ROOT / "configs" / "default.json").read_text(encoding="utf-8"))
    raw["dataset"]["num_samples"] = 3
    raw["dataset"]["sequence_length"] = 8
    config_path = tmp_path / "tiny.json"
    config_path.write_text(json.dumps(raw), encoding="utf-8")
    output = export_rtl_vectors(config_path, tmp_path / "rtl" / "vectors.svh")
    text = output.read_text(encoding="ascii")
    assert "RTL_NUM_SAMPLES = 3" in text
    assert "RTL_SEQ_LEN = 8" in text
    assert text.count("vector_samples[") == 24
    assert "expected_threshold[2]" in text
    assert "expected_fsm[2]" in text
    assert "expected_lut_like[2]" in text
    assert "expected_tiny_snn_v2[2]" in text
    assert "expected_tiny_snn_v2_sparse_activity[2]" in text


def test_scripts_skip_when_tools_are_missing(tmp_path: Path) -> None:
    bash = shutil.which("bash")
    if bash is None:
        return
    env = {**os.environ, "PATH": str(tmp_path), "STRICT": "0"}
    for filename in ("run_rtl_sim.sh", "run_rtl_synth.sh"):
        result = subprocess.run(
            [bash, f"scripts/{filename}"],
            cwd=ROOT,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0
        assert "skipped" in result.stdout.lower()

        strict_result = subprocess.run(
            [bash, "-c", f"STRICT=1 scripts/{filename}"],
            cwd=ROOT,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        assert strict_result.returncode != 0
