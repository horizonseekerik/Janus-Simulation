// ==============================================================================
// PROJECT JANUS MINI (16-TILE): COMPILED DIFFUSION ROM MACRO ARCHITECTURE
// ==============================================================================
// Provides ASIC hard macro wrappers with dual-mode semantics:
//   1. Behavioral Simulation Mode (Default):
//      Zero-overhead, cycle-exact precomputed memory arrays initialized via initial blocks.
//   2. Physical ASIC Macro Mode (`ifdef ASIC_HARD_MACRO):
//      Declares (* blackbox *) dense diffusion ROM macros (~0.080 um^2/bit @ 7nm)
//      preventing synthesis tools from expanding ~852 kbit into discrete logic gates.
// ==============================================================================

`timescale 1ps / 1ps

// ------------------------------------------------------------------------------
// 1. CRT Partial-Product ROM Macro (256 words x 136 bits = 34,816 bits / macro)
// ------------------------------------------------------------------------------
`ifdef ASIC_HARD_MACRO
(* blackbox *)
module crt_rom_256x136_macro #(
    parameter integer CHAN_ID = 0
) (
    input  wire         clk,
    input  wire         ce,
    input  wire [7:0]   addr,
    output wire [135:0] dout
);
endmodule
`else
module crt_rom_256x136_macro #(
    parameter integer       CHAN_ID = 0,
    parameter [8:0]         M_VAL   = 9'd256,
    parameter [8:0]         N_VAL   = 9'd63,
    parameter [127:0]       MI_VAL  = 128'd0
) (
    input  wire         clk,
    input  wire         ce,
    input  wire [7:0]   addr,
    output reg  [135:0] dout
);
    reg [135:0] rom_data [0:255];
    integer i;

    initial begin
        for (i = 0; i < 256; i = i + 1) begin
            rom_data[i] = (({8'b0, i[7:0]} * {7'b0, N_VAL}) % {7'b0, M_VAL}) * MI_VAL;
        end
    end

    always @(posedge clk) begin
        if (ce) begin
            dout <= rom_data[addr];
        end
    end
endmodule
`endif


// ------------------------------------------------------------------------------
// 2. RNS Byte Residue Reduction ROM Macro (256 words x 8 bits = 2,048 bits / macro)
// ------------------------------------------------------------------------------
`ifdef ASIC_HARD_MACRO
(* blackbox *)
module rns_rom_256x8_macro #(
    parameter [8:0]   MOD      = 9'd256,
    parameter integer BYTE_IDX = 0
) (
    input  wire        clk,
    input  wire        ce,
    input  wire [7:0]  addr,
    output wire [7:0]  dout
);
endmodule
`else
module rns_rom_256x8_macro #(
    parameter [8:0]   MOD      = 9'd256,
    parameter integer BYTE_IDX = 0
) (
    input  wire        clk,
    input  wire        ce,
    input  wire [7:0]  addr,
    output reg  [7:0]  dout
);
    reg [7:0] rom_table [0:255];
    integer b, k;
    reg [63:0] weight;

    initial begin
        weight = 64'd1;
        for (b = 0; b < BYTE_IDX; b = b + 1) begin
            weight = (weight * 64'd256) % MOD;
        end
        for (b = 0; b < 256; b = b + 1) begin
            rom_table[b] = (b * weight) % MOD;
        end
    end

    always @(posedge clk) begin
        if (ce) begin
            dout <= rom_table[addr];
        end
    end
endmodule
`endif
