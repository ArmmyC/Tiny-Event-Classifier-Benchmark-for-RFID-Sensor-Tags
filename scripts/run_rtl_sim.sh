#!/usr/bin/env bash
set -euo pipefail

if ! command -v iverilog >/dev/null 2>&1 || ! command -v vvp >/dev/null 2>&1; then
  echo "RTL simulation skipped: iverilog and vvp are required. Set STRICT=1 to fail."
  if [[ "${STRICT:-0}" == "1" ]]; then exit 1; fi
  exit 0
fi

mkdir -p results/rtl

run_detector() {
  local name="$1"
  local define="$2"
  local executable="results/rtl/sim_${name}.out"
  iverilog -g2012 -Wall -I results/rtl -D "${define}" -o "${executable}" \
    rtl/baselines/threshold_detector.sv \
    rtl/baselines/fsm_detector.sv \
    rtl/baselines/lut_like_detector.sv \
    rtl/snn/tiny_snn_v2_detector.sv \
    rtl/tb/tb_baseline_detector.sv
  vvp "${executable}" "+VCD_FILE=results/rtl/vcd_${name}.vcd" | tee "results/rtl/sim_${name}.log"
}

run_detector threshold DETECTOR_THRESHOLD
run_detector fsm DETECTOR_FSM
run_detector lut_like DETECTOR_LUT_LIKE
run_detector tiny_snn_v2 DETECTOR_TINY_SNN_V2
