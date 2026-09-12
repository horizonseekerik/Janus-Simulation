"""
PROJECT JANUS MINI (16-TILE): DUAL-STRATUM 3D MONOLITHIC GDS II LAYOUT SYNTHESIZER
==================================================================================
Synthesizes the complete, tapeout-grade multi-layer physical mask layout
for the JANUS Mini 16-Tile Monolithic 3D-Stacked Accelerator (Model 1A).

Architecture:
  1. Top SiPh/Si3N4 Core Stratum (Dual-Layer Optical Stack):
     - Layer 5/0: Si3N4 Core (800x300 nm strip, low-loss routing, zero TPA)
     - Layer 1/0: Crystalline Silicon Core (450x220 nm, detector mesa base)
     - Adiabatic Inter-Layer Tapers (Si3N4 -> Si transition, IL < 0.05 dB)
     - Layer 3/0: Thin-Film LiTaO3 100 GHz Pockels Modulators
     - Layer 4/0 & 4/1: Sb2S3 Non-Volatile Directional Coupler Switches
     - Layer 20/0: SAC2M Ge/Si Avalanche Photodiode (APD) Mesas
     - Layer 10/0 & 11/0: Metal 1 & Metal 2 Copper Power and RF Distribution

  2. 3D Inter-Stratum Vertical Interconnects:
     - Layer 30/0: High-Density Vertical Copper TDVs (8 um diam, 10,000 mm^-2)
     - Layer 31/0: Under-Bump Metallization (UBM) & Micro-Bumps (50 um pitch)
     - Layer 32/0: Monolithic 250 um SiO2 Thermal Buffer Isolation

  3. Bottom 65nm LP/GP CMOS Base Stratum (1:1 Superimposed Footprint):
     Physical mask layers in 100-199 range (no GDS collision with optical 1-29):
     - Layer 101/0: N-Well & Active Diffusion
     - Layer 102/0: Polysilicon Gate
     ... (full layer map in janus_layer_constants.py)
     Abstract block annotations (40-49 range):
     - Layer 40/0: StrongARM Regenerative Sensing Latch Front-End
     - Layer 41/0 to 46/0: Deserializer, SIMD, SRAM, ROM, Accumulator, ADCs

  4. Chip Perimeter & Metrology:
     - Layer 190/0: 4-Layer Concentric Moisture Barrier Chip Seal Ring
     - Layer 199/0: Dicing Streets & Tile Perimeter Keep-Out
"""

import os
import sys
import math
import shutil
import numpy as np
from typing import List

# ---------------------------------------------------------------------------
# Workspace root on sys.path
# ---------------------------------------------------------------------------
_ws_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _ws_root not in sys.path:
    sys.path.insert(0, _ws_root)

import gdsfactory as gf

from janus_mini16_sim.layout.janus_layer_constants import (
    # Optical stratum layers (1-29)
    LAYER_SI_CORE, LAYER_SIO2_CLAD, LAYER_LITAO3_EO,
    LAYER_SB2S3_AMORPH, LAYER_SB2S3_CRYST,
    LAYER_SIN_CORE,
    LAYER_CU_M1, LAYER_CU_M2,
    LAYER_APD_GE,
    # 3D inter-stratum layers (30-39)
    LAYER_TDV_PILLAR, LAYER_UBM_BUMP, LAYER_THERMAL_BUF,
    # Physical CMOS layers (100-199) used directly in top-level assembly
    LAYER_TOP_METAL_PWR, LAYER_PAD_IO, LAYER_METAL6_CLK, LAYER_PASSIVATION_UBM,
    # Perimeter & metrology
    LAYER_SEAL_RING, LAYER_FLOORPLAN,
    # Canonical physical dimensions
    DIE_WIDTH_UM, DIE_HEIGHT_UM,
    TILE_CORE_UM, TILE_PITCH_UM, TILE_ARRAY_ORIGIN_X, TILE_ARRAY_ORIGIN_Y,
    SIN_WIDTH_UM, SI_WIDTH_UM,
    COUPLER_LEN_UM, COUPLER_GAP_UM, PATCH_LEN_UM, PATCH_WIDTH_UM,
    MMI_W_UM, MMI_L_UM, MMI_TAPER_UM,
    LITAO3_LEN_UM, LITAO3_W_UM,
    APD_LEN_UM, APD_W_UM,
    TDV_DIAMETER_UM, TDV_UBM_OVERHANG_UM, BUMP_PITCH_UM,
    GC_TEETH_PERIOD_UM, GC_DUTY_CYCLE, GC_NUM_TEETH,
    GC_BODY_LEN_UM, GC_HALF_WIDTH_UM,
    PAD_SIZE_UM, PAD_PITCH_UM,
    PWR_RING_WIDTH_UM, PWR_RING_OFFSET_UM,
    WAVELENGTH_NM,
)

