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

    logic [SAMPLE_COUNT_WIDTH-1:0] sample_count;
    logic signed [7:0] hidden_membrane [0:HIDDEN_NEURONS-1];
    logic signed [7:0] next_hidden_membrane [0:HIDDEN_NEURONS-1];
    logic signed [7:0] output_membrane;
    logic signed [7:0] next_output_membrane;
    logic hidden_spike [0:HIDDEN_NEURONS-1];
    logic next_prediction;

    function automatic int input_weight(input int channel, input int neuron);
        begin
            input_weight = 0;
            case (channel)
                0: begin
                    case (neuron)
                        0: input_weight = 4;
                        3: input_weight = -1;
                        4: input_weight = 2;
                        default: input_weight = 0;
                    endcase
                end
                1: begin
                    case (neuron)
                        1: input_weight = 3;
                        3: input_weight = -1;
                        4: input_weight = 2;
                        5: input_weight = 2;
                        default: input_weight = 0;
                    endcase
                end
                2: begin
                    case (neuron)
                        2: input_weight = 4;
                        3: input_weight = -1;
                        5: input_weight = 2;
                        default: input_weight = 0;
                    endcase
                end
                3: begin
                    case (neuron)
                        0: input_weight = -1;
                        1: input_weight = -1;
                        2: input_weight = -1;
                        3: input_weight = 6;
                        4: input_weight = -1;
                        5: input_weight = -1;
                        default: input_weight = 0;
                    endcase
                end
                default: input_weight = 0;
            endcase
        end
    endfunction

    function automatic int output_weight(input int neuron);
        begin
            case (neuron)
                0: output_weight = -1;
                1: output_weight = 0;
                2: output_weight = 1;
                3: output_weight = -2;
                4: output_weight = 1;
                5: output_weight = 1;
                default: output_weight = 0;
            endcase
        end
    endfunction

    function automatic logic signed [7:0] clip_membrane(input int value);
        begin
            if (value < MEMBRANE_MIN) begin
                clip_membrane = MEMBRANE_MIN;
            end else if (value > MEMBRANE_MAX) begin
                clip_membrane = MEMBRANE_MAX;
            end else begin
                clip_membrane = value;
            end
        end
    endfunction

    always_comb begin
        int hidden_value;
        int output_value;
        int drive;

        next_output_membrane = output_membrane;
        next_prediction = prediction;
        for (int neuron = 0; neuron < HIDDEN_NEURONS; neuron++) begin
            next_hidden_membrane[neuron] = hidden_membrane[neuron];
            hidden_spike[neuron] = 1'b0;
        end

        if (sample_valid) begin
            output_value = clip_membrane(output_membrane - LEAK);
            for (int neuron = 0; neuron < HIDDEN_NEURONS; neuron++) begin
                hidden_value = clip_membrane(hidden_membrane[neuron] - LEAK);
                drive = 0;
                for (int channel = 0; channel < INPUT_WIDTH; channel++) begin
                    if (sample_bits[channel]) begin
                        drive = drive + input_weight(channel, neuron);
                    end
                end
                hidden_value = clip_membrane(hidden_value + drive);
                if (hidden_value >= HIDDEN_THRESHOLD) begin
                    hidden_spike[neuron] = 1'b1;
                    next_hidden_membrane[neuron] = MEMBRANE_MIN;
                end else begin
                    next_hidden_membrane[neuron] = clip_membrane(hidden_value);
                end
            end

            drive = 0;
            for (int neuron = 0; neuron < HIDDEN_NEURONS; neuron++) begin
                if (hidden_spike[neuron]) begin
                    drive = drive + output_weight(neuron);
                end
            end
            next_output_membrane = clip_membrane(output_value + drive);
            if (next_output_membrane >= OUTPUT_THRESHOLD) begin
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
