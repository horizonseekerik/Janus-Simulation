// ==============================================================================
// PROJECT JANUS MINI (16-TILE): JIR FAULT INJECTION CAMPAIGN TESTBENCH
// ==============================================================================
// Directly addresses Red-Team Findings #1, #2, #3, #22, #23, #24, #41, #42.
//
// Verification Methodology:
//   - NON-CIRCULAR: Redundant residues originate from independent encoder channels
//     driven directly from in_X and delayed by 8 cycles (matching CRT tree latency).
//   - Transaction-Synchronized Fault Injection:
//     Fault injection tags travel through pipeline registers with exact delay-matching
//     so each vector experiences deterministic, isolated fault conditions:
//       Phase 1: Healthy Baseline traffic (0 faults, fault_detected=0, id=0)
//       Phase 2: Compute Channel Fault (r3 corrupted -> CRT output corrupted)
//                Both redundant checks mismatch -> fault_detected=1, id=5'd1 (Compute)
//       Phase 3: Redundant Channel 0 Fault (r_red0 corrupted)
//                Only red0 mismatches -> fault_detected=1, id=5'd16 (Red0)
//       Phase 4: Redundant Channel 1 Fault (r_red1 corrupted)
//                Only red1 mismatches -> fault_detected=1, id=5'd17 (Red1)
//       Phase 5: Fault Clearance and Recovery
//                Clean vectors immediately follow and verify recovery to id=0.
// ==============================================================================

