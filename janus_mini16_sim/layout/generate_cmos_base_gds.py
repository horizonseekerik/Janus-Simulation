"""
PROJECT JANUS MINI-16: 65nm CMOS BASE DIE PHYSICAL GDS II SYNTHESIZER
======================================================================
Target Hardware: JANUS Mini 16-Tile Monolithic MVP (Model 1A)
Foundry Process: Standard 65nm LP/GP CMOS (1P7M to 1P9M)
Operating Freq : 3.125 GHz (320.0 ps clock period, 32-lane SIMD)
Die Dimensions : 3.20 mm x 3.20 mm (1:1 match with SiPh top stratum)

This script synthesizes the standalone 65nm CMOS base die mask layout:
  - StrongARM Regenerative Sensing Latch Array (1:1 vertically under APD TDVs)
  - 1:32 Polyphase Time-Interleaved Deserializers
  - 32-Lane SIMD Wallace-Tree & Kogge-Stone Parallel-Prefix Arithmetic Arrays
  - 1.5 MB Dual-LUT Volatile Local SRAM Slices (48 KB per lane)
  - 1.5 MB Central Non-Volatile ROM & JIR Epoch Sequencer FSM
  - 160-Bit Binary Carry-Save Accumulator (CSA) Blocks
  - JIR Thermal Sensing Diodes & 10-bit Delta-Sigma ADCs
  - UBM Micro-Bump Array (50 um pitch) for 3D Cu TDV Inter-Stratum Bonding
  - Standard Pad Ring (all 4 sides), Power/Ground Mesh, and Scribe Line Metrology

Layer number conventions are defined in janus_layer_constants.py.
Physical CMOS mask layers use the 100-199 range to avoid collision with
optical stratum layers (1-29) in the combined 3D GDS file.
"""

import os
import sys
import shutil
import numpy as np
import gdsfactory as gf

# ---------------------------------------------------------------------------
# Ensure workspace root is on sys.path so the constants module is importable
# whether this script is run directly or imported as a module.
# ---------------------------------------------------------------------------
_ws_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _ws_root not in sys.path:
    sys.path.insert(0, _ws_root)

from janus_mini16_sim.layout.janus_layer_constants import (
    # Physical CMOS mask layers (100-199 range)
    LAYER_NW_DIFF, LAYER_POLY_GATE, LAYER_CONTACT,
    LAYER_METAL1, LAYER_VIA1,
    LAYER_METAL2, LAYER_VIA2,
    LAYER_METAL3, LAYER_VIA3,
    LAYER_METAL4, LAYER_VIA4,
    LAYER_METAL5, LAYER_VIA5,
    LAYER_METAL6_CLK, LAYER_VIA6,
    LAYER_TOP_METAL_PWR,
    LAYER_PASSIVATION_UBM,
    LAYER_PAD_IO,
    # Abstract CMOS architectural annotations (40-49 range)
    LAYER_ARCH_STRONGARM, LAYER_ARCH_DESER, LAYER_ARCH_SIMD,
    LAYER_ARCH_SRAM, LAYER_ARCH_ROM, LAYER_ARCH_ACC160, LAYER_ARCH_THERMAL,
    # Perimeter & metrology
    LAYER_SEAL_RING, LAYER_FLOORPLAN,
    # Canonical physical dimensions
    DIE_WIDTH_UM, DIE_HEIGHT_UM,
    TILE_CORE_UM, TILE_PITCH_UM, TILE_ARRAY_ORIGIN_X, TILE_ARRAY_ORIGIN_Y,
    TDV_DIAMETER_UM, TDV_UBM_OVERHANG_UM,
    PAD_SIZE_UM, PAD_PITCH_UM,
    PWR_RING_WIDTH_UM, PWR_RING_OFFSET_UM,
)

# Activate generic layout environment
gf.gpdk.PDK.activate()


# ==============================================================================
# UTILITY: HTREE SEGMENT HELPER
# ==============================================================================

def _htree_seg(comp, x1, y1, x2, y2, width, layer):
    """Add a single axis-aligned H-tree metal segment as a filled rectangle."""
    if x1 == x2:  # vertical segment
        comp.add_polygon([
            (x1 - width / 2, min(y1, y2)),
            (x1 + width / 2, min(y1, y2)),
            (x1 + width / 2, max(y1, y2)),
            (x1 - width / 2, max(y1, y2)),
        ], layer=layer)
    else:  # horizontal segment
        comp.add_polygon([
            (min(x1, x2), y1 - width / 2),
            (max(x1, x2), y1 - width / 2),
            (max(x1, x2), y1 + width / 2),
            (min(x1, x2), y1 + width / 2),
        ], layer=layer)


