// ==============================================================================
// PROJECT JANUS MINI (16-TILE): INTEGRATED DIGITAL CORE TOP (TIER 4)
// ==============================================================================
// Integrates:
//   1. 16-Channel 4-Stage Pipelined RNS Encoder (Algorithm 4A)
//   2. Independent Redundant Modulo Encoders (RED_M0=173, RED_M1=169)
//   3. 8-Stage Delay Alignment Pipeline for Redundant Channels
//   4. 8-Stage 140-bit Pipelined CRT Adder Tree (Algorithm 4B)
//   5. JIR Parity Fault Monitor with Single-Fault Assumption (SFA) Diagnostics
//
// Pipeline Latencies:
//   - in_X -> out_X: 12 clock cycles (4 enc + 8 CRT)
//   - in_X -> fault_detected: 17 clock cycles (4 enc + 8 CRT + 4 JIR-enc + 1 reg)
// ==============================================================================

`timescale 1ps / 1ps

module janus_tier4_top (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        in_valid,
    input  wire [63:0] in_X,
    output wire        out_valid,
    output wire [63:0] out_X,
    output wire        fault_detected,
    output wire [4:0]  fault_channel_id
);

    // --------------------------------------------------------------------------
    // 1. Compute Path: 16-Channel RNS Modulo Encoder (4 Stages)
    // --------------------------------------------------------------------------
    wire        enc_valid;
    wire [7:0]  r0,  r1,  r2,  r3;
    wire [7:0]  r4,  r5,  r6,  r7;
    wire [7:0]  r8,  r9,  r10, r11;
    wire [7:0]  r12, r13, r14, r15;

    rns_encoder u_compute_encoder (
        .clk(clk),
        .rst_n(rst_n),
        .in_valid(in_valid),
        .in_X(in_X),
        .out_valid(enc_valid),
        .out_r0(r0),   .out_r1(r1),   .out_r2(r2),   .out_r3(r3),
        .out_r4(r4),   .out_r5(r5),   .out_r6(r6),   .out_r7(r7),
        .out_r8(r8),   .out_r9(r9),   .out_r10(r10), .out_r11(r11),
        .out_r12(r12), .out_r13(r13), .out_r14(r14), .out_r15(r15)
    );

    // --------------------------------------------------------------------------
    // 2. Independent Redundant Paths: Generated directly from in_X (4 Stages)
    // --------------------------------------------------------------------------
    localparam [8:0] RED_M0 = 9'd173;
    localparam [8:0] RED_M1 = 9'd169;

    wire       red0_valid_raw;
    wire [7:0] red0_r_raw;
    wire       red1_valid_raw;
    wire [7:0] red1_r_raw;

    rns_channel_encoder #(.MOD(RED_M0)) u_enc_red0_indep (
        .clk(clk),
        .rst_n(rst_n),
        .in_valid(in_valid),
        .in_X(in_X),
        .out_valid(red0_valid_raw),
        .out_r(red0_r_raw)
    );

    rns_channel_encoder #(.MOD(RED_M1)) u_enc_red1_indep (
        .clk(clk),
        .rst_n(rst_n),
        .in_valid(in_valid),
        .in_X(in_X),
        .out_valid(red1_valid_raw),
        .out_r(red1_r_raw)
    );

    // --------------------------------------------------------------------------
    // 3. Compute Path: 8-Stage Pipelined CRT Adder Tree
    // --------------------------------------------------------------------------
    wire        crt_valid;
    wire [63:0] crt_out_X;

    crt_adder_tree u_crt_adder_tree (
        .clk(clk),
        .rst_n(rst_n),
        .in_valid(enc_valid),
        .in_r0(r0),   .in_r1(r1),   .in_r2(r2),   .in_r3(r3),
        .in_r4(r4),   .in_r5(r5),   .in_r6(r6),   .in_r7(r7),
        .in_r8(r8),   .in_r9(r9),   .in_r10(r10), .in_r11(r11),
        .in_r12(r12), .in_r13(r13), .in_r14(r14), .in_r15(r15),
        .out_valid(crt_valid),
        .out_X(crt_out_X)
    );

    assign out_valid = crt_valid;
    assign out_X     = crt_out_X;

    // --------------------------------------------------------------------------
    // 4. Delay Matching: 8 Stages for Redundant Residues to align with CRT latency
    // --------------------------------------------------------------------------
    reg [7:0] red0_delay [0:7];
    reg [7:0] red1_delay [0:7];
    integer d;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (d = 0; d < 8; d = d + 1) begin
                red0_delay[d] <= 8'd0;
                red1_delay[d] <= 8'd0;
            end
        end else begin
            red0_delay[0] <= red0_r_raw;
            red1_delay[0] <= red1_r_raw;
            for (d = 1; d < 8; d = d + 1) begin
                red0_delay[d] <= red0_delay[d-1];
                red1_delay[d] <= red1_delay[d-1];
            end
        end
    end

    // --------------------------------------------------------------------------
    // 5. JIR Parity Fault Monitor
    // --------------------------------------------------------------------------
    jir_fault_monitor u_jir_monitor (
        .clk(clk),
        .rst_n(rst_n),
        .in_valid(crt_valid),
        .in_reconstructed_X(crt_out_X),
        .in_redundant_r0(red0_delay[7]),
        .in_redundant_r1(red1_delay[7]),
        .fault_detected(fault_detected),
        .fault_channel_id(fault_channel_id)
    );

endmodule
