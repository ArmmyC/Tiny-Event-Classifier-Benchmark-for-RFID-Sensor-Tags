// Tiny SNN detector candidate.
// Four hidden neurons feed a small ordered-progress output rule.

module tiny_snn_detector (
    input  logic       clk,
    input  logic       rst_n,
    input  logic       event_valid,
    input  logic [3:0] event_in,
    output logic       detected
);
    logic [3:0] h_spike;
    logic [1:0] ordered_progress;
    logic [3:0] spike_seen;

    tiny_if_neuron #(.W_POS(4'b0001), .W_NEG(4'b0010), .THRESHOLD(2)) h0 (
        .clk(clk), .rst_n(rst_n), .event_valid(event_valid), .event_in(event_in), .spike(h_spike[0])
    );
    tiny_if_neuron #(.W_POS(4'b0010), .W_NEG(4'b0001), .THRESHOLD(2)) h1 (
        .clk(clk), .rst_n(rst_n), .event_valid(event_valid), .event_in(event_in), .spike(h_spike[1])
    );
    tiny_if_neuron #(.W_POS(4'b0100), .W_NEG(4'b0010), .THRESHOLD(2)) h2 (
        .clk(clk), .rst_n(rst_n), .event_valid(event_valid), .event_in(event_in), .spike(h_spike[2])
    );
    tiny_if_neuron #(.W_POS(4'b0111), .W_NEG(4'b1000), .THRESHOLD(3)) h3 (
        .clk(clk), .rst_n(rst_n), .event_valid(event_valid), .event_in(event_in), .spike(h_spike[3])
    );

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            ordered_progress <= 2'd0;
            spike_seen <= 4'b0000;
            detected <= 1'b0;
        end else if (event_valid) begin
            spike_seen <= spike_seen | h_spike;

            if (ordered_progress == 2'd0 && h_spike[0]) begin
                ordered_progress <= 2'd1;
            end else if (ordered_progress == 2'd1 && h_spike[1]) begin
                ordered_progress <= 2'd2;
            end else if (ordered_progress == 2'd2 && h_spike[2]) begin
                ordered_progress <= 2'd3;
            end

            if (ordered_progress == 2'd3 ||
                (ordered_progress == 2'd2 && h_spike[2]) ||
                ((spike_seen | h_spike)[2:0] == 3'b111 && h_spike[3])) begin
                detected <= 1'b1;
            end
        end
    end
endmodule