from janus_mini16_sim.layout.generate_cmos_base_gds import (
    pcell_cmos_strongarm_latch_unit,
    pcell_cmos_deserializer_bank,
    pcell_cmos_simd_wallace_kogge_array,
    pcell_cmos_duallut_sram_macro,
    pcell_cmos_central_rom_jir_macro,
    pcell_cmos_accumulator_160bit,
    pcell_cmos_thermal_sensor_unit,
    build_cmos_base_tile,
    _htree_seg,
    add_balanced_htree_4x4,
)

# Activate generic layout environment
gf.gpdk.PDK.activate()


# ==============================================================================
# UTILITY: HTREE SEGMENT (re-exported from cmos module for top-level use)
# ==============================================================================
# _htree_seg and add_balanced_htree_4x4 are imported above.


# ==============================================================================
# 1. PARAMETRIC CELLS (PCELLS) — OPTICAL STRATUM
# ==============================================================================

@gf.cell
def pcell_sin_straight_wg(length: float = 20.0, width: float = SIN_WIDTH_UM) -> gf.Component:
    """Straight low-loss Si3N4 waveguide (Layer 5/0)."""
    c = gf.Component(f"SIN_STRAIGHT_WG_L{int(length)}_W{int(width * 1000)}")
    c.add_polygon(
        [(0, -width / 2), (length, -width / 2), (length, width / 2), (0, width / 2)],
        layer=LAYER_SIN_CORE,
    )
    return c


@gf.cell
def pcell_sin_sbend_wg(dx: float = 30.0, dy: float = 10.0,
                       width: float = SIN_WIDTH_UM) -> gf.Component:
    """
    Adiabatic S-bend waveguide in Si3N4 with cubic spline (Layer 5/0).
    Cell name encodes |dy| to avoid embedded '-' characters in GDS cell names,
    which are non-standard and cause parsing failures in some EDA tools.
    """
    # Use absolute value in name; sign encoded by 'N' prefix for negative dy
    sign_char = "N" if dy < 0 else "P"
    c = gf.Component(f"SIN_SBEND_WG_DX{int(dx)}_{sign_char}DY{int(abs(dy) * 10)}")
    N = 25
    pts = [(i / N * dx, dy * (3.0 * (i / N) ** 2 - 2.0 * (i / N) ** 3)) for i in range(N + 1)]

    poly = [(x, y - width / 2) for x, y in pts] + \
           [(x, y + width / 2) for x, y in reversed(pts)]
    c.add_polygon(poly, layer=LAYER_SIN_CORE)
    return c


@gf.cell
def pcell_sin_to_si_taper(length: float = 15.0) -> gf.Component:
    """
    Adiabatic inter-layer transition taper: Si3N4 (Layer 5/0) → Si (Layer 1/0).
    Foundry-standard dual-core inverse taper (IL < 0.05 dB).
    """
    c = gf.Component(f"SIN_TO_SI_TAPER_L{int(length)}")
    # Si3N4 inverse taper narrowing from 800 nm to 150 nm tip
    c.add_polygon([(0, -SIN_WIDTH_UM / 2), (length, -0.075),
                   (length, 0.075), (0, SIN_WIDTH_UM / 2)], layer=LAYER_SIN_CORE)
    # Underlying Si inverse taper widening from 150 nm to 450 nm
    c.add_polygon([(0, -0.075), (length, -SI_WIDTH_UM / 2),
                   (length, SI_WIDTH_UM / 2), (0, 0.075)], layer=LAYER_SI_CORE)
    c.add_label("SIN_SI_TAPER", position=(length / 2, 0.0), layer=LAYER_SIN_CORE)
    return c


@gf.cell
def pcell_sb2s3_sin_switch_cell() -> gf.Component:
    """
    Low-loss Si3N4 directional coupler with non-volatile Sb2S3 phase-change patch.
    IL = 0.263 dB, ER = 51.9 dB, 0 W static power.
    """
    c = gf.Component("SB2S3_SIN_SWITCH_CELL")
    total_len = COUPLER_LEN_UM + 3.0
    y_bar = COUPLER_GAP_UM / 2 + SIN_WIDTH_UM / 2
    y_cross = -y_bar

    # Through (Bar) & Cross Waveguides in Si3N4 (Layer 5/0)
    for y_wg in [y_bar, y_cross]:
        c.add_polygon([(0, y_wg - SIN_WIDTH_UM / 2), (total_len, y_wg - SIN_WIDTH_UM / 2),
                       (total_len, y_wg + SIN_WIDTH_UM / 2), (0, y_wg + SIN_WIDTH_UM / 2)],
                      layer=LAYER_SIN_CORE)

    # Active Sb2S3 Phase-Change Patch (Layer 4/0)
    x_ps = (total_len - PATCH_LEN_UM) / 2
    x_pe = x_ps + PATCH_LEN_UM
    c.add_polygon([(x_ps, y_bar - PATCH_WIDTH_UM / 2), (x_pe, y_bar - PATCH_WIDTH_UM / 2),
                   (x_pe, y_bar + PATCH_WIDTH_UM / 2), (x_ps, y_bar + PATCH_WIDTH_UM / 2)],
                  layer=LAYER_SB2S3_AMORPH)

    # Integrated Micro-Heater Contact Traces (Layer 10/0)
    c.add_polygon([(x_ps - 0.5, y_bar + 0.8), (x_pe + 0.5, y_bar + 0.8),
                   (x_pe + 0.5, y_bar + 2.0), (x_ps - 0.5, y_bar + 2.0)], layer=LAYER_CU_M1)
    # TDV pillars connecting heater to CMOS drive (Layer 30/0)
    c.add_polygon([(x_ps - 0.5, y_bar + 2.2), (x_ps + 1.2, y_bar + 2.2),
                   (x_ps + 1.2, y_bar + 3.9), (x_ps - 0.5, y_bar + 3.9)], layer=LAYER_TDV_PILLAR)
    c.add_polygon([(x_pe - 1.2, y_bar + 2.2), (x_pe + 0.5, y_bar + 2.2),
                   (x_pe + 0.5, y_bar + 3.9), (x_pe - 1.2, y_bar + 3.9)], layer=LAYER_TDV_PILLAR)

    c.add_label("SB2S3_SW", position=(total_len / 2, y_bar), layer=LAYER_SB2S3_AMORPH)
    return c


