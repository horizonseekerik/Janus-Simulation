"""
PROJECT JANUS MINI-16: UNIFIED PHYSICAL MASK LAYER CONSTANTS
=============================================================
Single source-of-truth for ALL GDS II layer numbers, datatypes,
and canonical physical dimensions used by both:
  - generate_cmos_base_gds.py  (65nm CMOS base die)
  - generate_mini16_gds.py     (complete 3D monolithic stack)

Layer number allocation (NO overlaps between strata):
  Range   1 –  29 : Top SiPh / Si3N4 Optical Stratum
  Range  30 –  39 : 3D Inter-Stratum Vertical Interconnects
  Range  40 –  49 : Abstract 65nm CMOS Block Annotations (both GDS files)
  Range 100 – 199 : Physical 65nm LP/GP CMOS Mask Layers
  Layers 190, 199 : Die Perimeter & Metrology (shared by both strata)
"""

# ==============================================================================
# TOP SiPh / Si3N4 OPTICAL STRATUM  (Layers 1-29)
# ==============================================================================
LAYER_SI_CORE         = (1,  0)   # Crystalline Si core (450x220 nm, APD mesa base)
LAYER_SIO2_CLAD       = (2,  0)   # SiO2 Upper Cladding & BOX
LAYER_LITAO3_EO       = (3,  0)   # Thin-Film LiTaO3 Electro-Optic Pockels Modulator
LAYER_SB2S3_AMORPH    = (4,  0)   # Sb2S3 Phase-Change Switch (Amorphous / OFF state)
LAYER_SB2S3_CRYST     = (4,  1)   # Sb2S3 Phase-Change Switch (Crystalline / ON state)
LAYER_SIN_CORE        = (5,  0)   # Low-Loss Si3N4 Core (800x300 nm, 0.1 dB/cm)
LAYER_CU_M1           = (10, 0)   # Cu Metal 1 RF Electrodes & Micro-Heaters
LAYER_CU_M2           = (11, 0)   # Cu Metal 2 Global Power/Clock Mesh
LAYER_APD_GE          = (20, 0)   # Ge Epitaxial Absorption Mesa (SAC2M APD)

# ==============================================================================
# 3D INTER-STRATUM VERTICAL INTERCONNECTS  (Layers 30-39)
# ==============================================================================
LAYER_TDV_PILLAR      = (30, 0)   # Vertical Cu Through-Dielectric Vias (8 um diam)
LAYER_UBM_BUMP        = (31, 0)   # Under-Bump Metallization & Micro-Bumps (50 um pitch)
LAYER_THERMAL_BUF     = (32, 0)   # 250 um SiO2 Monolithic Thermal Buffer Boundary

# ==============================================================================
# ABSTRACT 65nm CMOS BLOCK ANNOTATIONS  (Layers 40-49)
# Architectural floorplan outlines.  No physical mask shapes go on these layers.
# ==============================================================================
LAYER_ARCH_STRONGARM  = (40, 0)   # StrongARM Regenerative Sense-Amp Front-End Block
LAYER_ARCH_DESER      = (41, 0)   # 1:32 Polyphase Deserializer Block
LAYER_ARCH_SIMD       = (42, 0)   # 32-Lane SIMD Wallace-Kogge Array Block
LAYER_ARCH_SRAM       = (43, 0)   # 1.5 MB Dual-LUT Volatile SRAM Block
LAYER_ARCH_ROM        = (44, 0)   # 1.5 MB Central ROM & JIR FSM Block
LAYER_ARCH_ACC160     = (45, 0)   # 160-Bit Binary CSA Accumulator Block
LAYER_ARCH_THERMAL    = (46, 0)   # JIR Thermal Diodes & Delta-Sigma ADC Block

# ==============================================================================
# PHYSICAL 65nm LP/GP CMOS MASK LAYERS  (Layers 100-199)
# Offset by +100 vs. conventional CMOS numbering to avoid collision with the
# optical stratum layers (1-20) when both co-exist in the combined 3D GDS file.
# ==============================================================================
LAYER_NW_DIFF         = (101, 0)  # N-Well & Active Diffusion (P/N OD)
LAYER_POLY_GATE       = (102, 0)  # Polysilicon Gate (65nm drawn Lg)
LAYER_CONTACT         = (106, 0)  # Tungsten Contact Plugs
LAYER_METAL1          = (111, 0)  # Metal 1 Local Interconnect & StrongARM sense nodes
LAYER_VIA1            = (112, 0)  # Via 1 Inter-Metal Plugs & Via-ROM Matrix
LAYER_METAL2          = (121, 0)  # Metal 2 Intra-Tile Signal Routing
LAYER_VIA2            = (122, 0)  # Via 2
LAYER_METAL3          = (131, 0)  # Metal 3 Lane Bus & SIMD Cross-Routing
LAYER_VIA3            = (132, 0)  # Via 3
LAYER_METAL4          = (141, 0)  # Metal 4 SRAM Wordline/Bitline Strapping
LAYER_VIA4            = (142, 0)  # Via 4
LAYER_METAL5          = (151, 0)  # Metal 5 Accumulator & CRT Adder Bus
LAYER_VIA5            = (152, 0)  # Via 5
LAYER_METAL6_CLK      = (161, 0)  # Metal 6 3.125 GHz H-Tree Clock Distribution
LAYER_VIA6            = (162, 0)  # Via 6
LAYER_TOP_METAL_PWR   = (171, 0)  # Top Thick Metal VDD/VSS Power Grid
LAYER_PASSIVATION_UBM = (181, 0)  # Passivation Opening & UBM Landing Pads
LAYER_PAD_IO          = (182, 0)  # Wire-Bond & Solder Bump I/O Pads

