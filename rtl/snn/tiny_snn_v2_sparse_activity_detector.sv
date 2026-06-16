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
    logic [2:0] hidden_membrane_0;
    logic [2:0] hidden_membrane_1;
    logic [2:0] hidden_membrane_2;
    logic [2:0] hidden_membrane_3;
    logic [2:0] hidden_membrane_4;
    logic [2:0] hidden_membrane_5;
    logic [2:0] next_hidden_membrane_0;
    logic [2:0] next_hidden_membrane_1;
    logic [2:0] next_hidden_membrane_2;
    logic [2:0] next_hidden_membrane_3;
    logic [2:0] next_hidden_membrane_4;
    logic [2:0] next_hidden_membrane_5;
    logic [2:0] output_membrane;
    logic [2:0] next_output_membrane;
    logic hidden_spike_0;
    logic hidden_spike_1;
    logic hidden_spike_2;
    logic hidden_spike_3;
    logic hidden_spike_4;
    logic hidden_spike_5;
    logic next_prediction;

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

    function automatic logic [3:0] update_drive_n3(input logic [2:0] membrane);
        begin
            case (membrane)
                3'd5: update_drive_n3 = {1'b0, 3'd1};
                3'd6: update_drive_n3 = {1'b0, 3'd2};
                3'd7: update_drive_n3 = {1'b0, 3'd3};
                default: update_drive_n3 = 4'd0;
            endcase
        end
    endfunction

    function automatic logic [3:0] update_drive_n2(input logic [2:0] membrane);
        begin
            case (membrane)
                3'd4: update_drive_n2 = {1'b0, 3'd1};
                3'd5: update_drive_n2 = {1'b0, 3'd2};
                3'd6: update_drive_n2 = {1'b0, 3'd3};
                3'd7: update_drive_n2 = {1'b1, 3'd0};
                default: update_drive_n2 = 4'd0;
            endcase
        end
    endfunction

    function automatic logic [3:0] update_drive_n1(input logic [2:0] membrane);
        begin
            case (membrane)
                3'd3: update_drive_n1 = {1'b0, 3'd1};
                3'd4: update_drive_n1 = {1'b0, 3'd2};
                3'd5: update_drive_n1 = {1'b0, 3'd3};
                3'd6, 3'd7: update_drive_n1 = {1'b1, 3'd0};
                default: update_drive_n1 = 4'd0;
            endcase
        end
    endfunction

    function automatic logic [3:0] update_drive_p0(input logic [2:0] membrane);
        begin
            case (membrane)
                3'd2: update_drive_p0 = {1'b0, 3'd1};
                3'd3: update_drive_p0 = {1'b0, 3'd2};
                3'd4: update_drive_p0 = {1'b0, 3'd3};
                3'd5, 3'd6, 3'd7: update_drive_p0 = {1'b1, 3'd0};
                default: update_drive_p0 = 4'd0;
            endcase
        end
    endfunction

    function automatic logic [3:0] update_drive_p1(input logic [2:0] membrane);
        begin
            if (membrane[2]) begin
                update_drive_p1 = 4'b1000;
            end else if (membrane[1]) begin
                update_drive_p1 = {1'b0, 2'b01, membrane[0]};
            end else begin
                update_drive_p1 = 4'b0001;
            end
        end
    endfunction

    function automatic logic [3:0] update_drive_p2(input logic [2:0] membrane);
        begin
            if (membrane[2] | (membrane[1] & membrane[0])) begin
                update_drive_p2 = 4'b1000;
            end else if (membrane[1]) begin
                update_drive_p2 = 4'b0011;
            end else begin
                update_drive_p2 = 4'b0010;
            end
        end
    endfunction

    function automatic logic [3:0] update_drive_p3(input logic [2:0] membrane);
        begin
            if (membrane[2] | membrane[1]) begin
                update_drive_p3 = 4'b1000;
            end else begin
                update_drive_p3 = 4'b0011;
            end
        end
    endfunction

    function automatic logic [3:0] hidden_update_0(input logic [2:0] membrane, input logic [INPUT_WIDTH-1:0] bits);
        begin
            if (bits[0]) begin
                hidden_update_0 = bits[3] ? update_drive_p3(membrane) : 4'b1000;
            end else begin
                hidden_update_0 = bits[3] ? update_drive_n1(membrane) : update_drive_p0(membrane);
            end
        end
    endfunction

    function automatic logic [3:0] hidden_update_1(input logic [2:0] membrane, input logic [INPUT_WIDTH-1:0] bits);
        begin
            if (bits[1]) begin
                hidden_update_1 = bits[3] ? update_drive_p2(membrane) : update_drive_p3(membrane);
            end else begin
                hidden_update_1 = bits[3] ? update_drive_n1(membrane) : update_drive_p0(membrane);
            end
        end
    endfunction

    function automatic logic [3:0] hidden_update_2(input logic [2:0] membrane, input logic [INPUT_WIDTH-1:0] bits);
        begin
            if (bits[2]) begin
                hidden_update_2 = bits[3] ? update_drive_p3(membrane) : 4'b1000;
            end else begin
                hidden_update_2 = bits[3] ? update_drive_n1(membrane) : update_drive_p0(membrane);
            end
        end
    endfunction

    function automatic logic [3:0] hidden_update_3(input logic [2:0] membrane, input logic [INPUT_WIDTH-1:0] bits);
        begin
            if (bits[3]) begin
                if (&bits[2:0]) begin
                    hidden_update_3 = update_drive_p3(membrane);
                end else begin
                    hidden_update_3 = 4'b1000;
                end
            end else begin
                case (bits[2:0])
                    3'b000: hidden_update_3 = update_drive_p0(membrane);
                    3'b001, 3'b010, 3'b100: hidden_update_3 = update_drive_n1(membrane);
                    3'b011, 3'b101, 3'b110: hidden_update_3 = update_drive_n2(membrane);
                    default: hidden_update_3 = update_drive_n3(membrane);
                endcase
            end
        end
    endfunction

    function automatic logic [3:0] hidden_update_4(input logic [2:0] membrane, input logic [INPUT_WIDTH-1:0] bits);
        begin
            if (bits[3]) begin
                case ({bits[1], bits[0]})
                    2'b00: hidden_update_4 = update_drive_n1(membrane);
                    2'b01, 2'b10: hidden_update_4 = update_drive_p1(membrane);
                    default: hidden_update_4 = update_drive_p3(membrane);
                endcase
            end else begin
                case ({bits[1], bits[0]})
                    2'b00: hidden_update_4 = update_drive_p0(membrane);
                    2'b01, 2'b10: hidden_update_4 = update_drive_p2(membrane);
                    default: hidden_update_4 = 4'b1000;
                endcase
            end
        end
    endfunction

    function automatic logic [3:0] hidden_update_5(input logic [2:0] membrane, input logic [INPUT_WIDTH-1:0] bits);
        begin
            if (bits[3]) begin
                case ({bits[2], bits[1]})
                    2'b00: hidden_update_5 = update_drive_n1(membrane);
                    2'b01, 2'b10: hidden_update_5 = update_drive_p1(membrane);
                    default: hidden_update_5 = update_drive_p3(membrane);
                endcase
            end else begin
                case ({bits[2], bits[1]})
                    2'b00: hidden_update_5 = update_drive_p0(membrane);
                    2'b01, 2'b10: hidden_update_5 = update_drive_p2(membrane);
                    default: hidden_update_5 = 4'b1000;
                endcase
            end
        end
    endfunction

    function automatic calc_t output_drive(
        input logic spike0,
        input logic spike2,
        input logic spike3,
        input logic spike4,
        input logic spike5
    );
        begin
            output_drive = (spike0 ? OW_N0 : 5'sd0)
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
        next_output_membrane = 3'd0;
        next_prediction = prediction;
        next_hidden_membrane_0 = 3'd0;
        next_hidden_membrane_1 = 3'd0;
        next_hidden_membrane_2 = 3'd0;
        next_hidden_membrane_3 = 3'd0;
        next_hidden_membrane_4 = 3'd0;
        next_hidden_membrane_5 = 3'd0;
        hidden_spike_0 = 1'b0;
        hidden_spike_1 = 1'b0;
        hidden_spike_2 = 1'b0;
        hidden_spike_3 = 1'b0;
        hidden_spike_4 = 1'b0;
        hidden_spike_5 = 1'b0;

        if (sample_valid) begin
            output_value = calc_t'(clip_membrane(calc_t'(output_membrane) - 5'sd1));
            update = hidden_update_0(hidden_membrane_0, sample_bits);
            hidden_spike_0 = update[3];
            next_hidden_membrane_0 = update[2:0];
            update = hidden_update_1(hidden_membrane_1, sample_bits);
            hidden_spike_1 = update[3];
            next_hidden_membrane_1 = update[2:0];
            update = hidden_update_2(hidden_membrane_2, sample_bits);
            hidden_spike_2 = update[3];
            next_hidden_membrane_2 = update[2:0];
            update = hidden_update_3(hidden_membrane_3, sample_bits);
            hidden_spike_3 = update[3];
            next_hidden_membrane_3 = update[2:0];
            update = hidden_update_4(hidden_membrane_4, sample_bits);
            hidden_spike_4 = update[3];
            next_hidden_membrane_4 = update[2:0];
            update = hidden_update_5(hidden_membrane_5, sample_bits);
            hidden_spike_5 = update[3];
            next_hidden_membrane_5 = update[2:0];

            drive = output_drive(
                hidden_spike_0,
                hidden_spike_2,
                hidden_spike_3,
                hidden_spike_4,
                hidden_spike_5
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
            hidden_membrane_0 <= '0;
            hidden_membrane_1 <= '0;
            hidden_membrane_2 <= '0;
            hidden_membrane_3 <= '0;
            hidden_membrane_4 <= '0;
            hidden_membrane_5 <= '0;
        end else begin
            done <= 1'b0;
            if (start) begin
                sample_count <= '0;
                output_membrane <= '0;
                prediction <= 1'b0;
                hidden_membrane_0 <= '0;
                hidden_membrane_1 <= '0;
                hidden_membrane_2 <= '0;
                hidden_membrane_3 <= '0;
                hidden_membrane_4 <= '0;
                hidden_membrane_5 <= '0;
            end else if (sample_valid) begin
                output_membrane <= next_output_membrane;
                prediction <= next_prediction;
                hidden_membrane_0 <= next_hidden_membrane_0;
                hidden_membrane_1 <= next_hidden_membrane_1;
                hidden_membrane_2 <= next_hidden_membrane_2;
                hidden_membrane_3 <= next_hidden_membrane_3;
                hidden_membrane_4 <= next_hidden_membrane_4;
                hidden_membrane_5 <= next_hidden_membrane_5;
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