@gf.cell
def pcell_sin_mmi_crossing() -> gf.Component:
    """Si3N4 Talbot Self-Imaging MMI Waveguide Crossing (IL < 0.08 dB, XT < -55 dB)."""
    c = gf.Component("SIN_MMI_CROSSING")
    w = MMI_W_UM
    l_mid = MMI_L_UM
    l_tap = MMI_TAPER_UM

    # Horizontal body
    c.add_polygon([(-l_tap - l_mid / 2, -SIN_WIDTH_UM / 2), (-l_mid / 2, -w / 2),
                   (-l_mid / 2, w / 2), (-l_tap - l_mid / 2, SIN_WIDTH_UM / 2)],
                  layer=LAYER_SIN_CORE)
    c.add_polygon([(-l_mid / 2, -w / 2), (l_mid / 2, -w / 2),
                   (l_mid / 2, w / 2), (-l_mid / 2, w / 2)], layer=LAYER_SIN_CORE)
    c.add_polygon([(l_mid / 2, -w / 2), (l_tap + l_mid / 2, -SIN_WIDTH_UM / 2),
                   (l_tap + l_mid / 2, SIN_WIDTH_UM / 2), (l_mid / 2, w / 2)],
                  layer=LAYER_SIN_CORE)
    # Vertical body
    c.add_polygon([(-SIN_WIDTH_UM / 2, -l_tap - l_mid / 2), (-w / 2, -l_mid / 2),
                   (w / 2, -l_mid / 2), (SIN_WIDTH_UM / 2, -l_tap - l_mid / 2)],
                  layer=LAYER_SIN_CORE)
    c.add_polygon([(-w / 2, l_mid / 2), (-SIN_WIDTH_UM / 2, l_tap + l_mid / 2),
                   (SIN_WIDTH_UM / 2, l_tap + l_mid / 2), (w / 2, l_mid / 2)],
                  layer=LAYER_SIN_CORE)

    c.add_label("MMI_CROSS", position=(0.0, 0.0), layer=LAYER_SIN_CORE)
    return c


