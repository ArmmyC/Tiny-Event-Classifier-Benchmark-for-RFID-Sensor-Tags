#!/usr/bin/env bash
set -euo pipefail

if ! command -v yosys >/dev/null 2>&1; then
  echo "RTL synthesis skipped: yosys is required. Set STRICT=1 to fail."
  if [[ "${STRICT:-0}" == "1" ]]; then exit 1; fi
  exit 0
fi

mkdir -p results/rtl

run_detector() {
  local name="$1"
  local top="$2"
  local source="$3"
  yosys -q -p "read_verilog -sv ${source}; hierarchy -top ${top}; proc; opt; fsm; opt; techmap; opt; stat; write_json results/rtl/synth_${name}.json" \
    2>&1 | tee "results/rtl/synth_${name}.log"
}

run_detector threshold threshold_detector rtl/baselines/threshold_detector.sv
run_detector fsm fsm_detector rtl/baselines/fsm_detector.sv
run_detector lut_like lut_like_detector rtl/baselines/lut_like_detector.sv
run_detector tiny_snn_v2 tiny_snn_v2_detector rtl/snn/tiny_snn_v2_detector.sv
run_detector tiny_snn_v2_sparse_activity tiny_snn_v2_sparse_activity_detector rtl/snn/tiny_snn_v2_sparse_activity_detector.sv
