// LUT-like detector using compact feature state.
// Tracks which channels have appeared and whether first-observed order is plausible.

module lut_detector (
    input  logic       clk,
    input  logic       rst_n,
    input  logic       event_valid,
    input  logic [3:0] event_in,
    output logic       detected
);
    logic [3:0] seen;
    logic [1:0] ordered_progress;
    logic [3:0] total_spikes_sat;

    function automatic logic [2:0] popcount4(input logic [3:0] value);
        return value[0] + value[1] + value[2] + value[3];
    endfunction

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            seen <= 4'b0000;
            ordered_progress <= 2'd0;
            total_spikes_sat <= 4'd0;
            detected <= 1'b0;
        end else if (event_valid) begin
            seen <= seen | event_in;

            if (total_spikes_sat != 4'hf) begin
                total_spikes_sat <= total_spikes_sat + popcount4(event_in);
            end

            if (ordered_progress == 2'd0 && event_in[0]) begin
                ordered_progress <= 2'd1;
            end else if (ordered_progress == 2'd1 && event_in[1]) begin
                ordered_progress <= 2'd2;
            end else if (ordered_progress == 2'd2 && event_in[2]) begin
                ordered_progress <= 2'd3;
            end

            detected <= (((seen | event_in) & 4'b0111) == 4'b0111)
                     && (ordered_progress >= 2'd2)
                     && (total_spikes_sat <= 4'd10);
        end
    end
endmodule