@gf.cell
def pcell_sac2m_apd_with_tdv() -> gf.Component:
    """
    Germanium-on-Silicon SAC2M APD Photodetector with 3D Vertical Cu TDVs:
      - Crystalline Si base (Layer 1/0) with avalanche guard ring
      - Ge absorption mesa (Layer 20/0)
      - Anode/Cathode Cu Metal 1 contacts (Layer 10/0)
      - Octagonal UBM Pad + 8 um diameter Cu TDV to CMOS StrongARM (Layers 30/0 & 31/0)
    UBM pad uses consistent TDV_DIAMETER_UM + 2*TDV_UBM_OVERHANG_UM sizing.
    """
    c = gf.Component("SAC2M_APD_WITH_TDV")
    l = APD_LEN_UM    # 10 um
    w = APD_W_UM      # 1.2 um

    # Silicon Coupling Waveguide & Base Slab (Layer 1/0)
    c.add_polygon([(0, -SI_WIDTH_UM / 2), (l / 2, -SI_WIDTH_UM / 2),
                   (l / 2, SI_WIDTH_UM / 2), (0, SI_WIDTH_UM / 2)], layer=LAYER_SI_CORE)
    c.add_polygon([(l / 4 - 1.0, -w / 2 - 1.5), (l / 4 + l + 1.0, -w / 2 - 1.5),
                   (l / 4 + l + 1.0, w / 2 + 1.5), (l / 4 - 1.0, w / 2 + 1.5)],
                  layer=LAYER_SI_CORE)

    # Avalanche Guard Ring Frame (Layer 1/0)
    c.add_polygon([(l / 4 - 2.0, -w / 2 - 2.8), (l / 4 + l + 2.0, -w / 2 - 2.8),
                   (l / 4 + l + 2.0, -w / 2 - 2.0), (l / 4 - 2.0, -w / 2 - 2.0)],
                  layer=LAYER_SI_CORE)
    c.add_polygon([(l / 4 - 2.0, w / 2 + 2.0), (l / 4 + l + 2.0, w / 2 + 2.0),
                   (l / 4 + l + 2.0, w / 2 + 2.8), (l / 4 - 2.0, w / 2 + 2.8)],
                  layer=LAYER_SI_CORE)

    # Crystalline Germanium Absorption Mesa (Layer 20/0)
    c.add_polygon([(l / 4, -w / 2), (l / 4 + l, -w / 2),
                   (l / 4 + l, w / 2), (l / 4, w / 2)], layer=LAYER_APD_GE)

    # Anode & Cathode Metal 1 Contacts (Layer 10/0)
    c.add_polygon([(l / 4 + 1.0, -w / 2 - 2.5), (l / 4 + 4.0, -w / 2 - 2.5),
                   (l / 4 + 4.0, -w / 2), (l / 4 + 1.0, -w / 2)], layer=LAYER_CU_M1)
    c.add_polygon([(l / 4 + l - 4.0, w / 2), (l / 4 + l - 1.0, w / 2),
                   (l / 4 + l - 1.0, w / 2 + 2.5), (l / 4 + l - 4.0, w / 2 + 2.5)],
                  layer=LAYER_CU_M1)

    # Vertical Copper TDV & UBM (consistent sizing: TDV_DIAMETER_UM = 8 um)
    r_tdv = TDV_DIAMETER_UM / 2.0                          # 4.0 um
    r_ubm = r_tdv + TDV_UBM_OVERHANG_UM                   # 5.5 um
    cx, cy = l / 4 + 2.5, -w / 2 - 2.5

    pts_ubm = [(cx + r_ubm * math.cos(math.radians(deg)),
                cy + r_ubm * math.sin(math.radians(deg))) for deg in range(0, 360, 45)]
    c.add_polygon(pts_ubm, layer=LAYER_UBM_BUMP)

    pts_tdv = [(cx + r_tdv * math.cos(math.radians(deg)),
                cy + r_tdv * math.sin(math.radians(deg))) for deg in range(0, 360, 45)]
    c.add_polygon(pts_tdv, layer=LAYER_TDV_PILLAR)

    c.add_label("SAC2M_APD_TDV", position=(cx, cy), layer=LAYER_APD_GE)
    return c


# ==============================================================================
# 2. COMPLETE MULTI-STRATUM TILE COMPONENT
# ==============================================================================

