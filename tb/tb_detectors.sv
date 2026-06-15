`timescale 1ns/1ps

module tb_detectors;
    logic clk;
    logic rst_n;
    logic event_valid;
    logic [3:0] event_in;

    logic threshold_detected;
    logic fsm_detected;
    logic lut_detected;
    logic snn_detected;

    threshold_detector u_threshold (
        .clk(clk),
        .rst_n(rst_n),
        .event_valid(event_valid),
        .event_in(event_in),
        .detected(threshold_detected)
    );

    fsm_detector u_fsm (
        .clk(clk),
        .rst_n(rst_n),
        .event_valid(event_valid),
        .event_in(event_in),
        .detected(fsm_detected)
    );

    lut_detector u_lut (
        .clk(clk),
        .rst_n(rst_n),
        .event_valid(event_valid),
        .event_in(event_in),
        .detected(lut_detected)
    );

    tiny_snn_detector u_snn (
        .clk(clk),
        .rst_n(rst_n),
        .event_valid(event_valid),
        .event_in(event_in),
        .detected(snn_detected)
    );

    always #5 clk = ~clk;

    task automatic drive(input logic [3:0] value);
        begin
            @(negedge clk);
            event_valid = 1'b1;
            event_in = value;
            @(negedge clk);
            event_in = 4'b0000;
        end
    endtask

    initial begin
        $dumpfile("results/vcd/tb_detectors.vcd");
        $dumpvars(0, tb_detectors);

        clk = 1'b0;
        rst_n = 1'b0;
        event_valid = 1'b0;
        event_in = 4'b0000;

        repeat (3) @(negedge clk);
        rst_n = 1'b1;
        event_valid = 1'b1;

        // Sparse valid motif with idle cycles between events.
        drive(4'b0001);
        drive(4'b0000);
        drive(4'b0010);
        drive(4'b0000);
        drive(4'b0100);

        repeat (8) drive(4'b0000);

        $display("threshold=%0d fsm=%0d lut=%0d snn=%0d", threshold_detected, fsm_detected, lut_detected, snn_detected);
        $finish;
    end
endmodule
