// ==============================================================================
// PROJECT JANUS MINI (16-TILE): STANDALONE RNS ENCODER TESTBENCH
// ==============================================================================
// Rigorously verifies the 16-channel RNS Modulo Encoder (Algorithm 4A)
// independently of the downstream CRT tree.
// Checks all 16 residue outputs against the reference mathematical modulo:
//   r_i = X mod m_i for i in [0..15]
//
// Timing Convention:
//   - Driven at negedge clk (stable setup before posedge)
//   - Sampled and verified at negedge clk (stable hold after posedge)
//   - Cycle-exact 4.0 clock cycle latency check
// ==============================================================================

`timescale 1ps / 1ps

module tb_rns_standalone;

    reg         clk;
    reg         rst_n;
    reg         in_valid;
    reg  [63:0] in_X;

    wire        out_valid;
    wire [7:0]  r0,  r1,  r2,  r3;
    wire [7:0]  r4,  r5,  r6,  r7;
    wire [7:0]  r8,  r9,  r10, r11;
    wire [7:0]  r12, r13, r14, r15;

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

    rns_encoder dut (
        .clk(clk),
        .rst_n(rst_n),
        .in_valid(in_valid),
        .in_X(in_X),
        .out_valid(out_valid),
        .out_r0(r0),   .out_r1(r1),   .out_r2(r2),   .out_r3(r3),
        .out_r4(r4),   .out_r5(r5),   .out_r6(r6),   .out_r7(r7),
        .out_r8(r8),   .out_r9(r9),   .out_r10(r10), .out_r11(r11),
        .out_r12(r12), .out_r13(r13), .out_r14(r14), .out_r15(r15)
    );

    // Scoreboard queues: 4-stage pipeline
    // Q[0] is driven at negedge cycle 0, arrives at output at negedge cycle 4
    reg        exp_valid_q [0:4];
    reg [63:0] exp_X_q     [0:4];

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
            in_X     <= val;
            total_vectors = total_vectors + 1;
        end
    endtask

    task drive_bubble();
        begin
            @(negedge clk);
            in_valid <= 1'b0;
            in_X     <= 64'd0;
        end
    endtask

    initial begin
        $display("======================================================================");
        $display("JANUS MINI: STANDALONE RNS ENCODER VERIFICATION (ALGORITHM 4A)");
        $display("======================================================================");

        clk = 0;
        rst_n = 0;
        in_valid = 0;
        in_X = 0;

        for (v_idx = 0; v_idx <= 4; v_idx = v_idx + 1) begin
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
        drive_vector(64'h00000000FFFFFFFF);
        drive_vector(64'hAAAAAAAAAAAAAAAA);
        drive_vector(64'h5555555555555555);
        drive_vector(64'h7FFFFFFFFFFFFFFF);
        drive_vector(64'hFFFFFFFFFFFFFFFF);
        drive_vector(64'd9876543210123);

        // 2. Introduce Bubbles to test pipeline synchronization
        drive_bubble();
        drive_bubble();

        // 3. Random Vectors with interspersed bubbles
        for (v_idx = 0; v_idx < 100; v_idx = v_idx + 1) begin
            test_val = {$random, $random};
            drive_vector(test_val);
            if (v_idx % 7 == 0) begin
                drive_bubble();
            end
        end

        // Drain pipeline
        drive_bubble();
        drive_bubble();
        drive_bubble();
        drive_bubble();
        drive_bubble();

        $display("----------------------------------------------------------------------");
        $display("RNS ENCODER RESULTS: Total Vectors=%0d, Passed=%0d, Errors=%0d", total_vectors, passed, errors);
        if (errors == 0 && passed == total_vectors) begin
            $display("[PASS] 100%% Bit-Exact Modulo Reduction across all 16 channels.");
            $display("[PASS] Exact 4-cycle pipeline latency verified.");
        end else begin
            $display("[FAIL] Encountered %0d mismatches in RNS encoder!", errors);
            $fatal(1, "RNS Standalone verification failed");
        end
        $display("======================================================================");
        $finish;
    end

    // Scoreboard shifting at posedge clk (perfectly tracking DUT pipeline stages)
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (sb_idx = 0; sb_idx <= 4; sb_idx = sb_idx + 1) begin
                exp_valid_q[sb_idx] <= 1'b0;
                exp_X_q[sb_idx]     <= 64'd0;
            end
        end else begin
            exp_valid_q[0] <= in_valid;
            exp_X_q[0]     <= in_X;
            for (sb_idx = 1; sb_idx <= 4; sb_idx = sb_idx + 1) begin
                exp_valid_q[sb_idx] <= exp_valid_q[sb_idx-1];
                exp_X_q[sb_idx]     <= exp_X_q[sb_idx-1];
            end
        end
    end

    // Verification sampling at negedge clk (zero race, fully settled)
    always @(negedge clk) begin
        if (rst_n) begin
            // Stage 3 of scoreboard matches Stage 4 output of DUT (0-indexed: 0, 1, 2, 3)
            if (out_valid !== exp_valid_q[3]) begin
                $display("[!] Cycle %0t ps: Valid mismatch! Got %b, Expected %b", $time, out_valid, exp_valid_q[3]);
                errors = errors + 1;
            end

            if (out_valid && exp_valid_q[3]) begin
                check_modulus(0,  r0,  M0,  exp_X_q[3]);
                check_modulus(1,  r1,  M1,  exp_X_q[3]);
                check_modulus(2,  r2,  M2,  exp_X_q[3]);
                check_modulus(3,  r3,  M3,  exp_X_q[3]);
                check_modulus(4,  r4,  M4,  exp_X_q[3]);
                check_modulus(5,  r5,  M5,  exp_X_q[3]);
                check_modulus(6,  r6,  M6,  exp_X_q[3]);
                check_modulus(7,  r7,  M7,  exp_X_q[3]);
                check_modulus(8,  r8,  M8,  exp_X_q[3]);
                check_modulus(9,  r9,  M9,  exp_X_q[3]);
                check_modulus(10, r10, M10, exp_X_q[3]);
                check_modulus(11, r11, M11, exp_X_q[3]);
                check_modulus(12, r12, M12, exp_X_q[3]);
                check_modulus(13, r13, M13, exp_X_q[3]);
                check_modulus(14, r14, M14, exp_X_q[3]);
                check_modulus(15, r15, M15, exp_X_q[3]);
                passed = passed + 1;
            end
        end
    end

    task check_modulus(input integer ch, input [7:0] got, input [8:0] mod_val, input [63:0] orig_X);
        reg [7:0] exp_res;
        begin
            exp_res = (mod_val == 9'd256) ? orig_X[7:0] : (orig_X % mod_val);
            if (got !== exp_res) begin
                $display("[!] Ch %0d mismatch for X=0x%16h: Got %0d, Expected %0d (mod %0d)",
                         ch, orig_X, got, exp_res, mod_val);
                errors = errors + 1;
            end
        end
    endtask

endmodule