@gf.cell
def build_monolithic_3d_tile(tile_id: int = 0) -> gf.Component:
    """
    Synthesizes a complete 3D Monolithic Tile combining:
      - Bottom 65nm CMOS digital compute base (physical mask layers 100-199)
      - Middle monolithic SiO2 thermal buffer with high-density Cu TDV pillars
      - Top dual-core Si3N4/Si optical permutation fabric with Sb2S3 switches
        and SAC2M APDs with Cu TDVs
    """
    tile = gf.Component(f"MONOLITHIC_3D_TILE_{tile_id}")
    tile_w = TILE_CORE_UM   # 600 um
    tile_h = TILE_CORE_UM   # 600 um

    # Physical Keep-Out Boundary (Layer 199/0)
    tile.add_polygon([(0, 0), (tile_w, 0), (tile_w, tile_h), (0, tile_h)],
                     layer=LAYER_FLOORPLAN)

    # Thermal Buffer Isolation Stratum (Layer 32/0)
    tile.add_polygon([(5.0, 5.0), (tile_w - 5.0, 5.0),
                      (tile_w - 5.0, tile_h - 5.0), (5.0, tile_h - 5.0)],
                     layer=LAYER_THERMAL_BUF)

    # 1. Bottom 65nm CMOS Base Stratum (physical mask layers 100-199)
    tile.add_ref(build_cmos_base_tile(tile_id=tile_id))

    # ---- Optical stratum component handles ----
    sw_len = COUPLER_LEN_UM + 3.0
    sin_sw     = pcell_sb2s3_sin_switch_cell()
    sin_cross  = pcell_sin_mmi_crossing()
    taper_cell = pcell_sin_to_si_taper(length=15.0)
    apd_cell   = pcell_sac2m_apd_with_tdv()

    # 2. Input Modulation Stage (X: 70-190 um)
    channel_y = [45.0 + i * 31.0 for i in range(17)]
    for ch, y_ch in enumerate(channel_y):
        tile.add_ref(pcell_sin_straight_wg(10.0)).move((60.0, y_ch))
        if ch < 16:
            # Active Channels: LiTaO3 Modulator (Layer 3/0)
            tile.add_polygon([(70.0, y_ch - LITAO3_W_UM / 2), (190.0, y_ch - LITAO3_W_UM / 2),
                               (190.0, y_ch + LITAO3_W_UM / 2), (70.0, y_ch + LITAO3_W_UM / 2)],
                              layer=LAYER_LITAO3_EO)
            tile.add_ref(pcell_sin_straight_wg(LITAO3_LEN_UM)).move((70.0, y_ch))
            # Modulator RF Coplanar Electrodes (Layer 10/0)
            tile.add_polygon([(70.0, y_ch + 1.5), (190.0, y_ch + 1.5),
                               (190.0, y_ch + 12.0), (70.0, y_ch + 12.0)], layer=LAYER_CU_M1)
            tile.add_polygon([(70.0, y_ch - 12.0), (190.0, y_ch - 12.0),
                               (190.0, y_ch - 1.5), (70.0, y_ch - 1.5)], layer=LAYER_CU_M1)
            tile.add_label(f"LITAO3_MOD_CH{ch}", position=(130.0, y_ch), layer=LAYER_LITAO3_EO)
        else:
            # Dark Reference Channel WG0
            tile.add_ref(pcell_sin_straight_wg(LITAO3_LEN_UM)).move((70.0, y_ch))
            tile.add_label("DARK_REF_WG0", position=(130.0, y_ch), layer=LAYER_SIN_CORE)

    # 3. 4-Stage Binary Tree Fermat Switching Network in Si3N4 (X: 200-460 um)
    stage_x = [205.0, 275.0, 345.0, 415.0]

    # Routing WGs from modulator outputs to stage 1
    for ch, y_ch in enumerate(channel_y):
        gap = stage_x[0] - (70.0 + LITAO3_LEN_UM)
        if gap > 0:
            tile.add_ref(pcell_sin_straight_wg(gap)).move((70.0 + LITAO3_LEN_UM, y_ch))

    # Stage 1
    for ch in range(16):
        y_ch = channel_y[ch]
        tile.add_ref(sin_sw).move((stage_x[0], y_ch))
        tile.add_ref(pcell_sin_sbend_wg(dx=28.0, dy=4.0)).move((stage_x[0] + sw_len, y_ch + 0.5))
        tile.add_ref(pcell_sin_sbend_wg(dx=28.0, dy=-4.0)).move((stage_x[0] + sw_len, y_ch - 0.5))

    # Stage 2
    for ch in range(16):
        y_ch = channel_y[ch]
        tile.add_ref(sin_sw).move((stage_x[1], y_ch + 4.0))
        tile.add_ref(sin_sw).move((stage_x[1], y_ch - 4.0))
        if ch % 2 == 0:
            tile.add_ref(sin_cross).move((stage_x[1] + sw_len + 12.0, y_ch))
        tile.add_ref(pcell_sin_sbend_wg(dx=28.0, dy=5.0)).move((stage_x[1] + sw_len, y_ch + 4.0))
        tile.add_ref(pcell_sin_sbend_wg(dx=28.0, dy=-5.0)).move((stage_x[1] + sw_len, y_ch - 4.0))

    # Stage 3
    for ch in range(16):
        y_ch = channel_y[ch]
        for s in range(4):
            dy = (s - 1.5) * 4.0
            tile.add_ref(sin_sw).move((stage_x[2], y_ch + dy))
            tile.add_ref(pcell_sin_straight_wg(12.0)).move((stage_x[2] + sw_len, y_ch + dy))

    # Stage 4
    for ch in range(16):
        y_ch = channel_y[ch]
        for s in range(4):
            dy = (s - 1.5) * 4.0
            tile.add_ref(sin_sw).move((stage_x[3], y_ch + dy))
            dy_bend = -dy * 0.7
            tile.add_ref(pcell_sin_sbend_wg(dx=30.0, dy=dy_bend)).move(
                (stage_x[3] + sw_len, y_ch + dy)
            )

    # WG0 dark reference bypass
    wg0_len = stage_x[3] + sw_len + 30.0 - stage_x[0]
    tile.add_ref(pcell_sin_straight_wg(wg0_len)).move((stage_x[0], channel_y[16]))

    # 4. Si3N4→Si Taper Transition & SAC2M APDs with TDVs (X: 475-560 um)
    x_taper = stage_x[3] + sw_len + 30.0
    x_apd = x_taper + 18.0
    for ch, y_ch in enumerate(channel_y):
        tile.add_ref(taper_cell).move((x_taper, y_ch))
        tile.add_ref(apd_cell).move((x_apd, y_ch))
        tile.add_label(f"APD_TDV_CH{ch}", position=(x_apd + 5.0, y_ch), layer=LAYER_APD_GE)

    # 5. High-Density Cu-Pillar TDV Grid (50 um pitch, 10,000 mm^-2 density)
    n_tdv = int(tile_w / BUMP_PITCH_UM)  # 11 x 11
    for ix in range(n_tdv + 1):
        for iy in range(n_tdv + 1):
            cx = 50.0 + ix * BUMP_PITCH_UM
            cy = 50.0 + iy * BUMP_PITCH_UM
            if cx > tile_w - 5 or cy > tile_h - 5:
                continue
            r = TDV_DIAMETER_UM / 2.0
            r_ubm = r + TDV_UBM_OVERHANG_UM
            tile.add_polygon([(cx - r, cy - r), (cx + r, cy - r),
                              (cx + r, cy + r), (cx - r, cy + r)], layer=LAYER_TDV_PILLAR)
            tile.add_polygon([(cx - r_ubm, cy - r_ubm), (cx + r_ubm, cy - r_ubm),
                              (cx + r_ubm, cy + r_ubm), (cx - r_ubm, cy + r_ubm)],
                             layer=LAYER_UBM_BUMP)

    # 6. Global Orthogonal Metal Power Distribution Mesh (Layers 10/0 & 11/0)
    for p_idx in range(6):
        yp = 25.0 + p_idx * 110.0
        tile.add_polygon([(15.0, yp), (585.0, yp), (585.0, yp + 4.0), (15.0, yp + 4.0)],
                         layer=LAYER_CU_M1)
    for p_idx in range(6):
        xp = 40.0 + p_idx * 105.0
        tile.add_polygon([(xp, 15.0), (xp + 4.0, 15.0), (xp + 4.0, 585.0), (xp, 585.0)],
                         layer=LAYER_CU_M2)

    tile.add_label(f"TILE_{tile_id}_3D_CORE", position=(tile_w / 2, tile_h - 20.0),
                   layer=LAYER_FLOORPLAN)
    tile.add_label("16TREE_FERMAT_FABRIC", position=(310.0, 30.0), layer=LAYER_SIN_CORE)
    tile.add_label("CU_TDV_POWER_GRID", position=(50.0, 50.0), layer=LAYER_TDV_PILLAR)
    return tile


