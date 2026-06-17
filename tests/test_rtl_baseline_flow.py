from __future__ import annotations

import json
from pathlib import Path

from tinysnnrfid.export_rtl_vectors import export_rtl_vectors
from tinysnnrfid.clean_outputs import DIRECTORIES
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
    for fixed_weight_marker in ("W_C0_N0", "OW_N0", "HIDDEN_THRESHOLD", "OUTPUT_THRESHOLD"):
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
        for neuron, weight in enumerate(row):
            if weight:
                sign = "-" if weight < 0 else ""
                assert f"localparam calc_t W_C{channel}_N{neuron} = {sign}5'sd{abs(weight)};" in source
    for neuron, weight in enumerate(expected_output_weights):
        sign = "-" if weight < 0 else ""
        assert f"localparam calc_t OW_N{neuron} = {sign}5'sd{abs(weight)};" in source


def test_makefile_and_python_runners_cover_rtl_flow() -> None:
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    for target in ("rtl-vectors:", "rtl-sim:", "rtl-synth:", "rtl-activity:", "rtl-report:"):
        assert target in makefile
    assert "\tpython python/run_rtl_sim.py" in makefile
    assert "\tpython python/run_rtl_synth.py" in makefile
    assert "bash scripts/run_rtl_sim.sh" not in makefile
    assert "bash scripts/run_rtl_synth.sh" not in makefile
    assert "results/rtl" in DIRECTORIES
    tb = (ROOT / "rtl" / "tb" / "tb_baseline_detector.sv").read_text(encoding="utf-8")
    assert "VCD_FILE=%s" in tb
    assert "$dumpvars" in tb
    assert "DETECTOR_TINY_SNN_V2" in tb
    assert "expected_tiny_snn_v2" in tb
    assert "DETECTOR_TINY_SNN_V2_SPARSE_ACTIVITY" in tb
    assert "expected_tiny_snn_v2_sparse_activity" in tb
    sim_runner = (ROOT / "python" / "tinysnnrfid" / "run_rtl_sim.py").read_text(encoding="utf-8")
    assert "rtl/snn/tiny_snn_v2_detector.sv" in sim_runner
    assert "rtl/snn/tiny_snn_v2_sparse_activity_detector.sv" in sim_runner
    assert "DETECTOR_TINY_SNN_V2" in sim_runner
    assert "DETECTOR_TINY_SNN_V2_SPARSE_ACTIVITY" in sim_runner
    assert "sim_{name}.log" in sim_runner
    assert "vcd_{name}.vcd" in sim_runner
    synth_runner = (ROOT / "python" / "tinysnnrfid" / "run_rtl_synth.py").read_text(encoding="utf-8")
    assert "rtl/snn/tiny_snn_v2_detector.sv" in synth_runner
    assert "rtl/snn/tiny_snn_v2_sparse_activity_detector.sv" in synth_runner
    assert "synth_{name}.json" in synth_runner
    assert "synth_{name}.log" in synth_runner


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
