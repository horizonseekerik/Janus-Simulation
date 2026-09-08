// ==============================================================================
// PROJECT JANUS MINI (16-TILE): STANDALONE CRT ADDER TREE TESTBENCH
// ==============================================================================
// Rigorously verifies the 8-stage 140-bit CRT Adder Tree (Algorithm 4B)
// independently of the RNS encoder.
// Feeds externally computed residues directly into the CRT tree and checks
// exact 64-bit integer reconstruction:
//   r_i = X mod m_i -> CRT Tree -> X_reconstructed == X
//
// Timing & Verification:
//   - Negedge-driven test vectors, posedge-shifted scoreboards
//   - Negedge sampling for race-free verification
//   - Exact 8-cycle pipeline latency assertion
//   - Strict pass check (passed == total_vectors && errors == 0)
//   - Interspersed bubbles and pipeline flushes
// ==============================================================================

`timescale 1ps / 1ps

module tb_crt_standalone;

    reg         clk;
    reg         rst_n;
    reg         in_valid;
    reg  [7:0]  r0,  r1,  r2,  r3;
    reg  [7:0]  r4,  r5,  r6,  r7;
    reg  [7:0]  r8,  r9,  r10, r11;
    reg  [7:0]  r12, r13, r14, r15;

    wire        out_valid;
    wire [63:0] out_X;

    // Moduli Constants
    localparam [8:0] M0  = 9'd256;
    localparam [8:0] M1  = 9'd251;
    localparam [8:0] M2  = 9'd243;
    localparam [8:0] M3  = 9'd241;
    localparam [8:0] M4  = 9'd239;
    localparam [8:0] M5  = 9'd233;
    localparam [8:0] M6  = 9'd229;
    localparam [8:0] M7  = 9'd227;
    localparam [8:0] M8  = 9'd223;
    localparam [8:0] M9  = 9'd211;
    localparam [8:0] M10 = 9'd199;
    localparam [8:0] M11 = 9'd197;
    localparam [8:0] M12 = 9'd193;
    localparam [8:0] M13 = 9'd191;
    localparam [8:0] M14 = 9'd181;
    localparam [8:0] M15 = 9'd179;

    // 100 GHz simulation clock: period = 10 ps (toggle every 5 ps)
    always #5 clk = ~clk;

    crt_adder_tree dut (
        .clk(clk),
        .rst_n(rst_n),
        .in_valid(in_valid),
        .in_r0(r0),   .in_r1(r1),   .in_r2(r2),   .in_r3(r3),
        .in_r4(r4),   .in_r5(r5),   .in_r6(r6),   .in_r7(r7),
        .in_r8(r8),   .in_r9(r9),   .in_r10(r10), .in_r11(r11),
        .in_r12(r12), .in_r13(r13), .in_r14(r14), .in_r15(r15),
        .out_valid(out_valid),
        .out_X(out_X)
    );

    // Scoreboard queues (8 stages latency: index 0..7)
    reg        exp_valid_q [0:7];
    reg [63:0] exp_X_q     [0:7];

    integer errors = 0;
    integer passed = 0;
    integer total_vectors = 0;
    integer v_idx;
    integer sb_idx;
    reg [63:0] test_val;

    task drive_vector(input [63:0] val);
        begin
            @(negedge clk);
            in_valid <= 1'b1;
            r0  <= val[7:0];
            r1  <= val % M1;
            r2  <= val % M2;
            r3  <= val % M3;
            r4  <= val % M4;
            r5  <= val % M5;
            r6  <= val % M6;
            r7  <= val % M7;
            r8  <= val % M8;
            r9  <= val % M9;
            r10 <= val % M10;
            r11 <= val % M11;
            r12 <= val % M12;
            r13 <= val % M13;
            r14 <= val % M14;
            r15 <= val % M15;
            // Record expected 64-bit value at input
            exp_drive_val <= val;
            total_vectors = total_vectors + 1;
        end
    endtask

    reg [63:0] exp_drive_val;

    task drive_bubble();
        begin
            @(negedge clk);
            in_valid <= 1'b0;
            r0  <= 8'd0; r1  <= 8'd0; r2  <= 8'd0; r3  <= 8'd0;
            r4  <= 8'd0; r5  <= 8'd0; r6  <= 8'd0; r7  <= 8'd0;
            r8  <= 8'd0; r9  <= 8'd0; r10 <= 8'd0; r11 <= 8'd0;
            r12 <= 8'd0; r13 <= 8'd0; r14 <= 8'd0; r15 <= 8'd0;
            exp_drive_val <= 64'd0;
        end
    endtask

    initial begin
        $display("======================================================================");
        $display("JANUS MINI: STANDALONE CRT ADDER TREE VERIFICATION (ALGORITHM 4B)");
        $display("======================================================================");

        clk = 0;
        rst_n = 0;
        in_valid = 0;
        exp_drive_val = 0;
        r0 = 0; r1 = 0; r2 = 0; r3 = 0; r4 = 0; r5 = 0; r6 = 0; r7 = 0;
        r8 = 0; r9 = 0; r10 = 0; r11 = 0; r12 = 0; r13 = 0; r14 = 0; r15 = 0;

        for (v_idx = 0; v_idx <= 7; v_idx = v_idx + 1) begin
            exp_valid_q[v_idx] = 0;
            exp_X_q[v_idx] = 0;
        end

        #20;
        @(negedge clk);
        rst_n = 1;
        #10;

        // 1. Boundary & Corner Cases
        drive_vector(64'd0);
        drive_vector(64'd1);
        drive_vector(64'd255);
        drive_vector(64'd256);
        drive_vector(64'd65535);
        drive_vector(64'd123456789);
        drive_vector(64'd9876543210123);
        drive_vector(64'h00000000FFFFFFFF);
        drive_vector(64'hAAAAAAAAAAAAAAAA);
        drive_vector(64'h5555555555555555);
        drive_vector(64'h123456789ABCDEF0);
        drive_vector(64'hFEDCBA9876543210);
        drive_vector(64'h7FFFFFFFFFFFFFFF);
        drive_vector(64'hFFFFFFFFFFFFFFFF);

        // 2. Interspersed Bubbles
        drive_bubble();
        drive_bubble();

        // 3. 100 Random 64-bit Vectors
        for (v_idx = 0; v_idx < 100; v_idx = v_idx + 1) begin
            test_val = {$random, $random};
            drive_vector(test_val);
            if (v_idx % 6 == 0) begin
                drive_bubble();
            end
        end

        // Drain pipeline (8 stages + margin)
        drive_bubble();
        drive_bubble();
        drive_bubble();
        drive_bubble();
        drive_bubble();
        drive_bubble();
        drive_bubble();
        drive_bubble();
        drive_bubble();

        $display("----------------------------------------------------------------------");
        $display("CRT TREE RESULTS: Total Vectors=%0d, Passed=%0d, Errors=%0d", total_vectors, passed, errors);
        if (errors == 0 && passed == total_vectors) begin
            $display("[PASS] 100%% Bit-Exact 64-Bit CRT Reconstruction from external residues.");
            $display("[PASS] Exact 8-cycle pipeline latency verified.");
        end else begin
            $display("[FAIL] Encountered %0d mismatches in CRT tree!", errors);
            $fatal(1, "CRT Standalone verification failed");
        end
        $display("======================================================================");
        $finish;
    end

    // Scoreboard shifted at posedge clk
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (sb_idx = 0; sb_idx <= 7; sb_idx = sb_idx + 1) begin
                exp_valid_q[sb_idx] <= 1'b0;
                exp_X_q[sb_idx]     <= 64'd0;
            end
        end else begin
            exp_valid_q[0] <= in_valid;
            exp_X_q[0]     <= exp_drive_val;
            for (sb_idx = 1; sb_idx <= 7; sb_idx = sb_idx + 1) begin
                exp_valid_q[sb_idx] <= exp_valid_q[sb_idx-1];
                exp_X_q[sb_idx]     <= exp_X_q[sb_idx-1];
            end
        end
    end

    // Verification check at negedge clk (zero race)
    always @(negedge clk) begin
        if (rst_n) begin
            // Stage 7 of scoreboard corresponds to 8th stage output of CRT tree (0-indexed)
            if (out_valid !== exp_valid_q[7]) begin
                $display("[!] Cycle %0t ps: CRT Valid mismatch! Got %b, Expected %b", $time, out_valid, exp_valid_q[7]);
                errors = errors + 1;
            end

            if (out_valid && exp_valid_q[7]) begin
                if (out_X === exp_X_q[7]) begin
                    passed = passed + 1;
                end else begin
                    $display("[!] Cycle %0t ps: CRT MISMATCH! Got 0x%16h, Expected 0x%16h", $time, out_X, exp_X_q[7]);
                    errors = errors + 1;
                end
            end
        end
    end

endmodule