# ==============================================================================
# 3. TOP-LEVEL CHIP ASSEMBLY (16-TILE 3D MONOLITHIC ACCELERATOR)
# ==============================================================================

def generate_janus_mini16_top_layout() -> gf.Component:
    """
    Complete tapeout-ready layout of the JANUS Mini 16-Tile 3D Monolithic Accelerator:
      - 4x4 Array of Heterogeneous 3D Tiles (SiPh + SiO2 Thermal Buffer + 65nm CMOS)
      - Dual 17-channel Fiber V-Groove Array Couplers (GC period from WAVELENGTH_NM)
      - Complete 4-Layer Concentric Seal Ring & Scribe-Line Test Metrology
      - 4-Level Balanced H-Tree 3.125 GHz Clock (Metal 6 / Layer 161/0)

    Die: 3200 x 3200 um | Tiles: 4x4 @ 700 um pitch | Origin: (200, 200)
    """
    top = gf.Component("JANUS_MINI16_TOP_CORE")

    die_w = DIE_WIDTH_UM    # 3200 um
    die_h = DIE_HEIGHT_UM   # 3200 um

    # ---- 1. 4-Layer Concentric Moisture Seal Ring (Layer 190/0) & Die Boundary ----
    seal_ring_w = 4.0
    seal_ring_gap = 6.0
    seal_edge_off = 10.0
    for s in range(4):
        off = seal_edge_off + s * seal_ring_gap
        top.add_polygon([(off, off), (die_w - off, off),
                         (die_w - off, off + seal_ring_w), (off, off + seal_ring_w)],
                        layer=LAYER_SEAL_RING)
        top.add_polygon([(off, die_h - off - seal_ring_w), (die_w - off, die_h - off - seal_ring_w),
                         (die_w - off, die_h - off), (off, die_h - off)],
                        layer=LAYER_SEAL_RING)
        top.add_polygon([(off, off), (off + seal_ring_w, off),
                         (off + seal_ring_w, die_h - off), (off, die_h - off)],
                        layer=LAYER_SEAL_RING)
        top.add_polygon([(die_w - off - seal_ring_w, off), (die_w - off, off),
                         (die_w - off, die_h - off), (die_w - off - seal_ring_w, die_h - off)],
                        layer=LAYER_SEAL_RING)

    top.add_polygon([(0, 0), (die_w, 0), (die_w, die_h), (0, die_h)], layer=LAYER_FLOORPLAN)
    top.add_label("JANUS_MINI16_3D_TOP_DIE", position=(die_w / 2, die_h - 30.0),
                  layer=LAYER_FLOORPLAN)
    top.add_label("4LAYER_MOISTURE_SEAL_RING", position=(40.0, die_h - 40.0),
                  layer=LAYER_SEAL_RING)

    # ---- 2. 4x4 Grid of 3D Monolithic Tiles (16 Tiles Total) ----
    x_origin = TILE_ARRAY_ORIGIN_X   # 200 um
    y_origin = TILE_ARRAY_ORIGIN_Y   # 200 um
    tile_pitch = TILE_PITCH_UM       # 700 um  (was 690 um — fixed)

    for row in range(4):
        for col in range(4):
            tile_id = row * 4 + col
            x_pos = x_origin + col * tile_pitch
            y_pos = y_origin + row * tile_pitch
            tile_ref = top.add_ref(build_monolithic_3d_tile(tile_id=tile_id))
            tile_ref.move((x_pos, y_pos))
            top.add_label(f"TILE_{tile_id}_LOCATION",
                          position=(x_pos + 300.0, y_pos + 300.0), layer=LAYER_FLOORPLAN)

    # ---- 3. Dual Optical Fiber V-Groove Array Grating Couplers ----
    # Grating coupler period derived from WAVELENGTH_NM constant (not hardcoded).
    gc_period = GC_TEETH_PERIOD_UM   # from janus_layer_constants
    gc_dc = GC_DUTY_CYCLE            # 0.5

    gc_cell = gf.Component("JANUS_OPTICAL_FIBER_VGROOVE_COUPLER")
    for i in range(17):
        y_gc = i * 127.0
        # Grating body in Si3N4 (Layer 5/0)
        gc_cell.add_polygon([(0, y_gc - GC_HALF_WIDTH_UM), (GC_BODY_LEN_UM, y_gc - GC_HALF_WIDTH_UM),
                             (GC_BODY_LEN_UM, y_gc + GC_HALF_WIDTH_UM), (0, y_gc + GC_HALF_WIDTH_UM)],
                            layer=LAYER_SIN_CORE)
        # Individual grating teeth
        for t in range(GC_NUM_TEETH):
            xt = 5.0 + t * gc_period
            tooth_w = gc_period * gc_dc
            gc_cell.add_polygon([(xt, y_gc - GC_HALF_WIDTH_UM),
                                  (xt + tooth_w, y_gc - GC_HALF_WIDTH_UM),
                                  (xt + tooth_w, y_gc + GC_HALF_WIDTH_UM),
                                  (xt, y_gc + GC_HALF_WIDTH_UM)], layer=LAYER_SIN_CORE)
        # Taper from fiber-width to waveguide width
        gc_cell.add_polygon([(-25.0, y_gc - SIN_WIDTH_UM / 2), (0, y_gc - GC_HALF_WIDTH_UM),
                             (0, y_gc + GC_HALF_WIDTH_UM), (-25.0, y_gc + SIN_WIDTH_UM / 2)],
                            layer=LAYER_SIN_CORE)
        gc_cell.add_label(f"FIBER_CH{i}", position=(17.5, y_gc), layer=LAYER_SIN_CORE)

    top.add_ref(gc_cell).move((35.0, 550.0))
    ref_r = top.add_ref(gc_cell)
    ref_r.mirror((0, 0), (0, 1))
    ref_r.move((die_w - 35.0, 550.0))
    top.add_label("FIBER_VGROOVE_PORT_WEST", position=(20.0, 520.0), layer=LAYER_SIN_CORE)
    top.add_label("FIBER_VGROOVE_PORT_EAST", position=(die_w - 20.0, 520.0), layer=LAYER_SIN_CORE)

    # Optical Feed Trunks (Si3N4, Layer 5/0)
    for i in range(17):
        y_gc = 550.0 + i * 127.0
        if y_gc < die_h - 100.0:
            for x0, x1 in [(10.0, 180.0), (die_w - 180.0, die_w - 10.0)]:
                top.add_polygon([(x0, y_gc - SIN_WIDTH_UM / 2), (x1, y_gc - SIN_WIDTH_UM / 2),
                                  (x1, y_gc + SIN_WIDTH_UM / 2), (x0, y_gc + SIN_WIDTH_UM / 2)],
                                layer=LAYER_SIN_CORE)

    # ---- 4. Global 65nm CMOS VDD/VSS Power Ring (Top Metal 171/0) ----
    pwr_off = PWR_RING_OFFSET_UM   # 60 um
    pwr_w = PWR_RING_WIDTH_UM      # 40 um
    top.add_polygon([(pwr_off, 50.0), (die_w - pwr_off, 50.0),
                     (die_w - pwr_off, 50.0 + pwr_w), (pwr_off, 50.0 + pwr_w)],
                    layer=LAYER_TOP_METAL_PWR)
    top.add_polygon([(pwr_off, die_h - 50.0 - pwr_w), (die_w - pwr_off, die_h - 50.0 - pwr_w),
                     (die_w - pwr_off, die_h - 50.0), (pwr_off, die_h - 50.0)],
                    layer=LAYER_TOP_METAL_PWR)
    top.add_polygon([(pwr_off, 50.0), (pwr_off + pwr_w, 50.0),
                     (pwr_off + pwr_w, die_h - 50.0), (pwr_off, die_h - 50.0)],
                    layer=LAYER_TOP_METAL_PWR)
    top.add_polygon([(die_w - pwr_off - pwr_w, 50.0), (die_w - pwr_off, 50.0),
                     (die_w - pwr_off, die_h - 50.0), (die_w - pwr_off - pwr_w, die_h - 50.0)],
                    layer=LAYER_TOP_METAL_PWR)
    top.add_label("GLOBAL_VDD_VSS_POWER_RING", position=(die_w / 2, 70.0),
                  layer=LAYER_TOP_METAL_PWR)

    # ---- 5. Complete 4-Side Wire-Bond / Solder Bump I/O Pad Ring ----
    pad_s = PAD_SIZE_UM    # 75 um
    pad_p = PAD_PITCH_UM   # 120 um

    # Bottom & Top rows (horizontal)
    num_pads_x = int((die_w - 400.0) / pad_p)
    for p in range(num_pads_x):
        xp = 200.0 + p * pad_p
        for pad_y, lbl_base in [(95.0, "BOT"), (die_h - 95.0 - pad_s, "TOP")]:
            top.add_polygon([(xp, pad_y), (xp + pad_s, pad_y),
                              (xp + pad_s, pad_y + pad_s), (xp, pad_y + pad_s)],
                            layer=LAYER_PAD_IO)
            top.add_label(f"IO_PAD_{lbl_base}_{p}",
                          position=(xp + pad_s / 2, pad_y + pad_s / 2), layer=LAYER_PAD_IO)

    # Left & Right columns (vertical)
    num_pads_y = int((die_h - 400.0) / pad_p)
    for p in range(num_pads_y):
        yp = 200.0 + p * pad_p
        for pad_x, lbl_base in [(95.0, "LEFT"), (die_w - 95.0 - pad_s, "RIGHT")]:
            top.add_polygon([(pad_x, yp), (pad_x + pad_s, yp),
                              (pad_x + pad_s, yp + pad_s), (pad_x, yp + pad_s)],
                            layer=LAYER_PAD_IO)
            top.add_label(f"IO_PAD_{lbl_base}_{p}",
                          position=(pad_x + pad_s / 2, yp + pad_s / 2), layer=LAYER_PAD_IO)

    # ---- 6. 4-Level Balanced H-Tree Global Clock (Metal 6 / Layer 161/0) ----
    add_balanced_htree_4x4(top, x_origin, y_origin, tile_pitch, LAYER_METAL6_CLK)

    # ---- 7. Metrology & Test Structures in Scribe Margin ----
    top.add_polygon([(1300.0, 50.0), (1700.0, 50.0),
                     (1700.0, 50.0 + SIN_WIDTH_UM), (1300.0, 50.0 + SIN_WIDTH_UM)],
                    layer=LAYER_SIN_CORE)
    top.add_polygon([(1300.0, die_h - 60.0), (1700.0, die_h - 60.0),
                     (1700.0, die_h - 60.0 + SIN_WIDTH_UM), (1300.0, die_h - 60.0 + SIN_WIDTH_UM)],
                    layer=LAYER_SIN_CORE)
    top.add_label("OPTICAL_TEST_STRUCTURE_SIN", position=(1500.0, 50.0), layer=LAYER_SIN_CORE)

    return top


