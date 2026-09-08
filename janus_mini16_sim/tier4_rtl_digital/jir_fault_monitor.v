// ==============================================================================
// PROJECT JANUS MINI (16-TILE): JIR FAULT MONITOR
// ==============================================================================
// Monitors terminal StrongARM latch outputs for RRNS parity mismatches.
// Uses a 4-stage pipelined residue generator for RED_M0 (173) and RED_M1 (169).
// Target clock TBD — depends on synthesis results for chosen technology node
// Priority-encodes failing channels (5'd1=Compute, 5'd16=Red0, 5'd17=Red1).
// ==============================================================================

`timescale 1ps / 1ps

module jir_fault_monitor (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        in_valid,
    input  wire [63:0] in_reconstructed_X,
    input  wire [7:0]  in_redundant_r0,
    input  wire [7:0]  in_redundant_r1,
    output reg         fault_detected,
    output reg  [4:0]  fault_channel_id
);

`include "janus_moduli_params.vh"

    // Pipelined residue calculation for redundant moduli
    wire       red0_valid;
    wire [7:0] exp_r0;
    wire       red1_valid;
    wire [7:0] exp_r1;

    rns_channel_encoder #(.MOD(RED_M0)) u_enc_red0 (
        .clk(clk),
        .rst_n(rst_n),
        .in_valid(in_valid),
        .in_X(in_reconstructed_X),
        .out_valid(red0_valid),
        .out_r(exp_r0)
    );

    rns_channel_encoder #(.MOD(RED_M1)) u_enc_red1 (
        .clk(clk),
        .rst_n(rst_n),
        .in_valid(in_valid),
        .in_X(in_reconstructed_X),
        .out_valid(red1_valid),
        .out_r(exp_r1)
    );

    // Delay match incoming redundant residues through 4 pipeline stages
    reg [7:0] r0_d1, r0_d2, r0_d3, r0_d4;
    reg [7:0] r1_d1, r1_d2, r1_d3, r1_d4;
    reg [3:0] in_valid_pipe;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            r0_d1 <= 8'd0; r0_d2 <= 8'd0; r0_d3 <= 8'd0; r0_d4 <= 8'd0;
            r1_d1 <= 8'd0; r1_d2 <= 8'd0; r1_d3 <= 8'd0; r1_d4 <= 8'd0;
            in_valid_pipe    <= 4'b0;
            fault_detected   <= 1'b0;
            fault_channel_id <= FID_HEALTHY;
        end else begin
            in_valid_pipe <= {in_valid_pipe[2:0], in_valid};

            r0_d1 <= in_redundant_r0;
            r0_d2 <= r0_d1;
            r0_d3 <= r0_d2;
            r0_d4 <= r0_d3;

            r1_d1 <= in_redundant_r1;
            r1_d2 <= r1_d1;
            r1_d3 <= r1_d2;
            r1_d4 <= r1_d3;

            // Single-Fault Assumption (SFA) Diagnostic Logic & Multi-Fault Classification:
            // - If both redundant channels disagree with reconstructed X: primary compute tile / CRT error (FID_COMPUTE_TILE = 5'd1)
            // - If only red0 disagrees: redundant channel 0 parity fault (FID_RED0_PARITY = 5'd16)
            // - If only red1 disagrees: redundant channel 1 parity fault (FID_RED1_PARITY = 5'd17)
            // - If valid pipeline diverges: protocol / sync fault (FID_PROTOCOL_SYNC = 5'd30)
            // - If expected valid is dropped on both redundant channels: multiple-fault syndrome (FID_MULTI_FAULT = 5'd31)
            if (red0_valid && red1_valid) begin
                if ((exp_r0 != r0_d4) && (exp_r1 != r1_d4)) begin
                    fault_detected   <= 1'b1;
                    fault_channel_id <= FID_COMPUTE_TILE;  // Both mismatch: Primary compute tile / CRT error (SFA)
                end else if ((exp_r0 != r0_d4) && (exp_r1 == r1_d4)) begin
                    fault_detected   <= 1'b1;
                    fault_channel_id <= FID_RED0_PARITY;   // Redundant Modulus 0 error
                end else if ((exp_r0 == r0_d4) && (exp_r1 != r1_d4)) begin
                    fault_detected   <= 1'b1;
                    fault_channel_id <= FID_RED1_PARITY;   // Redundant Modulus 1 error
                end else begin
                    fault_detected   <= 1'b0;
                    fault_channel_id <= FID_HEALTHY;       // No fault detected
                end
            end else if (red0_valid != red1_valid) begin
                fault_detected   <= 1'b1;
                fault_channel_id <= FID_PROTOCOL_SYNC;     // Protocol / pipeline synchronization error
            end else if (in_valid_pipe[3] && !red0_valid && !red1_valid) begin
                fault_detected   <= 1'b1;
                fault_channel_id <= FID_MULTI_FAULT;       // Multi-fault: dual redundant channel drop
            end else begin
                fault_detected   <= 1'b0;
                fault_channel_id <= FID_HEALTHY;
            end
        end
    end

endmodule
