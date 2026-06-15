module lut_like_detector #(
    parameter int INPUT_WIDTH = 4,
    parameter int SEQ_LEN = 40,
    parameter int MAX_TOTAL_SPIKES = 10
) (
    input  logic                   clk,
    input  logic                   rst_n,
    input  logic                   start,
    input  logic                   sample_valid,
    input  logic [INPUT_WIDTH-1:0] sample_bits,
    output logic                   done,
    output logic                   prediction
);
    localparam int SAMPLE_COUNT_WIDTH = (SEQ_LEN <= 1) ? 1 : $clog2(SEQ_LEN);
    localparam int SPIKE_COUNT_WIDTH = $clog2((SEQ_LEN * INPUT_WIDTH) + 1);

    logic [SAMPLE_COUNT_WIDTH-1:0] sample_count;
    logic [2:0] seen;
    logic order_ok;
    logic [SPIKE_COUNT_WIDTH-1:0] total_spikes;
    logic [2:0] next_seen;
    logic next_order_ok;
    integer sample_spikes;

    always_comb begin
        sample_spikes = 0;
        for (int bit_index = 0; bit_index < INPUT_WIDTH; bit_index++) begin
            sample_spikes = sample_spikes + sample_bits[bit_index];
        end
        next_seen = seen | sample_bits[2:0];
        next_order_ok = order_ok;
        if (!seen[1] && sample_bits[1] && !seen[0]) begin
            next_order_ok = 1'b0;
        end
        if (!seen[2] && sample_bits[2] && !(seen[1] && order_ok)) begin
            next_order_ok = 1'b0;
        end
    end

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            sample_count <= '0;
            seen <= '0;
            order_ok <= 1'b1;
            total_spikes <= '0;
            done <= 1'b0;
            prediction <= 1'b0;
        end else begin
            done <= 1'b0;
            if (start) begin
                sample_count <= '0;
                seen <= '0;
                order_ok <= 1'b1;
                total_spikes <= '0;
                prediction <= 1'b0;
            end else if (sample_valid) begin
                seen <= next_seen;
                order_ok <= next_order_ok;
                total_spikes <= total_spikes + sample_spikes;
                if (sample_count == SEQ_LEN - 1) begin
                    prediction <= (&next_seen) && next_order_ok
                               && ((total_spikes + sample_spikes) <= MAX_TOTAL_SPIKES);
                    done <= 1'b1;
                    sample_count <= '0;
                end else begin
                    sample_count <= sample_count + 1'b1;
                end
            end
        end
    end
endmodule