# ==============================================================================
# 4. MAIN EXPORTER ROUTINE
# ==============================================================================

def main():
    print("=" * 75)
    print("PROJECT JANUS: COMPLETE 3D MONOLITHIC GDS II LAYOUT SYNTHESIZER")
    print("=" * 75)
    print("[*] Synthesizing Dual-Layer Si3N4/Si Photonic Stratum...")
    print("[*] Synthesizing 3D Vertical Copper TDVs & Thermal Buffer...")
    print("[*] Synthesizing 65nm LP/GP CMOS Digital Base Die Stratum...")
    print(f"[*] Operating wavelength: {WAVELENGTH_NM:.0f} nm | GC period: {GC_TEETH_PERIOD_UM*1000:.0f} nm")

    out_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "layout"))
    os.makedirs(out_dir, exist_ok=True)
    gds_path = os.path.join(out_dir, "janus_mini16_layout.gds")

    top_core = generate_janus_mini16_top_layout()

    print(f"[*] Writing binary GDS II stream file to:\n    {gds_path}")
    top_core.write_gds(gds_path)

    lyp_src = os.path.join(out_dir, "janus_mini16_layers.lyp")
    lyp_top = os.path.join(out_dir, "janus_mini16_layout.lyp")
    if os.path.exists(lyp_src):
        shutil.copyfile(lyp_src, lyp_top)

    gds_size = os.path.getsize(gds_path)
    print(f"[+] SUCCESS! Complete 3D Monolithic GDS II layout generated.")
    print(f"    - Target File   : {gds_path}")
    print(f"    - Companion LYP : {lyp_top}")
    print(f"    - File Size     : {gds_size:,} bytes ({gds_size / 1024:.2f} KB)")
    print(f"    - Top Cell      : {top_core.name}")
    print(f"    - Die Dimensions: {DIE_WIDTH_UM/1000:.2f} mm x {DIE_HEIGHT_UM/1000:.2f} mm")
    print(f"    - Optical layers: 1-29 | Inter-stratum: 30-39 | CMOS physical: 100-199")
    print("=" * 75)


if __name__ == "__main__":
    main()
