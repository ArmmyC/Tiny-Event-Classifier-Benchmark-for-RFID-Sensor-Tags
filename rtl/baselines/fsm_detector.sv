module fsm_detector #(
    parameter int INPUT_WIDTH = 4,
    parameter int SEQ_LEN = 40,
    parameter int MAX_GAP = 6
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
    localparam int GAP_COUNT_WIDTH = $clog2(MAX_GAP + 2);

    logic [SAMPLE_COUNT_WIDTH-1:0] sample_count;
    logic [1:0] progress;
    logic [GAP_COUNT_WIDTH-1:0] gap_count;
    logic motif_found;
    logic [1:0] next_progress;
    logic [GAP_COUNT_WIDTH-1:0] next_gap_count;
    logic next_motif_found;

    always_comb begin
        next_progress = progress;
        next_gap_count = gap_count;
        next_motif_found = motif_found;

        if (!motif_found) begin
            if ((progress != 0) && (gap_count >= MAX_GAP)) begin
                next_progress = 0;
                next_gap_count = 0;
            end else if (progress != 0) begin
                next_gap_count = gap_count + 1'b1;
            end

            case (next_progress)
                0: if (sample_bits[0]) begin
                    next_progress = 1;
                    next_gap_count = 0;
                end
                1: if (sample_bits[1]) begin
                    next_progress = 2;
                    next_gap_count = 0;
                end
                2: if (sample_bits[2]) begin
                    next_progress = 3;
                    next_motif_found = 1'b1;
                end
                default: next_motif_found = 1'b1;
            endcase
        end
    end

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            sample_count <= '0;
            progress <= '0;
            gap_count <= '0;
            motif_found <= 1'b0;
            done <= 1'b0;
            prediction <= 1'b0;
        end else begin
            done <= 1'b0;
            if (start) begin
                sample_count <= '0;
                progress <= '0;
                gap_count <= '0;
                motif_found <= 1'b0;
                prediction <= 1'b0;
            end else if (sample_valid) begin
                progress <= next_progress;
                gap_count <= next_gap_count;
                motif_found <= next_motif_found;
                if (sample_count == SEQ_LEN - 1) begin
                    prediction <= next_motif_found;
                    done <= 1'b1;
                    sample_count <= '0;
                end else begin
                    sample_count <= sample_count + 1'b1;
                end
            end
        end
    end
endmodule