def add_balanced_htree_4x4(comp, origin_x, origin_y, pitch, layer):
    """
    Adds a 4-level balanced H-tree clock distribution network that connects
    from the centroid of the 4x4 tile array down to each individual tile center.

    Wire widths taper from 8 um (trunk) down to 3 um (terminal branches) to
    maintain constant RC delay at each level.

    Args:
        comp       : gf.Component to add segments to.
        origin_x   : X of tile[row=0, col=0] bottom-left corner.
        origin_y   : Y of tile[row=0, col=0] bottom-left corner.
        pitch      : Center-to-center tile pitch.
        layer      : GDS layer tuple for clock metal.
    """
    # Tile center positions
    tile_half = TILE_CORE_UM / 2.0
    xs = [origin_x + col * pitch + tile_half for col in range(4)]  # [500,1200,1900,2600]
    ys = [origin_y + row * pitch + tile_half for row in range(4)]  # [500,1200,1900,2600]

    # Quad midpoints
    x_ql = (xs[0] + xs[1]) / 2.0   # Left quad X mid  = 850
    x_qr = (xs[2] + xs[3]) / 2.0   # Right quad X mid = 2250
    y_qb = (ys[0] + ys[1]) / 2.0   # Bottom quad Y mid = 850
    y_qt = (ys[2] + ys[3]) / 2.0   # Top quad Y mid    = 2250

    # H-tree root centroid
    cx = (xs[0] + xs[-1]) / 2.0    # 1550
    cy = (ys[0] + ys[-1]) / 2.0    # 1550

    W = [8.0, 6.0, 4.5, 3.0]       # Wire width per level (trunk → terminal)

    # ---- Level 1: Root horizontal trunk (left quad-center → right quad-center) ----
    _htree_seg(comp, x_ql, cy, x_qr, cy, W[0], layer)

    # ---- Level 2: Vertical branch at each quad X position ----
    for xq in [x_ql, x_qr]:
        _htree_seg(comp, xq, y_qb, xq, y_qt, W[1], layer)

    # ---- Level 3: Horizontal branch at each quadrant corner ----
    for xq, (xa, xb) in [(x_ql, (xs[0], xs[1])), (x_qr, (xs[2], xs[3]))]:
        for yq in [y_qb, y_qt]:
            _htree_seg(comp, xa, yq, xb, yq, W[2], layer)

    # ---- Level 4: Vertical terminal drops to each individual tile center ----
    for xi, x in enumerate(xs):
        yq_parent = y_qb if xi < 2 else None   # xi drives which quad X, ys drive quad Y
        for yi, y in enumerate(ys):
            yq = y_qb if yi < 2 else y_qt
            _htree_seg(comp, x, yq, x, y, W[3], layer)

    comp.add_label(
        "BALANCED_H-TREE_3.125GHz_4-LEVEL",
        position=(cx, cy),
        layer=layer,
    )


# ==============================================================================
# 1. PARAMETRIC CELLS (PCELLS) FOR 65nm DIGITAL CIRCUITS
# ==============================================================================

@gf.cell
def pcell_cmos_strongarm_latch_unit() -> gf.Component:
    """
    Single StrongARM Regenerative Dynamic Latch Cell:
      - Differential cross-coupled inverters (M1-M4)
      - Input differential NMOS pair (M5-M6)
      - Clock tail current source (M7)
      - UBM Micro-Bump pad landing directly on sense node
    Physical CMOS layers: 101/0 (NW_DIFF), 102/0 (POLY_GATE), 106/0 (CONTACT),
                          111/0 (M1), 112/0 (VIA1), 121/0 (M2), 181/0 (UBM).
    """
    c = gf.Component("STRONGARM_LATCH_UNIT")

    # Active Diffusion & Poly Gates
    c.add_polygon([(0, 0), (25.0, 0), (25.0, 18.0), (0, 18.0)], layer=LAYER_NW_DIFF)
    for g in range(4):
        xg = 3.0 + g * 5.5
        c.add_polygon([(xg, -1.0), (xg + 1.2, -1.0), (xg + 1.2, 19.0), (xg, 19.0)],
                      layer=LAYER_POLY_GATE)
        # Tungsten contact plugs on S/D nodes
        c.add_polygon([(xg - 1.2, 3.0), (xg - 0.2, 3.0), (xg - 0.2, 5.0), (xg - 1.2, 5.0)],
                      layer=LAYER_CONTACT)
        c.add_polygon([(xg - 1.2, 12.0), (xg - 0.2, 12.0), (xg - 0.2, 14.0), (xg - 1.2, 14.0)],
                      layer=LAYER_CONTACT)

    # Metal 1 Cross-Coupled Connections
    c.add_polygon([(2.0, 2.0), (23.0, 2.0), (23.0, 6.0), (2.0, 6.0)], layer=LAYER_METAL1)
    c.add_polygon([(2.0, 12.0), (23.0, 12.0), (23.0, 16.0), (2.0, 16.0)], layer=LAYER_METAL1)

    # Via 1 & Metal 2 Output Rails
    c.add_polygon([(4.0, 5.0), (7.0, 5.0), (7.0, 7.0), (4.0, 7.0)], layer=LAYER_VIA1)
    c.add_polygon([(18.0, 11.0), (21.0, 11.0), (21.0, 13.0), (18.0, 13.0)], layer=LAYER_VIA1)
    c.add_polygon([(4.0, 5.0), (7.0, 5.0), (7.0, 13.0), (4.0, 13.0)], layer=LAYER_METAL2)
    c.add_polygon([(18.0, 5.0), (21.0, 5.0), (21.0, 13.0), (18.0, 13.0)], layer=LAYER_METAL2)

    # UBM Landing Pad for Cu TDV from APD anode
    # Diameter = TDV_DIAMETER_UM = 8 um; pad radius = TDV/2 + UBM_OVERHANG = 4+1.5 = 5.5 um
    r_pad = TDV_DIAMETER_UM / 2.0 + TDV_UBM_OVERHANG_UM   # 5.5 um
    cx, cy = 12.5, 9.0
    pts_ubm = [
        (cx + r_pad * np.cos(np.deg2rad(deg)), cy + r_pad * np.sin(np.deg2rad(deg)))
        for deg in range(0, 360, 45)
    ]
    c.add_polygon(pts_ubm, layer=LAYER_PASSIVATION_UBM)

    # Architectural annotation
    c.add_polygon([(0, 0), (25.0, 0), (25.0, 18.0), (0, 18.0)], layer=LAYER_ARCH_STRONGARM)
    c.add_label("STRONGARM_LATCH", position=(12.5, 9.0), layer=LAYER_ARCH_STRONGARM)
    return c


