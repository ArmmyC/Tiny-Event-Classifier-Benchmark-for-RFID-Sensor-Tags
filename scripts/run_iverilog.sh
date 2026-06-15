#!/usr/bin/env bash
set -euo pipefail

mkdir -p results/vcd
iverilog -g2012 -Wall -o sim.out \
  rtl/threshold_detector.sv \
  rtl/fsm_detector.sv \
  rtl/lut_detector.sv \
  rtl/tiny_if_neuron.sv \
  rtl/tiny_snn_detector.sv \
  tb/tb_detectors.sv
vvp sim.out
python scripts/count_vcd_toggles.py results/vcd/tb_detectors.vcd
