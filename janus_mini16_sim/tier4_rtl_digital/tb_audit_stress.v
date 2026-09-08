// ==============================================================================
// PROJECT JANUS MINI (16-TILE): AUDIT STRESS TESTBENCH (1000 VECTORS)
// ==============================================================================
// Directly addresses Red-Team Findings #1, #6, #7, #8, #42, #44, #46, #48.
//
// Verification Methodology:
//   - NON-CIRCULAR: Redundant residues originate independently from in_X and are
//     delay-matched through 8 pipeline stages to arrive synchronized with out_X.
//   - Zero-Race Scoreboard: Driven at negedge clk, shifted at posedge clk,
//     and checked at negedge clk.
//   - Full valid/data queue tracking across 12-cycle pipeline depth.
//   - Fixed deterministic PRNG seed logged for 100% reproducibility.
//   - Strict pass requirement: exactly 1000 vectors checked with 0 errors.
//   - Fatal error on mismatch for automated CI integration.
// ==============================================================================

`timescale 1ps / 1ps

module tb_audit_stress;

    reg         clk;
    reg         rst_n;
    reg         in_valid;
    reg  [63:0] in_X;

    wire        enc_valid;
    wire [7:0]  r0,  r1,  r2,  r3,  r4,  r5,  r6,  r7;
    wire [7:0]  r8,  r9,  r10, r11, r12, r13, r14, r15;

    wire        crt_valid;
    wire [63:0] out_X;

    wire        fault_detected;
    wire [4:0]  fault_channel_id;

    // 100 GHz simulation clock: period = 10 ps (toggle every 5 ps)
    always #5 clk = ~clk;

    // 1. Compute Path: 16-Channel 4-Stage Pipelined Encoder
    rns_encoder u_encoder (
        .clk(clk), .rst_n(rst_n), .in_valid(in_valid), .in_X(in_X),
        .out_valid(enc_valid),
        .out_r0(r0),   .out_r1(r1),   .out_r2(r2),   .out_r3(r3),
        .out_r4(r4),   .out_r5(r5),   .out_r6(r6),   .out_r7(r7),
        .out_r8(r8),   .out_r9(r9),   .out_r10(r10), .out_r11(r11),
        .out_r12(r12), .out_r13(r13), .out_r14(r14), .out_r15(r15)
    );

    // 2. Independent Redundant Encoders (4 Stages, directly from in_X)
    localparam [8:0] RED_M0 = 9'd173;
    localparam [8:0] RED_M1 = 9'd169;

    wire       red0_valid_raw;
    wire [7:0] red0_r_raw;
    wire       red1_valid_raw;
    wire [7:0] red1_r_raw;

    rns_channel_encoder #(.MOD(RED_M0)) u_enc_red0 (
        .clk(clk), .rst_n(rst_n), .in_valid(in_valid), .in_X(in_X),
        .out_valid(red0_valid_raw), .out_r(red0_r_raw)
    );

    rns_channel_encoder #(.MOD(RED_M1)) u_enc_red1 (
        .clk(clk), .rst_n(rst_n), .in_valid(in_valid), .in_X(in_X),
        .out_valid(red1_valid_raw), .out_r(red1_r_raw)
    );

    // 3. Compute Path: 8-Stage CRT Adder Tree
    crt_adder_tree u_crt_tree (
        .clk(clk), .rst_n(rst_n), .in_valid(enc_valid),
        .in_r0(r0),   .in_r1(r1),   .in_r2(r2),   .in_r3(r3),
        .in_r4(r4),   .in_r5(r5),   .in_r6(r6),   .in_r7(r7),
        .in_r8(r8),   .in_r9(r9),   .in_r10(r10), .in_r11(r11),
        .in_r12(r12), .in_r13(r13), .in_r14(r14), .in_r15(r15),
        .out_valid(crt_valid),
        .out_X(out_X)
    );

    // 4. Delay Matching: 8 Stages for Redundant Residues
    reg [7:0] red0_delay [0:7];
    reg [7:0] red1_delay [0:7];
    integer d_idx;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (d_idx = 0; d_idx < 8; d_idx = d_idx + 1) begin
                red0_delay[d_idx] <= 8'd0;
                red1_delay[d_idx] <= 8'd0;
            end
        end else begin
            red0_delay[0] <= red0_r_raw;
            red1_delay[0] <= red1_r_raw;
            for (d_idx = 1; d_idx < 8; d_idx = d_idx + 1) begin
                red0_delay[d_idx] <= red0_delay[d_idx-1];
                red1_delay[d_idx] <= red1_delay[d_idx-1];
            end
        end
    end

    // 5. JIR Parity Fault Monitor (NON-CIRCULAR: fed with independent delayed residues)
    jir_fault_monitor u_fault_mon (
        .clk(clk), .rst_n(rst_n), .in_valid(crt_valid),
        .in_reconstructed_X(out_X),
        .in_redundant_r0(red0_delay[7]),
        .in_redundant_r1(red1_delay[7]),
        .fault_detected(fault_detected),
        .fault_channel_id(fault_channel_id)
    );

    // Scoreboard queues (Exact 12 cycles latency: index 0..11)
    reg        sb_valid_q [0:11];
    reg [63:0] sb_data_q  [0:11];

    integer v_idx;
    integer sb_idx;
    integer passed = 0;
    integer errors = 0;
    reg [63:0] rand_val;
    reg [63:0] exp_drive_val;

    // Seed for reproducible verification
    integer seed = 32'h1A2B3C4D;

    initial begin
        $display("======================================================================");
        $display("JANUS MINI: 1000-VECTOR AUDIT STRESS TESTBENCH");
        $display("Reproducible PRNG Seed: 0x%08h", seed);
        $display("======================================================================");

        clk = 0;
        rst_n = 0;
        in_valid = 0;
        in_X = 0;
        exp_drive_val = 0;
        passed = 0;
        errors = 0;

        for (sb_idx = 0; sb_idx <= 11; sb_idx = sb_idx + 1) begin
            sb_valid_q[sb_idx] = 1'b0;
            sb_data_q[sb_idx]  = 64'd0;
        end

        #20;
        @(negedge clk);
        rst_n = 1;
        #10;

        // Feed exactly 1000 randomized 64-bit vectors with clean negedge timing
        for (v_idx = 0; v_idx < 1000; v_idx = v_idx + 1) begin
            @(negedge clk);
            in_valid <= 1'b1;
            rand_val = {$random(seed), $random(seed)};
            in_X          <= rand_val;
            exp_drive_val <= rand_val;
        end

        // Pipeline drain
        for (v_idx = 0; v_idx < 20; v_idx = v_idx + 1) begin
            @(negedge clk);
            in_valid <= 1'b0;
            in_X     <= 64'd0;
            exp_drive_val <= 64'd0;
        end

        $display("----------------------------------------------------------------------");
        $display("STRESS AUDIT RESULTS: Passed=%0d, Errors=%0d", passed, errors);
        if (errors == 0 && passed == 1000) begin
            $display("[AUDIT_PASS] 1000/1000 random vectors passed bit-exact with 0 errors!");
            $display("[AUDIT_PASS] Pipelined Latency: 12 clock cycles confirmed.");
        end else begin
            $display("[AUDIT_FAIL] Passed=%0d, Errors=%0d (Expected 1000)", passed, errors);
            $fatal(1, "Audit stress test failed");
        end
        $display("======================================================================");
        $finish;
    end

    // Shift scoreboard at posedge clk
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (sb_idx = 0; sb_idx <= 11; sb_idx = sb_idx + 1) begin
                sb_valid_q[sb_idx] <= 1'b0;
                sb_data_q[sb_idx]  <= 64'd0;
            end
        end else begin
            sb_valid_q[0] <= in_valid;
            sb_data_q[0]  <= exp_drive_val;
            for (sb_idx = 1; sb_idx <= 11; sb_idx = sb_idx + 1) begin
                sb_valid_q[sb_idx] <= sb_valid_q[sb_idx-1];
                sb_data_q[sb_idx]  <= sb_data_q[sb_idx-1];
            end
        end
    end

    // Verify output at negedge clk (zero race, 12 cycles latency: index 11)
    always @(negedge clk) begin
        if (rst_n) begin
            if (crt_valid !== sb_valid_q[11]) begin
                $display("[!] Cycle %0t ps: Valid mismatch! Got %b, Expected %b", $time, crt_valid, sb_valid_q[11]);
                errors = errors + 1;
            end

            if (crt_valid && sb_valid_q[11]) begin
                if (out_X === sb_data_q[11]) begin
                    passed = passed + 1;
                end else begin
                    errors = errors + 1;
                    $display("[!] Error at time %0t: Got 0x%16h, Expected 0x%16h", $time, out_X, sb_data_q[11]);
                end
            end
        end
    end

endmodule
