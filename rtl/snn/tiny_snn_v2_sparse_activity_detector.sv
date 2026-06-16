module tiny_snn_v2_sparse_activity_detector #(
    parameter int INPUT_WIDTH = 4,
    parameter int SEQ_LEN = 40
) (
    input  logic                   clk,
    input  logic                   rst_n,
    input  logic                   start,
    input  logic                   sample_valid,
    input  logic [INPUT_WIDTH-1:0] sample_bits,
    output logic                   done,
    output logic                   prediction
);
    localparam int HIDDEN_NEURONS = 6;
    localparam int HIDDEN_THRESHOLD = 4;
    localparam int OUTPUT_THRESHOLD = 3;
    localparam int LEAK = 1;
    localparam int MEMBRANE_MIN = 0;
    localparam int MEMBRANE_MAX = 7;
    localparam int SAMPLE_COUNT_WIDTH = (SEQ_LEN <= 1) ? 1 : $clog2(SEQ_LEN);
    typedef logic signed [4:0] calc_t;

    localparam calc_t W_C0_N0 = 5'sd4;
    localparam calc_t W_C0_N3 = -5'sd1;
    localparam calc_t W_C0_N4 = 5'sd2;
    localparam calc_t W_C1_N1 = 5'sd3;
    localparam calc_t W_C1_N3 = -5'sd1;
    localparam calc_t W_C1_N4 = 5'sd2;
    localparam calc_t W_C1_N5 = 5'sd2;
    localparam calc_t W_C2_N2 = 5'sd4;
    localparam calc_t W_C2_N3 = -5'sd1;
    localparam calc_t W_C2_N5 = 5'sd2;
    localparam calc_t W_C3_N0 = -5'sd1;
    localparam calc_t W_C3_N1 = -5'sd1;
    localparam calc_t W_C3_N2 = -5'sd1;
    localparam calc_t W_C3_N3 = 5'sd6;
    localparam calc_t W_C3_N4 = -5'sd1;
    localparam calc_t W_C3_N5 = -5'sd1;
    localparam calc_t OW_N0 = -5'sd1;
    localparam calc_t OW_N1 = 5'sd0;
    localparam calc_t OW_N2 = 5'sd1;
    localparam calc_t OW_N3 = -5'sd2;
    localparam calc_t OW_N4 = 5'sd1;
    localparam calc_t OW_N5 = 5'sd1;

    logic [SAMPLE_COUNT_WIDTH-1:0] sample_count;
    logic [2:0] hidden_membrane [0:HIDDEN_NEURONS-1];
    logic [2:0] next_hidden_membrane [0:HIDDEN_NEURONS-1];
    logic [2:0] output_membrane;
    logic [2:0] next_output_membrane;
    logic hidden_spike [0:HIDDEN_NEURONS-1];
    logic next_prediction;

    function automatic calc_t hidden_drive_0(input logic [INPUT_WIDTH-1:0] bits);
        begin
            hidden_drive_0 = (bits[0] ? W_C0_N0 : 5'sd0) + (bits[3] ? W_C3_N0 : 5'sd0);
        end
    endfunction

    function automatic calc_t hidden_drive_1(input logic [INPUT_WIDTH-1:0] bits);
        begin
            hidden_drive_1 = (bits[1] ? W_C1_N1 : 5'sd0) + (bits[3] ? W_C3_N1 : 5'sd0);
        end
    endfunction

    function automatic calc_t hidden_drive_2(input logic [INPUT_WIDTH-1:0] bits);
        begin
            hidden_drive_2 = (bits[2] ? W_C2_N2 : 5'sd0) + (bits[3] ? W_C3_N2 : 5'sd0);
        end
    endfunction

    function automatic calc_t hidden_drive_3(input logic [INPUT_WIDTH-1:0] bits);
        begin
            hidden_drive_3 = (bits[0] ? W_C0_N3 : 5'sd0)
                + (bits[1] ? W_C1_N3 : 5'sd0)
                + (bits[2] ? W_C2_N3 : 5'sd0)
                + (bits[3] ? W_C3_N3 : 5'sd0);
        end
    endfunction

    function automatic calc_t hidden_drive_4(input logic [INPUT_WIDTH-1:0] bits);
        begin
            hidden_drive_4 = (bits[0] ? W_C0_N4 : 5'sd0)
                + (bits[1] ? W_C1_N4 : 5'sd0)
                + (bits[3] ? W_C3_N4 : 5'sd0);
        end
    endfunction

    function automatic calc_t hidden_drive_5(input logic [INPUT_WIDTH-1:0] bits);
        begin
            hidden_drive_5 = (bits[1] ? W_C1_N5 : 5'sd0)
                + (bits[2] ? W_C2_N5 : 5'sd0)
                + (bits[3] ? W_C3_N5 : 5'sd0);
        end
    endfunction

    function automatic logic [2:0] clip_membrane(input calc_t value);
        begin
            if (value < 5'sd0) begin
                clip_membrane = 3'd0;
            end else if (value > 5'sd7) begin
                clip_membrane = 3'd7;
            end else begin
                clip_membrane = value[2:0];
            end
        end
    endfunction

    function automatic logic [3:0] hidden_update(input logic [2:0] membrane, input calc_t drive);
        calc_t hidden_value;
        logic [2:0] clipped_value;
        begin
            hidden_value = calc_t'(clip_membrane(calc_t'(membrane) - 5'sd1));
            clipped_value = clip_membrane(hidden_value + drive);
            if (clipped_value >= 3'd4) begin
                hidden_update = {1'b1, 3'd0};
            end else begin
                hidden_update = {1'b0, clipped_value};
            end
        end
    endfunction

    function automatic calc_t output_drive(
        input logic spike0,
        input logic spike1,
        input logic spike2,
        input logic spike3,
        input logic spike4,
        input logic spike5
    );
        begin
            output_drive = (spike0 ? OW_N0 : 5'sd0)
                + (spike1 ? OW_N1 : 5'sd0)
                + (spike2 ? OW_N2 : 5'sd0)
                + (spike3 ? OW_N3 : 5'sd0)
                + (spike4 ? OW_N4 : 5'sd0)
                + (spike5 ? OW_N5 : 5'sd0);
        end
    endfunction

    always_comb begin
        calc_t output_value;
        calc_t drive;
        logic [3:0] update;

        output_value = output_membrane;
        drive = 0;
        update = 4'd0;
        next_output_membrane = output_membrane;
        next_prediction = prediction;
        next_hidden_membrane[0] = hidden_membrane[0];
        next_hidden_membrane[1] = hidden_membrane[1];
        next_hidden_membrane[2] = hidden_membrane[2];
        next_hidden_membrane[3] = hidden_membrane[3];
        next_hidden_membrane[4] = hidden_membrane[4];
        next_hidden_membrane[5] = hidden_membrane[5];
        hidden_spike[0] = 1'b0;
        hidden_spike[1] = 1'b0;
        hidden_spike[2] = 1'b0;
        hidden_spike[3] = 1'b0;
        hidden_spike[4] = 1'b0;
        hidden_spike[5] = 1'b0;

        if (sample_valid) begin
            output_value = calc_t'(clip_membrane(calc_t'(output_membrane) - 5'sd1));
            update = hidden_update(hidden_membrane[0], hidden_drive_0(sample_bits));
            hidden_spike[0] = update[3];
            next_hidden_membrane[0] = update[2:0];
            update = hidden_update(hidden_membrane[1], hidden_drive_1(sample_bits));
            hidden_spike[1] = update[3];
            next_hidden_membrane[1] = update[2:0];
            update = hidden_update(hidden_membrane[2], hidden_drive_2(sample_bits));
            hidden_spike[2] = update[3];
            next_hidden_membrane[2] = update[2:0];
            update = hidden_update(hidden_membrane[3], hidden_drive_3(sample_bits));
            hidden_spike[3] = update[3];
            next_hidden_membrane[3] = update[2:0];
            update = hidden_update(hidden_membrane[4], hidden_drive_4(sample_bits));
            hidden_spike[4] = update[3];
            next_hidden_membrane[4] = update[2:0];
            update = hidden_update(hidden_membrane[5], hidden_drive_5(sample_bits));
            hidden_spike[5] = update[3];
            next_hidden_membrane[5] = update[2:0];

            drive = output_drive(
                hidden_spike[0],
                hidden_spike[1],
                hidden_spike[2],
                hidden_spike[3],
                hidden_spike[4],
                hidden_spike[5]
            );
            next_output_membrane = clip_membrane(output_value + drive);
            if (next_output_membrane >= 3'd3) begin
                next_prediction = 1'b1;
            end
        end
    end

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            sample_count <= '0;
            output_membrane <= '0;
            done <= 1'b0;
            prediction <= 1'b0;
            for (int neuron = 0; neuron < HIDDEN_NEURONS; neuron++) begin
                hidden_membrane[neuron] <= '0;
            end
        end else begin
            done <= 1'b0;
            if (start) begin
                sample_count <= '0;
                output_membrane <= '0;
                prediction <= 1'b0;
                for (int neuron = 0; neuron < HIDDEN_NEURONS; neuron++) begin
                    hidden_membrane[neuron] <= '0;
                end
            end else if (sample_valid) begin
                output_membrane <= next_output_membrane;
                prediction <= next_prediction;
                for (int neuron = 0; neuron < HIDDEN_NEURONS; neuron++) begin
                    hidden_membrane[neuron] <= next_hidden_membrane[neuron];
                end
                if (sample_count == SEQ_LEN - 1) begin
                    done <= 1'b1;
                    sample_count <= '0;
                end else begin
                    sample_count <= sample_count + 1'b1;
                end
            end
        end
    end
endmodule