@gf.cell
def pcell_cmos_deserializer_bank() -> gf.Component:
    """
    1:32 Polyphase Time-Interleaved Deserializer Bank:
      - 5-bit master binary ring counter & 32-phase latch clock generators
      - 32-bit register shift register array (height = 16*32 = 512 um core)
    """
    c = gf.Component("DESERIALIZER_1TO32_BANK")
    w, h = 45.0, 512.0    # Corrected: 32 stages * 16 um = 512 um

    c.add_polygon([(0, 0), (w, 0), (w, h), (0, h)], layer=LAYER_NW_DIFF)

    for i in range(32):
        y_sec = 8.0 + i * 16.0
        c.add_polygon([(2.0, y_sec), (w - 2.0, y_sec),
                       (w - 2.0, y_sec + 3.0), (2.0, y_sec + 3.0)], layer=LAYER_POLY_GATE)
        # Metal 1 Clock & Data taps
        c.add_polygon([(5.0, y_sec - 2.0), (15.0, y_sec - 2.0),
                       (15.0, y_sec + 5.0), (5.0, y_sec + 5.0)], layer=LAYER_METAL1)
        c.add_polygon([(25.0, y_sec - 2.0), (40.0, y_sec - 2.0),
                       (40.0, y_sec + 5.0), (25.0, y_sec + 5.0)], layer=LAYER_METAL2)
        # Via 1 & 2 interconnects
        c.add_polygon([(10.0, y_sec), (12.0, y_sec), (12.0, y_sec + 2.0), (10.0, y_sec + 2.0)],
                      layer=LAYER_VIA1)
        c.add_polygon([(30.0, y_sec), (32.0, y_sec), (32.0, y_sec + 2.0), (30.0, y_sec + 2.0)],
                      layer=LAYER_VIA2)

    # Metal 3 32-bit parallel bus output
    for b in range(8):
        xb = 6.0 + b * 4.5
        c.add_polygon([(xb, 5.0), (xb + 2.0, 5.0), (xb + 2.0, h - 5.0), (xb, h - 5.0)],
                      layer=LAYER_METAL3)

    c.add_polygon([(0, 0), (w, 0), (w, h), (0, h)], layer=LAYER_ARCH_DESER)
    c.add_label("1TO32_DESERIALIZER_BANK", position=(w / 2, h / 2), layer=LAYER_ARCH_DESER)
    return c