# ==============================================================================
# DIE PERIMETER & METROLOGY  (Shared; no collision since no optical/CMOS overlap)
# ==============================================================================
LAYER_SEAL_RING       = (190, 0)  # 4-Layer Moisture Barrier Chip Seal Ring
LAYER_FLOORPLAN       = (199, 0)  # Die Boundary & Tile Keep-Out Margins

# ==============================================================================
# CANONICAL PHYSICAL DIMENSIONS  (micrometers, consistent across both scripts)
# ==============================================================================
# --- Die geometry ---
DIE_WIDTH_UM          = 3200.0    # 3.20 mm (identical for both strata)
DIE_HEIGHT_UM         = 3200.0    # 3.20 mm (identical for both strata)

# --- Tile array geometry (4x4 = 16 tiles) ---
TILE_CORE_UM          = 600.0     # 600 um x 600 um core active area per tile
TILE_PITCH_UM         = 700.0     # 700 um center-to-center pitch (100 um inter-tile gap)
TILE_ARRAY_ORIGIN_X   = 200.0     # X position of tile[row=0,col=0] bottom-left corner
TILE_ARRAY_ORIGIN_Y   = 200.0     # Y position of tile[row=0,col=0] bottom-left corner

# --- Optical waveguide dimensions ---
SIN_WIDTH_UM          = 0.800     # 800 nm Si3N4 strip width (ultra-low-loss)
SI_WIDTH_UM           = 0.450     # 450 nm crystalline Si strip width
COUPLER_LEN_UM        = 8.400     # 8.4 um Sb2S3 directional coupler coupling length
COUPLER_GAP_UM        = 0.200     # 200 nm coupling gap
PATCH_LEN_UM          = 8.000     # 8.0 um active Sb2S3 patch length
PATCH_WIDTH_UM        = 0.800     # 800 nm patch width (matches Si3N4 core)
MMI_W_UM              = 2.400     # 2.4 um Si3N4 Talbot MMI multimode width
MMI_L_UM              = 5.800     # 5.8 um self-imaging center length
MMI_TAPER_UM          = 6.000     # 6.0 um MMI access taper length
LITAO3_LEN_UM         = 120.0     # 120 um LiTaO3 modulator active region length
LITAO3_W_UM           = 2.000     # 2.0 um LiTaO3 waveguide rib width

# --- Photodetector & 3D interconnect ---
APD_LEN_UM            = 10.00     # 10 um Ge absorption mesa length
APD_W_UM              = 1.200     # 1.2 um Ge mesa width
TDV_DIAMETER_UM       = 8.000     # 8 um Cu-pillar via diameter
TDV_UBM_OVERHANG_UM   = 1.500     # UBM pad extends 1.5 um beyond TDV radius per side
BUMP_PITCH_UM         = 50.00     # 50 um micro-bump pitch

# --- Grating coupler (2nd-order Si3N4 coupler at operating wavelength) ---
WAVELENGTH_NM         = 1310.0    # 1310 nm operating wavelength (Ge APD absorption peak)
GC_TEETH_PERIOD_UM    = 0.630     # 630 nm grating period (2nd-order Si3N4 at 1310 nm)
GC_DUTY_CYCLE         = 0.500     # 50% duty cycle
GC_NUM_TEETH          = 22        # Number of grating teeth per coupler
GC_BODY_LEN_UM        = 35.0      # Grating coupler total body length
GC_HALF_WIDTH_UM      = 6.0       # Half-width of grating aperture

# --- I/O pad geometry ---
PAD_SIZE_UM           = 75.0      # 75 um square pad size
PAD_PITCH_UM          = 120.0     # 120 um center-to-center pad pitch

# --- Power distribution ---
PWR_RING_WIDTH_UM     = 40.0      # Global VDD/VSS power ring width
PWR_RING_OFFSET_UM    = 60.0      # Distance of power ring from die edge
