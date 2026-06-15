#!/usr/bin/env bash
set -euo pipefail

TOP=${1:-threshold_detector}
mkdir -p results/synthesis
yosys -q -p "read_verilog -sv rtl/threshold_detector.sv rtl/fsm_detector.sv rtl/lut_detector.sv rtl/tiny_if_neuron.sv rtl/tiny_snn_detector.sv; hierarchy -top ${TOP}; proc; opt; fsm; opt; techmap; opt; stat" \
  | tee "results/synthesis/${TOP}_stat.rpt"