@gf.cell
def pcell_cmos_simd_wallace_kogge_array() -> gf.Component:
    """
    32-Lane SIMD Wallace-Tree & Kogge-Stone Parallel-Prefix Arithmetic Array:
      - 8:2 Wallace Tree Carry-Save Compressor Tree (4 levels, 75 ps)
      - 64-Bit Kogge-Stone Parallel-Prefix Adder (110 ps)
      - Montgomery Constant-Modulus Reducer (100 ps)
    """
    c = gf.Component("SIMD_WALLACE_KOGGE_ARRAY")
    w, h = 180.0, 310.0

    c.add_polygon([(0, 0), (w, 0), (w, h), (0, h)], layer=LAYER_NW_DIFF)

    lane_w = w / 32.0
    for l in range(32):
        xl = l * lane_w
        # Wallace Tree CSA Section (Y: 10-120 um)
        c.add_polygon([(xl + 0.5, 10.0), (xl + lane_w - 0.5, 10.0),
                       (xl + lane_w - 0.5, 120.0), (xl + 0.5, 120.0)], layer=LAYER_METAL1)
        # Kogge-Stone Prefix Tree (Y: 130-230 um)
        c.add_polygon([(xl + 0.5, 130.0), (xl + lane_w - 0.5, 130.0),
                       (xl + lane_w - 0.5, 230.0), (xl + 0.5, 230.0)], layer=LAYER_METAL2)
        # Montgomery Reducer (Y: 240-300 um)
        c.add_polygon([(xl + 0.5, 240.0), (xl + lane_w - 0.5, 240.0),
                       (xl + lane_w - 0.5, 300.0), (xl + 0.5, 300.0)], layer=LAYER_METAL3)
        # Vias between stages
        c.add_polygon([(xl + 1.0, 123.0), (xl + 3.0, 123.0),
                       (xl + 3.0, 127.0), (xl + 1.0, 127.0)], layer=LAYER_VIA1)
        c.add_polygon([(xl + 1.0, 233.0), (xl + 3.0, 233.0),
                       (xl + 3.0, 237.0), (xl + 1.0, 237.0)], layer=LAYER_VIA2)

    # Cross-lane Metal 4 Carry / Routing Tracks
    for t in range(12):
        yt = 25.0 + t * 24.0
        c.add_polygon([(5.0, yt), (w - 5.0, yt), (w - 5.0, yt + 2.5), (5.0, yt + 2.5)],
                      layer=LAYER_METAL4)
        c.add_polygon([(8.0, yt), (12.0, yt), (12.0, yt + 2.5), (8.0, yt + 2.5)],
                      layer=LAYER_VIA3)
        c.add_polygon([(w - 12.0, yt), (w - 8.0, yt), (w - 8.0, yt + 2.5), (w - 12.0, yt + 2.5)],
                      layer=LAYER_VIA3)

    c.add_polygon([(0, 0), (w, 0), (w, h), (0, h)], layer=LAYER_ARCH_SIMD)
    c.add_label("32LANE_SIMD_WALLACE_KOGGE", position=(w / 2, h / 2), layer=LAYER_ARCH_SIMD)
    return c


@gf.cell
def pcell_cmos_duallut_sram_macro() -> gf.Component:
    """
    1.5 MB Dual-LUT Volatile Local SRAM Macro (32 Slices x 48 KB):
      - 6T SRAM Bitcell Matrix
      - Wordline Drivers & Sense Amplifiers
      - Dynamic MTCMOS Power-Gating Headers
    """
    c = gf.Component("DUALLUT_SRAM_1P5MB_MACRO")
    w, h = 260.0, 190.0

    c.add_polygon([(0, 0), (w, 0), (w, h), (0, h)], layer=LAYER_NW_DIFF)

    # Memory Sub-Banks (4 quadrants x 2 rows)
    for qx in range(4):
        for qy in range(2):
            bx = 10.0 + qx * 62.0
            by = 10.0 + qy * 90.0
            c.add_polygon([(bx, by), (bx + 54.0, by),
                           (bx + 54.0, by + 78.0), (bx, by + 78.0)], layer=LAYER_METAL2)
            for wl in range(6):
                yw = by + 6.0 + wl * 12.0
                c.add_polygon([(bx + 2.0, yw), (bx + 52.0, yw),
                               (bx + 52.0, yw + 1.8), (bx + 2.0, yw + 1.8)], layer=LAYER_METAL3)
            for bl in range(4):
                xb = bx + 6.0 + bl * 12.0
                c.add_polygon([(xb, by + 2.0), (xb + 1.8, by + 2.0),
                               (xb + 1.8, by + 76.0), (xb, by + 76.0)], layer=LAYER_METAL4)

    # Sense-Amp & Address Decoder Spine
    c.add_polygon([(w / 2 - 12.0, 5.0), (w / 2 + 12.0, 5.0),
                   (w / 2 + 12.0, h - 5.0), (w / 2 - 12.0, h - 5.0)], layer=LAYER_METAL1)

    c.add_polygon([(0, 0), (w, 0), (w, h), (0, h)], layer=LAYER_ARCH_SRAM)
    c.add_label("DUALLUT_SRAM_1.5MB", position=(w / 2, h / 2), layer=LAYER_ARCH_SRAM)
    return c


@gf.cell
def pcell_cmos_central_rom_jir_macro() -> gf.Component:
    """
    1.5 MB Central Non-Volatile ROM & Master JIR Epoch Sequencer FSM:
      - Hardwired Via-ROM Array for PRNS constants & Montgomery tables
      - JIR Running-Average Thermal Slope Estimator
      - Warp / Epoch Sequencer Control FSM
    """
    c = gf.Component("CENTRAL_ROM_JIR_MACRO")
    w, h = 120.0, 190.0

    c.add_polygon([(0, 0), (w, 0), (w, h), (0, h)], layer=LAYER_NW_DIFF)

    # Dense Via-ROM Matrix
    for col in range(12):
        xc = 8.0 + col * 9.0
        c.add_polygon([(xc, 10.0), (xc + 2.5, 10.0), (xc + 2.5, 140.0), (xc, 140.0)],
                      layer=LAYER_METAL1)
        for row in range(14):
            yr = 14.0 + row * 9.0
            c.add_polygon([(xc, yr), (xc + 2.5, yr), (xc + 2.5, yr + 2.5), (xc, yr + 2.5)],
                          layer=LAYER_VIA1)

    # JIR Controller Logic Block (Y: 150-185 um)
    c.add_polygon([(5.0, 150.0), (w - 5.0, 150.0), (w - 5.0, 185.0), (5.0, 185.0)],
                  layer=LAYER_METAL2)
    c.add_polygon([(10.0, 155.0), (w - 10.0, 155.0), (w - 10.0, 180.0), (10.0, 180.0)],
                  layer=LAYER_METAL3)

    c.add_polygon([(0, 0), (w, 0), (w, h), (0, h)], layer=LAYER_ARCH_ROM)
    c.add_label("CENTRAL_ROM_JIR_1.5MB", position=(w / 2, h / 2), layer=LAYER_ARCH_ROM)
    return c


