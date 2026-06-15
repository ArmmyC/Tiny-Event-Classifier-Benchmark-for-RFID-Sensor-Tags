// Simple threshold detector for RFID-style event streams.
// This is a hard baseline: small, deterministic, and easy to verify.

module threshold_detector #(
    parameter int INPUT_WIDTH = 4,
    parameter int WINDOW = 8,
    parameter int MIN_ACTIVE_CYCLES = 3
) (
    input  logic                   clk,
    input  logic                   rst_n,
    input  logic                   event_valid,
    input  logic [INPUT_WIDTH-1:0] event_in,
    output logic                   detected
);
    logic [WINDOW-1:0] active_hist;
    logic [$clog2(WINDOW+1)-1:0] active_count;

    function automatic logic [$clog2(WINDOW+1)-1:0] popcount_window(input logic [WINDOW-1:0] value);
        logic [$clog2(WINDOW+1)-1:0] count;
        begin
            count = '0;
            for (int i = 0; i < WINDOW; i++) begin
                count = count + value[i];
            end
            return count;
        end
    endfunction

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            active_hist <= '0;
            detected <= 1'b0;
        end else if (event_valid) begin
            active_hist <= {active_hist[WINDOW-2:0], |event_in};
            detected <= (active_count >= MIN_ACTIVE_CYCLES);
        end
    end

    always_comb begin
        active_count = popcount_window({active_hist[WINDOW-2:0], |event_in});
    end
endmodule
