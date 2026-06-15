module threshold_detector #(
    parameter int INPUT_WIDTH = 4,
    parameter int SEQ_LEN = 40,
    parameter int MIN_ACTIVE_CYCLES = 3,
    parameter int MIN_TOTAL_SPIKES = 3
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
    localparam int ACTIVE_COUNT_WIDTH = $clog2(SEQ_LEN + 1);
    localparam int SPIKE_COUNT_WIDTH = $clog2((SEQ_LEN * INPUT_WIDTH) + 1);

    logic [SAMPLE_COUNT_WIDTH-1:0] sample_count;
    logic [ACTIVE_COUNT_WIDTH-1:0] active_cycles;
    logic [SPIKE_COUNT_WIDTH-1:0] total_spikes;
    integer sample_spikes;

    always_comb begin
        sample_spikes = 0;
        for (int bit_index = 0; bit_index < INPUT_WIDTH; bit_index++) begin
            sample_spikes = sample_spikes + sample_bits[bit_index];
        end
    end

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            sample_count <= '0;
            active_cycles <= '0;
            total_spikes <= '0;
            done <= 1'b0;
            prediction <= 1'b0;
        end else begin
            done <= 1'b0;
            if (start) begin
                sample_count <= '0;
                active_cycles <= '0;
                total_spikes <= '0;
                prediction <= 1'b0;
            end else if (sample_valid) begin
                if (sample_count == SEQ_LEN - 1) begin
                    prediction <= ((active_cycles + (|sample_bits)) >= MIN_ACTIVE_CYCLES)
                               && ((total_spikes + sample_spikes) >= MIN_TOTAL_SPIKES);
                    done <= 1'b1;
                    sample_count <= '0;
                end else begin
                    sample_count <= sample_count + 1'b1;
                end
                active_cycles <= active_cycles + (|sample_bits);
                total_spikes <= total_spikes + sample_spikes;
            end
        end
    end
endmodule