@gf.cell
def pcell_cmos_accumulator_160bit() -> gf.Component:
    """
    160-Bit Binary Carry-Save Accumulator (CSA):
      - 160-bit 3:2 CSA Accumulation Slice (25 ps)
      - Final 160-bit Kogge-Stone Resolution Adder (applied at K-loop end)
      - 32-bit Accumulation Headroom (K = 32 to 4096)
    """
    c = gf.Component("ACCUMULATOR_160BIT_CSA")
    w, h = 200.0, 160.0

    c.add_polygon([(0, 0), (w, 0), (w, h), (0, h)], layer=LAYER_NW_DIFF)

    for b in range(5):
        yb = 10.0 + b * 28.0
        c.add_polygon([(10.0, yb), (w - 10.0, yb), (w - 10.0, yb + 12.0), (10.0, yb + 12.0)],
                      layer=LAYER_METAL1)
        c.add_polygon([(10.0, yb + 14.0), (w - 10.0, yb + 14.0),
                       (w - 10.0, yb + 24.0), (10.0, yb + 24.0)], layer=LAYER_METAL2)
        c.add_polygon([(12.0, yb + 10.0), (w - 12.0, yb + 10.0),
                       (w - 12.0, yb + 14.0), (12.0, yb + 14.0)], layer=LAYER_METAL5)

    c.add_polygon([(0, 0), (w, 0), (w, h), (0, h)], layer=LAYER_ARCH_ACC160)
    c.add_label("160BIT_CSA_ACCUMULATOR", position=(w / 2, h / 2), layer=LAYER_ARCH_ACC160)
    return c


@gf.cell
def pcell_cmos_thermal_sensor_unit() -> gf.Component:
    """
    JIR On-Chip Thermal Diode & 10-Bit Delta-Sigma ADC Unit:
      - Substrate PNP thermal sensing diode (2 mV / deg-C)
      - Switched-capacitor second-order modulator & decimation filter
    """
    c = gf.Component("THERMAL_SENSOR_UNIT")
    w, h = 30.0, 30.0

    c.add_polygon([(0, 0), (w, 0), (w, h), (0, h)], layer=LAYER_NW_DIFF)
    c.add_polygon([(5.0, 5.0), (w - 5.0, 5.0), (w - 5.0, h - 5.0), (5.0, h - 5.0)],
                  layer=LAYER_METAL1)
    c.add_polygon([(8.0, 8.0), (w - 8.0, 8.0), (w - 8.0, h - 8.0), (8.0, h - 8.0)],
                  layer=LAYER_METAL2)

    c.add_polygon([(0, 0), (w, 0), (w, h), (0, h)], layer=LAYER_ARCH_THERMAL)
    c.add_label("JIR_THERMAL_ADC", position=(w / 2, h / 2), layer=LAYER_ARCH_THERMAL)
    return c


# ==============================================================================
# 2. SINGLE 65nm CMOS TILE SUB-SYSTEM (600 x 600 um footprint)
# ==============================================================================