`timescale 1ps / 1ps

module tb_jir_fault_injection;

    reg         clk;
    reg         rst_n;
    reg         in_valid;
    reg  [63:0] in_X;

    // Transaction-level injection flags driven at input
    reg         tx_inject_compute;
    reg         tx_inject_red0;
    reg         tx_inject_red1;
    reg  [4:0]  tx_expected_fid;

    // 100 GHz simulation clock: period = 10 ps (toggle every 5 ps)
    always #5 clk = ~clk;

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
    // 2. Independent Redundant Encoders (4 Stages)
    // --------------------------------------------------------------------------
    localparam [8:0] RED_M0 = 9'd173;
    localparam [8:0] RED_M1 = 9'd169;

    wire       red0_valid_raw;
    wire [7:0] red0_r_raw;
    wire       red1_valid_raw;
    wire [7:0] red1_r_raw;

    rns_channel_encoder #(.MOD(RED_M0)) u_enc_red0 (
        .clk(clk),
        .rst_n(rst_n),
        .in_valid(in_valid),
        .in_X(in_X),
        .out_valid(red0_valid_raw),
        .out_r(red0_r_raw)
    );

    rns_channel_encoder #(.MOD(RED_M1)) u_enc_red1 (
        .clk(clk),
        .rst_n(rst_n),
        .in_valid(in_valid),
        .in_X(in_X),
        .out_valid(red1_valid_raw),
        .out_r(red1_r_raw)
    );

    // --------------------------------------------------------------------------
    // 3. Pipeline delay lines for Fault Injection Tags
    // --------------------------------------------------------------------------
    // Delay compute injection tag by 4 cycles to match rns_encoder output
    reg [3:0] comp_fault_pipe;
    // Delay redundant injection tags by 12 cycles (4 enc + 8 delay) to match JIR input
    reg [11:0] red0_fault_pipe;
    reg [11:0] red1_fault_pipe;
    integer p;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            comp_fault_pipe <= 4'b0;
            red0_fault_pipe <= 12'b0;
            red1_fault_pipe <= 12'b0;
        end else begin
            comp_fault_pipe <= {comp_fault_pipe[2:0], tx_inject_compute};
            red0_fault_pipe <= {red0_fault_pipe[10:0], tx_inject_red0};
            red1_fault_pipe <= {red1_fault_pipe[10:0], tx_inject_red1};
        end
    end

    // Compute residue r3 corruption
    wire [7:0] r3_into_crt = (comp_fault_pipe[3]) ? (r3 ^ 8'h01) : r3;

    // --------------------------------------------------------------------------
    // 4. Compute Path: 8-Stage CRT Adder Tree
    // --------------------------------------------------------------------------
    wire        crt_valid;
    wire [63:0] crt_out_X;

    crt_adder_tree u_crt_tree (
        .clk(clk),
        .rst_n(rst_n),
        .in_valid(enc_valid),
        .in_r0(r0),   .in_r1(r1),   .in_r2(r2),   .in_r3(r3_into_crt),
        .in_r4(r4),   .in_r5(r5),   .in_r6(r6),   .in_r7(r7),
        .in_r8(r8),   .in_r9(r9),   .in_r10(r10), .in_r11(r11),
        .in_r12(r12), .in_r13(r13), .in_r14(r14), .in_r15(r15),
        .out_valid(crt_valid),
        .out_X(crt_out_X)
    );

    // --------------------------------------------------------------------------
    // 5. 8-Stage Delay Alignment for Redundant Residues
    // --------------------------------------------------------------------------
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

    // Redundant residue corruption entering JIR
    wire [7:0] jir_red0_in = (red0_fault_pipe[11]) ? (red0_delay[7] ^ 8'h55) : red0_delay[7];
    wire [7:0] jir_red1_in = (red1_fault_pipe[11]) ? (red1_delay[7] ^ 8'hAA) : red1_delay[7];

    // --------------------------------------------------------------------------
    // 6. JIR Parity Fault Monitor
    // --------------------------------------------------------------------------
    wire       fault_detected;
    wire [4:0] fault_channel_id;

    jir_fault_monitor u_jir_monitor (
        .clk(clk),
        .rst_n(rst_n),
        .in_valid(crt_valid),
        .in_reconstructed_X(crt_out_X),
        .in_redundant_r0(jir_red0_in),
        .in_redundant_r1(jir_red1_in),
        .fault_detected(fault_detected),
        .fault_channel_id(fault_channel_id)
    );

    // Scoreboard for JIR tracking:
    // Total latency: 4 enc + 8 CRT + 4 JIR-enc + 1 reg = 17 cycles (0 to 16 index)
    reg        sb_valid_q    [0:16];
    reg [4:0]  sb_exp_fid_q  [0:16];
    reg        sb_exp_det_q  [0:16];

    integer errors = 0;
    integer passed = 0;
    integer v_count = 0;
    integer v_idx;
    integer sb_idx;

    task drive_vector(input [63:0] val, input [4:0] expected_fid, input f_comp, input f_red0, input f_red1);
        begin
            @(negedge clk);
            in_valid          <= 1'b1;
            in_X              <= val;
            tx_inject_compute <= f_comp;
            tx_inject_red0    <= f_red0;
            tx_inject_red1    <= f_red1;
            tx_expected_fid   <= expected_fid;
            v_count           <= v_count + 1;
        end
    endtask

    task drive_idle();
        begin
            @(negedge clk);
            in_valid          <= 1'b0;
            in_X              <= 64'd0;
            tx_inject_compute <= 1'b0;
            tx_inject_red0    <= 1'b0;
            tx_inject_red1    <= 1'b0;
            tx_expected_fid   <= 5'd0;
        end
    endtask

    initial begin
        $display("======================================================================");
        $display("JANUS MINI: JIR FAULT INJECTION CAMPAIGN TESTBENCH (SFA MATRIX)");
        $display("======================================================================");

        clk = 0;
        rst_n = 0;
        in_valid = 0;
        in_X = 0;
        tx_inject_compute = 1'b0;
        tx_inject_red0 = 1'b0;
        tx_inject_red1 = 1'b0;
        tx_expected_fid = 5'd0;

        for (v_idx = 0; v_idx <= 16; v_idx = v_idx + 1) begin
            sb_valid_q[v_idx]   = 1'b0;
            sb_exp_fid_q[v_idx] = 5'd0;
            sb_exp_det_q[v_idx] = 1'b0;
        end

        #20;
        @(negedge clk);
        rst_n = 1;
        #10;

        // ----------------------------------------------------------------------
        // PHASE 1: Healthy Baseline Traffic (Expect ID=0, Detected=0)
        // ----------------------------------------------------------------------
        $display("[+] Phase 1: Injecting Healthy Baseline Traffic...");
        for (v_idx = 0; v_idx < 15; v_idx = v_idx + 1) begin
            drive_vector(64'h1000 + v_idx, 5'd0, 1'b0, 1'b0, 1'b0);
        end

        // ----------------------------------------------------------------------
        // PHASE 2: Primary Compute Tile Fault (Corrupt r3)
        // Expect: fault_detected=1, fault_channel_id=5'd1
        // ----------------------------------------------------------------------
        $display("[+] Phase 2: Injecting Compute Tile Error (Bit flip on r3)...");
        for (v_idx = 0; v_idx < 15; v_idx = v_idx + 1) begin
            drive_vector(64'h2000 + v_idx, 5'd1, 1'b1, 1'b0, 1'b0);
        end

        // ----------------------------------------------------------------------
        // PHASE 3: Redundant Modulus 0 Fault (Corrupt red0 input to JIR)
        // Expect: fault_detected=1, fault_channel_id=5'd16
        // ----------------------------------------------------------------------
        $display("[+] Phase 3: Injecting Redundant Channel 0 Error...");
        for (v_idx = 0; v_idx < 15; v_idx = v_idx + 1) begin
            drive_vector(64'h3000 + v_idx, 5'd16, 1'b0, 1'b1, 1'b0);
        end

        // ----------------------------------------------------------------------
        // PHASE 4: Redundant Modulus 1 Fault (Corrupt red1 input to JIR)
        // Expect: fault_detected=1, fault_channel_id=5'd17
        // ----------------------------------------------------------------------
        $display("[+] Phase 4: Injecting Redundant Channel 1 Error...");
        for (v_idx = 0; v_idx < 15; v_idx = v_idx + 1) begin
            drive_vector(64'h4000 + v_idx, 5'd17, 1'b0, 1'b0, 1'b1);
        end

        // ----------------------------------------------------------------------
        // PHASE 5: Fault Clearance & Healthy Recovery
        // Expect: fault_detected=0, fault_channel_id=5'd0
        // ----------------------------------------------------------------------
        $display("[+] Phase 5: Clearing all faults and verifying healthy recovery...");
        for (v_idx = 0; v_idx < 20; v_idx = v_idx + 1) begin
            drive_vector(64'h5000 + v_idx, 5'd0, 1'b0, 1'b0, 1'b0);
        end

        // Drain pipeline
        for (v_idx = 0; v_idx < 30; v_idx = v_idx + 1) begin
            drive_idle();
        end

        $display("----------------------------------------------------------------------");
        $display("JIR CAMPAIGN SUMMARY: Vectors=%0d, Checked=%0d, Errors=%0d", v_count, passed, errors);
        if (errors == 0 && passed == v_count) begin
            $display("[PASS] 100%% Fault Matrix Coverage under Single-Fault Assumption (SFA).");
            $display("[PASS] Compute, Red0, and Red1 faults uniquely diagnosed with zero false alarms.");
        end else begin
            $display("[FAIL] Encountered %0d JIR fault classification errors!", errors);
            $fatal(1, "JIR Fault Injection Campaign failed");
        end
        $display("======================================================================");
        $finish;
    end

    // Scoreboard shifting at posedge clk
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (sb_idx = 0; sb_idx <= 16; sb_idx = sb_idx + 1) begin
                sb_valid_q[sb_idx]   <= 1'b0;
                sb_exp_fid_q[sb_idx] <= 5'd0;
                sb_exp_det_q[sb_idx] <= 1'b0;
            end
        end else begin
            sb_valid_q[0]   <= in_valid;
            sb_exp_fid_q[0] <= tx_expected_fid;
            sb_exp_det_q[0] <= (tx_expected_fid != 5'd0);

            for (sb_idx = 1; sb_idx <= 16; sb_idx = sb_idx + 1) begin
                sb_valid_q[sb_idx]   <= sb_valid_q[sb_idx-1];
                sb_exp_fid_q[sb_idx] <= sb_exp_fid_q[sb_idx-1];
                sb_exp_det_q[sb_idx] <= sb_exp_det_q[sb_idx-1];
            end
        end
    end

    // Verification check at negedge clk (zero race, 17 cycles latency: index 16)
    always @(negedge clk) begin
        if (rst_n) begin
            if (sb_valid_q[16]) begin
                if (fault_detected !== sb_exp_det_q[16] || fault_channel_id !== sb_exp_fid_q[16]) begin
                    $display("[!] Time %0t ps: JIR Fault Mismatch! Got det=%b id=%0d, Expected det=%b id=%0d",
                             $time, fault_detected, fault_channel_id, sb_exp_det_q[16], sb_exp_fid_q[16]);
                    errors = errors + 1;
                end else begin
                    passed = passed + 1;
                end
            end
        end
    end

endmodule
