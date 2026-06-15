`timescale 1ns/1ps

module tb_baseline_detector;
    `include "vectors.svh"

    logic clk = 1'b0;
    logic rst_n = 1'b0;
    logic start = 1'b0;
    logic sample_valid = 1'b0;
    logic [RTL_INPUT_WIDTH-1:0] sample_bits = '0;
    logic done;
    logic prediction;
    integer pass_count = 0;
    integer fail_count = 0;

`ifdef DETECTOR_FSM
    fsm_detector #(
        .INPUT_WIDTH(RTL_INPUT_WIDTH), .SEQ_LEN(RTL_SEQ_LEN), .MAX_GAP(RTL_FSM_MAX_GAP)
    ) dut (.*);
`elsif DETECTOR_LUT_LIKE
    lut_like_detector #(
        .INPUT_WIDTH(RTL_INPUT_WIDTH), .SEQ_LEN(RTL_SEQ_LEN),
        .MAX_TOTAL_SPIKES(RTL_LUT_MAX_TOTAL_SPIKES)
    ) dut (.*);
`else
    threshold_detector #(
        .INPUT_WIDTH(RTL_INPUT_WIDTH), .SEQ_LEN(RTL_SEQ_LEN),
        .MIN_ACTIVE_CYCLES(RTL_THRESHOLD_MIN_ACTIVE_CYCLES),
        .MIN_TOTAL_SPIKES(RTL_THRESHOLD_MIN_TOTAL_SPIKES)
    ) dut (.*);
`endif

    always #5 clk = ~clk;

    function automatic logic expected_prediction(input integer sample_index);
`ifdef DETECTOR_FSM
        expected_prediction = expected_fsm[sample_index];
`elsif DETECTOR_LUT_LIKE
        expected_prediction = expected_lut_like[sample_index];
`else
        expected_prediction = expected_threshold[sample_index];
`endif
    endfunction

    initial begin
        repeat (2) @(posedge clk);
        rst_n <= 1'b1;
        @(posedge clk);

        for (int sample_index = 0; sample_index < RTL_NUM_SAMPLES; sample_index++) begin
            start <= 1'b1;
            @(posedge clk);
            start <= 1'b0;
            for (int cycle = 0; cycle < RTL_SEQ_LEN; cycle++) begin
                sample_valid <= 1'b1;
                sample_bits <= vector_samples[(sample_index * RTL_SEQ_LEN) + cycle];
                @(posedge clk);
            end
            sample_valid <= 1'b0;
            sample_bits <= '0;
            #1;
            if (!done || prediction !== expected_prediction(sample_index)) begin
                $display("FAIL sample=%0d expected=%0d prediction=%0d done=%0d",
                         sample_index, expected_prediction(sample_index), prediction, done);
                fail_count = fail_count + 1;
            end else begin
                pass_count = pass_count + 1;
            end
            @(posedge clk);
        end

        $display("baseline detector: %0d passed, %0d failed", pass_count, fail_count);
        if (fail_count != 0) $fatal(1, "RTL prediction mismatch");
        $finish;
    end
endmodule