@gf.cell
def build_cmos_base_tile(tile_id: int = 0) -> gf.Component:
    """
    Synthesizes a complete 65nm CMOS Base Tile (600 um x 600 um core active area,
    matching the 6.25 mm^2 top optical tile footprint 1:1):
      1. 17x StrongARM Regenerative Sensing Latches (1:1 aligned with APD TDVs)
      2. 1:32 Polyphase Time-Interleaved Deserializer Bank
      3. 32-Lane SIMD Wallace-Tree / Kogge-Stone Arithmetic Array
      4. 1.5 MB Dual-LUT Volatile Local SRAM Slices
      5. 1.5 MB Central Non-Volatile ROM & JIR Epoch Sequencer
      6. 160-Bit Binary Carry-Save Accumulator
      7. 4x Distributed JIR Thermal Diodes & ADCs
      8. Inter-block M3/M4/M5 buses & local Power Grid / Clock trunk
    """
    tile = gf.Component(f"CMOS_BASE_TILE_{tile_id}")
    tile_w = TILE_CORE_UM
    tile_h = TILE_CORE_UM

    # Physical Boundary
    tile.add_polygon([(0, 0), (tile_w, 0), (tile_w, tile_h), (0, tile_h)],
                     layer=LAYER_FLOORPLAN)

    # 1. 17x StrongARM Latches directly beneath APD TDVs (X: 510-535 um)
    latch_unit = pcell_cmos_strongarm_latch_unit()
    for ch in range(17):
        y_latch = 45.0 + ch * 31.0
        tile.add_ref(latch_unit).move((510.0, y_latch - 9.0))
        tile.add_label(f"STRONGARM_CH{ch}", position=(522.5, y_latch),
                       layer=LAYER_ARCH_STRONGARM)

    # 2. 1:32 Polyphase Deserializer Bank (X: 450-495 um, Y: 40-552 um)
    tile.add_ref(pcell_cmos_deserializer_bank()).move((450.0, 40.0))

    # 3. 32-Lane SIMD Wallace-Kogge Array (X: 250-430 um, Y: 40-350 um)
    tile.add_ref(pcell_cmos_simd_wallace_kogge_array()).move((250.0, 40.0))

    # 4. 1.5 MB Dual-LUT Local SRAM (X: 60-320 um, Y: 380-570 um)
    tile.add_ref(pcell_cmos_duallut_sram_macro()).move((60.0, 380.0))

    # 5. Central ROM & JIR Controller (X: 340-460 um, Y: 380-570 um)
    tile.add_ref(pcell_cmos_central_rom_jir_macro()).move((340.0, 380.0))

    # 6. 160-Bit Binary Carry-Save Accumulator (X: 40-240 um, Y: 40-200 um)
    tile.add_ref(pcell_cmos_accumulator_160bit()).move((40.0, 40.0))

    # 7. 4x Distributed JIR Thermal Diode Sensors
    sensor_cell = pcell_cmos_thermal_sensor_unit()
    for td in range(4):
        xt = 70.0 + td * 120.0
        tile.add_ref(sensor_cell).move((xt, 220.0))

    # 8. Inter-Block Signal Buses
    # Sense-Amp → Deserializer Bus (Metal 2)
    for ch in range(17):
        y_latch = 45.0 + ch * 31.0
        tile.add_polygon([(495.0, y_latch - 1.5), (510.0, y_latch - 1.5),
                          (510.0, y_latch + 1.5), (495.0, y_latch + 1.5)], layer=LAYER_METAL2)
    # Deserializer → SIMD 32-Lane Bus (Metal 3)
    for b in range(16):
        yb = 55.0 + b * 18.0
        tile.add_polygon([(430.0, yb), (450.0, yb), (450.0, yb + 2.0), (430.0, yb + 2.0)],
                         layer=LAYER_METAL3)
    # SRAM → SIMD Dual-LUT Weight Bus (Metal 4)
    for w_idx in range(12):
        xw = 260.0 + w_idx * 12.0
        tile.add_polygon([(xw, 350.0), (xw + 2.0, 350.0),
                          (xw + 2.0, 380.0), (xw, 380.0)], layer=LAYER_METAL4)
    # SIMD → Accumulator 160-bit Carry-Save Bus (Metal 5)
    for a_idx in range(8):
        ya = 60.0 + a_idx * 16.0
        tile.add_polygon([(240.0, ya), (250.0, ya), (250.0, ya + 2.5), (240.0, ya + 2.5)],
                         layer=LAYER_METAL5)

    # 9. Local Power Grid Mesh (Top Metal 171/0: VDD / VSS Stripes)
    for p in range(7):
        yp = 30.0 + p * 85.0
        tile.add_polygon([(10.0, yp), (tile_w - 10.0, yp),
                          (tile_w - 10.0, yp + 12.0), (10.0, yp + 12.0)],
                         layer=LAYER_TOP_METAL_PWR)
    for p in range(7):
        xp = 30.0 + p * 85.0
        tile.add_polygon([(xp, 10.0), (xp + 12.0, 10.0),
                          (xp + 12.0, tile_h - 10.0), (xp, tile_h - 10.0)],
                         layer=LAYER_TOP_METAL_PWR)

    # 10. In-tile Clock Trunk (Metal 6: cross-shaped local distribution)
    tile.add_polygon([(tile_w / 2 - 3.0, 20.0), (tile_w / 2 + 3.0, 20.0),
                      (tile_w / 2 + 3.0, tile_h - 20.0), (tile_w / 2 - 3.0, tile_h - 20.0)],
                     layer=LAYER_METAL6_CLK)
    tile.add_polygon([(20.0, tile_h / 2 - 3.0), (tile_w - 20.0, tile_h / 2 - 3.0),
                      (tile_w - 20.0, tile_h / 2 + 3.0), (20.0, tile_h / 2 + 3.0)],
                     layer=LAYER_METAL6_CLK)

    tile.add_label(f"CMOS_TILE_{tile_id}_BASE", position=(tile_w / 2, tile_h / 2),
                   layer=LAYER_FLOORPLAN)
    tile.add_label("VDD_VSS_LOCAL_POWER_GRID", position=(40.0, 35.0),
                   layer=LAYER_TOP_METAL_PWR)
    tile.add_label("CLK_TRUNK_3.125GHZ", position=(tile_w / 2, 25.0),
                   layer=LAYER_METAL6_CLK)

    return tile


# ==============================================================================
# 3. FULL CHIP 65nm CMOS BASE DIE SYNTHESIZER (3.20 mm x 3.20 mm)
# ==============================================================================

