// FSM detector for ordered motif: channel 0, then channel 1, then channel 2.

module fsm_detector #(
    parameter int TIMEOUT = 6
) (
    input  logic       clk,
    input  logic       rst_n,
    input  logic       event_valid,
    input  logic [3:0] event_in,
    output logic       detected
);
    typedef enum logic [1:0] {
        WAIT_CH0,
        WAIT_CH1,
        WAIT_CH2,
        DONE
    } state_t;

    state_t state;
    logic [$clog2(TIMEOUT+2)-1:0] age;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= WAIT_CH0;
            age <= '0;
            detected <= 1'b0;
        end else if (event_valid) begin
            detected <= 1'b0;

            if (state != WAIT_CH0 && state != DONE) begin
                if (age >= TIMEOUT) begin
                    state <= WAIT_CH0;
                    age <= '0;
                end else begin
                    age <= age + 1'b1;
                end
            end

            unique case (state)
                WAIT_CH0: begin
                    if (event_in[0]) begin
                        state <= WAIT_CH1;
                        age <= '0;
                    end
                end
                WAIT_CH1: begin
                    if (event_in[1]) begin
                        state <= WAIT_CH2;
                        age <= '0;
                    end
                end
                WAIT_CH2: begin
                    if (event_in[2]) begin
                        state <= DONE;
                        detected <= 1'b1;
                    end
                end
                DONE: begin
                    detected <= 1'b1;
                end
            endcase
        end
    end
endmodule
