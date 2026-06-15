// Tiny integrate-and-fire neuron with ternary weights encoded by masks.
// +1 weights are set in W_POS. -1 weights are set in W_NEG.

module tiny_if_neuron #(
    parameter int INPUT_WIDTH = 4,
    parameter logic [INPUT_WIDTH-1:0] W_POS = 4'b0001,
    parameter logic [INPUT_WIDTH-1:0] W_NEG = 4'b0000,
    parameter int MEM_BITS = 4,
    parameter int THRESHOLD = 2,
    parameter int LEAK = 1
) (
    input  logic                   clk,
    input  logic                   rst_n,
    input  logic                   event_valid,
    input  logic [INPUT_WIDTH-1:0] event_in,
    output logic                   spike
);
    logic signed [MEM_BITS:0] mem;
    logic signed [MEM_BITS:0] drive;
    logic signed [MEM_BITS:0] mem_next;

    function automatic logic [2:0] popcount4(input logic [3:0] value);
        return value[0] + value[1] + value[2] + value[3];
    endfunction

    always_comb begin
        drive = $signed({1'b0, popcount4(event_in & W_POS)})
              - $signed({1'b0, popcount4(event_in & W_NEG)});
        if (|event_in) begin
            mem_next = mem + drive;
        end else if (mem > LEAK) begin
            mem_next = mem - LEAK;
        end else begin
            mem_next = '0;
        end
    end

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            mem <= '0;
            spike <= 1'b0;
        end else if (event_valid) begin
            if (mem_next >= THRESHOLD) begin
                mem <= '0;
                spike <= 1'b1;
            end else if (mem_next < 0) begin
                mem <= '0;
                spike <= 1'b0;
            end else begin
                mem <= mem_next;
                spike <= 1'b0;
            end
        end
    end
endmodule