def generate_janus_mini16_cmos_top_layout() -> gf.Component:
    """
    Synthesizes the complete 4x4 array of 16 CMOS Arithmetic Tiles surrounded by:
      - 4-level balanced H-tree 3.125 GHz clock distribution (Metal 6)
      - Global VDD/VSS power ring (Top Metal)
      - 4-side wire-bond / solder bump I/O pad ring
      - 4-layer concentric moisture seal ring

    Die: 3200 x 3200 um | Tiles: 4x4 @ 700 um pitch | Origin: (200, 200)
    """
    top = gf.Component("JANUS_MINI16_CMOS_BASE_DIE")

    die_w = DIE_WIDTH_UM    # 3200 um
    die_h = DIE_HEIGHT_UM   # 3200 um

    # ---- 1. Chip Boundary ----
    top.add_polygon([(0, 0), (die_w, 0), (die_w, die_h), (0, die_h)], layer=LAYER_FLOORPLAN)
    top.add_label("JANUS_MINI16_CMOS_DIE_BOUNDARY", position=(die_w / 2, die_h - 30.0),
                  layer=LAYER_FLOORPLAN)

    # ---- 2. 4-Layer Concentric Moisture Seal Ring ----
    # Four separate ring widths stacked inward from the edge at 4 um spacing.
    seal_ring_w = 4.0       # individual ring width
    seal_ring_gap = 6.0     # pitch between ring centers
    seal_edge_off = 10.0    # innermost ring outer edge distance from die edge
    for s in range(4):
        off = seal_edge_off + s * seal_ring_gap
        # Bottom bar
        top.add_polygon([(off, off), (die_w - off, off),
                         (die_w - off, off + seal_ring_w), (off, off + seal_ring_w)],
                        layer=LAYER_SEAL_RING)
        # Top bar
        top.add_polygon([(off, die_h - off - seal_ring_w), (die_w - off, die_h - off - seal_ring_w),
                         (die_w - off, die_h - off), (off, die_h - off)],
                        layer=LAYER_SEAL_RING)
        # Left bar
        top.add_polygon([(off, off), (off + seal_ring_w, off),
                         (off + seal_ring_w, die_h - off), (off, die_h - off)],
                        layer=LAYER_SEAL_RING)
        # Right bar
        top.add_polygon([(die_w - off - seal_ring_w, off), (die_w - off, off),
                         (die_w - off, die_h - off), (die_w - off - seal_ring_w, die_h - off)],
                        layer=LAYER_SEAL_RING)
    top.add_label("CMOS_SEAL_RING_4LAYER", position=(40.0, die_h - 40.0),
                  layer=LAYER_SEAL_RING)

    # ---- 3. 4x4 Array of 16 CMOS Compute Tiles ----
    x_origin = TILE_ARRAY_ORIGIN_X   # 200 um
    y_origin = TILE_ARRAY_ORIGIN_Y   # 200 um
    tile_pitch = TILE_PITCH_UM       # 700 um

    for row in range(4):
        for col in range(4):
            tile_id = row * 4 + col
            x_pos = x_origin + col * tile_pitch
            y_pos = y_origin + row * tile_pitch
            tile_ref = top.add_ref(build_cmos_base_tile(tile_id=tile_id))
            tile_ref.move((x_pos, y_pos))
            top.add_label(f"CMOS_TILE_{tile_id}_LOC",
                          position=(x_pos + 300.0, y_pos + 300.0),
                          layer=LAYER_FLOORPLAN)

    # ---- 4. Global VDD/VSS Power Ring (Top Metal 171/0) ----
    pwr_off = PWR_RING_OFFSET_UM     # 60 um
    pwr_w = PWR_RING_WIDTH_UM        # 40 um
    # Bottom & Top rails
    top.add_polygon([(pwr_off, 50.0), (die_w - pwr_off, 50.0),
                     (die_w - pwr_off, 50.0 + pwr_w), (pwr_off, 50.0 + pwr_w)],
                    layer=LAYER_TOP_METAL_PWR)
    top.add_polygon([(pwr_off, die_h - 50.0 - pwr_w), (die_w - pwr_off, die_h - 50.0 - pwr_w),
                     (die_w - pwr_off, die_h - 50.0), (pwr_off, die_h - 50.0)],
                    layer=LAYER_TOP_METAL_PWR)
    # Left & Right rails
    top.add_polygon([(pwr_off, 50.0), (pwr_off + pwr_w, 50.0),
                     (pwr_off + pwr_w, die_h - 50.0), (pwr_off, die_h - 50.0)],
                    layer=LAYER_TOP_METAL_PWR)
    top.add_polygon([(die_w - pwr_off - pwr_w, 50.0), (die_w - pwr_off, 50.0),
                     (die_w - pwr_off, die_h - 50.0), (die_w - pwr_off - pwr_w, die_h - 50.0)],
                    layer=LAYER_TOP_METAL_PWR)
    top.add_label("GLOBAL_VDD_VSS_POWER_RING", position=(die_w / 2, 70.0),
                  layer=LAYER_TOP_METAL_PWR)

    # ---- 5. Complete 4-Side Wire-Bond / Solder Bump I/O Pad Ring ----
    pad_s = PAD_SIZE_UM      # 75 um
    pad_p = PAD_PITCH_UM     # 120 um
    pad_y_bot = 95.0         # Bottom row Y offset from die bottom
    pad_y_top = die_h - 95.0 - pad_s   # Top row Y offset from die top

    # Bottom & Top rows (horizontal)
    num_pads_x = int((die_w - 400.0) / pad_p)
    for p in range(num_pads_x):
        xp = 200.0 + p * pad_p
        top.add_polygon([(xp, pad_y_bot), (xp + pad_s, pad_y_bot),
                         (xp + pad_s, pad_y_bot + pad_s), (xp, pad_y_bot + pad_s)],
                        layer=LAYER_PAD_IO)
        top.add_label(f"IO_PAD_BOT_{p}",
                      position=(xp + pad_s / 2, pad_y_bot + pad_s / 2), layer=LAYER_PAD_IO)
        top.add_polygon([(xp, pad_y_top), (xp + pad_s, pad_y_top),
                         (xp + pad_s, pad_y_top + pad_s), (xp, pad_y_top + pad_s)],
                        layer=LAYER_PAD_IO)
        top.add_label(f"IO_PAD_TOP_{p}",
                      position=(xp + pad_s / 2, pad_y_top + pad_s / 2), layer=LAYER_PAD_IO)

    # Left & Right columns (vertical)
    pad_x_left = 95.0
    pad_x_right = die_w - 95.0 - pad_s
    num_pads_y = int((die_h - 400.0) / pad_p)
    for p in range(num_pads_y):
        yp = 200.0 + p * pad_p
        top.add_polygon([(pad_x_left, yp), (pad_x_left + pad_s, yp),
                         (pad_x_left + pad_s, yp + pad_s), (pad_x_left, yp + pad_s)],
                        layer=LAYER_PAD_IO)
        top.add_label(f"IO_PAD_LEFT_{p}",
                      position=(pad_x_left + pad_s / 2, yp + pad_s / 2), layer=LAYER_PAD_IO)
        top.add_polygon([(pad_x_right, yp), (pad_x_right + pad_s, yp),
                         (pad_x_right + pad_s, yp + pad_s), (pad_x_right, yp + pad_s)],
                        layer=LAYER_PAD_IO)
        top.add_label(f"IO_PAD_RIGHT_{p}",
                      position=(pad_x_right + pad_s / 2, yp + pad_s / 2), layer=LAYER_PAD_IO)

    # ---- 6. 4-Level Balanced H-Tree Global Clock (Metal 6 / Layer 161/0) ----
    add_balanced_htree_4x4(top, x_origin, y_origin, tile_pitch, LAYER_METAL6_CLK)

    return top


# ==============================================================================
# 4. MAIN ROUTINE & EXPORTER
# ==============================================================================

def main():
    print("=" * 75)
    print("PROJECT JANUS: 65nm LP/GP CMOS DIGITAL BASE DIE GDS II SYNTHESIZER")
    print("=" * 75)
    print("[*] Synthesizing 16x 65nm CMOS Compute Tiles...")
    print("[*] Synthesizing StrongARM Latches, 1:32 Deserializers & SIMD Wallace-Kogge...")
    print("[*] Synthesizing 1.5MB Dual-LUT SRAM & Central ROM Macros...")
    print("[*] Synthesizing 160-Bit Carry-Save Accumulator & JIR Thermal Diodes...")
    print("[*] Synthesizing UBM Micro-Bump Pads, 4-Level H-Tree Clock & Power Rings...")

    out_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "layout"))
    os.makedirs(out_dir, exist_ok=True)
    cmos_gds_path = os.path.join(out_dir, "janus_mini16_cmos_base_layout.gds")

    top_cmos = generate_janus_mini16_cmos_top_layout()

    print(f"[*] Writing binary GDS II stream file to:\n    {cmos_gds_path}")
    top_cmos.write_gds(cmos_gds_path)

    lyp_src = os.path.join(out_dir, "janus_mini16_layers.lyp")
    lyp_cmos = os.path.join(out_dir, "janus_mini16_cmos_base_layout.lyp")
    if os.path.exists(lyp_src):
        shutil.copyfile(lyp_src, lyp_cmos)

    gds_size = os.path.getsize(cmos_gds_path)
    print(f"[+] SUCCESS! 65nm CMOS Base Die GDS II layout generated.")
    print(f"    - Target File   : {cmos_gds_path}")
    print(f"    - Companion LYP : {lyp_cmos}")
    print(f"    - File Size     : {gds_size:,} bytes ({gds_size / 1024:.2f} KB)")
    print(f"    - Top Cell      : {top_cmos.name}")
    print(f"    - Die Dimensions: {DIE_WIDTH_UM/1000:.2f} mm x {DIE_HEIGHT_UM/1000:.2f} mm")
    print(f"    - CMOS Layer Range: 100-199 (no collision with optical stratum 1-29)")
    print("=" * 75)


if __name__ == "__main__":
    main()
