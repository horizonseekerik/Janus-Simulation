# JANUS Mini-16 Photonic & 3D Monolithic Layout Directory

This directory houses the physical GDS II stream files, generator scripts, and mask layout definitions for the JANUS Mini 16-Tile Monolithic 3D Planar MVP.

## Layer Number Convention (v2 — Collision-Free)

All layer numbers are defined in **`janus_layer_constants.py`** (single source of truth).
No two strata share a GDS (layer, datatype) pair:

| Range | Stratum |
|-------|---------|
| 1 – 29 | Top SiPh / Si₃N₄ Optical |
| 30 – 39 | 3D Inter-Stratum Vertical Interconnects |
| 40 – 49 | Abstract CMOS Block Annotations (floorplan only) |
| 100 – 199 | Physical 65nm LP/GP CMOS Mask Layers |
| 190, 199 | Die Perimeter & Metrology (shared) |

---

## Layout Artifacts

### `janus_mini16_layout.gds` — Complete 3D Monolithic Stack

  - **Optical & Photonic Stratum (Top)**:
    - **Layer 5/0 (`LAYER_SIN_CORE`)**: Low-Loss Si₃N₄ (800×300 nm strip, 0.1 dB/cm) primary routing, Talbot MMI crossbars, 4-stage binary tree switching network.
    - **Layer 1/0 (`LAYER_SI_CORE`)**: Crystalline Si (450×220 nm) APD mesa base & taper termination (IL < 0.05 dB).
    - **Layer 3/0 (`LAYER_LITAO3_EO`)**: Thin-Film LiTaO₃ Pockels Modulators ($r_{33} \approx 30.5$ pm/V).
    - **Layer 4/0 & 4/1 (`LAYER_SB2S3_AMORPH` / `LAYER_SB2S3_CRYST`)**: Non-volatile Sb₂S₃ directional coupler switches.
    - **Layer 10/0 (`LAYER_CU_M1`)**: Cu Metal 1 RF Coplanar Electrodes & Micro-Heaters.
    - **Layer 11/0 (`LAYER_CU_M2`)**: Cu Metal 2 Global Power/Clock Mesh.
    - **Layer 20/0 (`LAYER_APD_GE`)**: SAC²M Ge Epitaxial Mesas (1.2 µm × 10 µm).
  - **3D Heterogeneous Inter-Stratum**:
    - **Layer 30/0 (`LAYER_TDV_PILLAR`)**: Vertical Cu TDVs (8 µm diam, 10,000 mm⁻² density).
    - **Layer 31/0 (`LAYER_UBM_BUMP`)**: UBM & Micro-Bump array (50 µm pitch).
    - **Layer 32/0 (`LAYER_THERMAL_BUF`)**: 250 µm SiO₂ Thermal Buffer Boundary.
  - **65nm LP/GP CMOS Base Die — Abstract Blocks (Layers 40–49)**:
    - **40/0 (`LAYER_ARCH_STRONGARM`)**: StrongARM sensing latches (floorplan outline).
    - **41/0–46/0**: Deserializer, SIMD, SRAM, ROM, Accumulator, Thermal ADC blocks.
  - **65nm LP/GP CMOS Base Die — Physical Mask Layers (100–199)**:
    - See `janus_mini16_cmos_base_layout.gds` section below for the full map.
  - **Perimeter & Metrology**:
    - **Layer 190/0 (`LAYER_SEAL_RING`)**: 4-Layer Concentric Moisture Seal Ring.
    - **Layer 199/0 (`LAYER_FLOORPLAN`)**: Die Guard Ring & Tile Keep-Out Boundaries.

---

### `janus_mini16_cmos_base_layout.gds` — Standalone 65nm CMOS Base Die

  - **Process Node**: Standard 65nm LP/GP CMOS (1P7M to 1P9M BEOL).
  - **Die Footprint**: 3.20 mm × 3.20 mm (10.24 mm²) — identical to top optical die (1:1 vertical alignment).
  - **Tile Array**: 4×4 @ 700 µm pitch, origin (200, 200) µm — consistent with 3D GDS.
  - **Physical Mask Layers (100-199 range)**:

| Layer | Symbol | Purpose |
|-------|--------|---------|
| 101/0 | `LAYER_NW_DIFF` | N-Well & Active Silicon Diffusion (P/N OD) |
| 102/0 | `LAYER_POLY_GATE` | 65nm drawn polysilicon gates |
| 106/0 | `LAYER_CONTACT` | Tungsten contact plugs |
| 111/0 | `LAYER_METAL1` | Metal 1 local interconnect & StrongARM sense nodes |
| 112/0 | `LAYER_VIA1` | Via 1 & Via-ROM matrix |
| 121/0 | `LAYER_METAL2` | Metal 2 intra-tile signal routing |
| 122/0 | `LAYER_VIA2` | Via 2 |
| 131/0 | `LAYER_METAL3` | Metal 3 lane bus & SIMD cross-routing |
| 132/0 | `LAYER_VIA3` | Via 3 |
| 141/0 | `LAYER_METAL4` | Metal 4 SRAM wordline/bitline strapping |
| 142/0 | `LAYER_VIA4` | Via 4 |
| 151/0 | `LAYER_METAL5` | Metal 5 accumulator & CRT adder bus |
| 152/0 | `LAYER_VIA5` | Via 5 |
| 161/0 | `LAYER_METAL6_CLK` | Metal 6 global 4-level balanced H-Tree (3.125 GHz) |
| 162/0 | `LAYER_VIA6` | Via 6 |
| 171/0 | `LAYER_TOP_METAL_PWR` | Top thick metal VDD/VSS power mesh & power ring |
| 181/0 | `LAYER_PASSIVATION_UBM` | Passivation openings & UBM landing pads (8 µm, 50 µm pitch) |
| 182/0 | `LAYER_PAD_IO` | 4-side wire-bond & solder bump I/O pads (75 µm, 120 µm pitch) |
| 190/0 | `LAYER_SEAL_RING` | 4-layer concentric moisture barrier chip seal ring |
| 199/0 | `LAYER_FLOORPLAN` | Die boundary & tile keep-out margins |

  - **Top Cell**: `JANUS_MINI16_CMOS_BASE_DIE`

---

## Generator Scripts

- **`janus_layer_constants.py`**: Single source-of-truth for all layer numbers, datatypes, and canonical physical dimensions.
- **`generate_mini16_gds.py`**: Automated physical layout synthesis for the complete 3D heterogeneous stack.
- **`generate_cmos_base_gds.py`**: Dedicated synthesis script for the standalone 65nm LP/GP CMOS base die.

---

## Layout Verification & Dimensions

| Parameter | Value |
|-----------|-------|
| Total Die Footprint | 3.20 mm × 3.20 mm (10.24 mm² — both strata) |
| 3D Top Cell | `JANUS_MINI16_TOP_CORE` |
| CMOS Top Cell | `JANUS_MINI16_CMOS_BASE_DIE` |
| Tile Array | 4×4 × 700 µm pitch, origin (200, 200) µm |
| Tile Core | 600 µm × 600 µm |
| Clock Distribution | 4-level balanced H-tree (levels 1–4 trunk→terminal) |
| Optical I/O | Dual 17-channel Fiber V-Groove Array (127 µm pitch) |
| Vertical Interconnect | Cu TDVs (8 µm ⌀) to CMOS StrongARM latches ($R_\text{via} < 0.05\ \Omega$, $C_\text{via} < 4.2\ \text{fF}$) |
| Grating Coupler | 630 nm period, 50% duty cycle, 22 teeth (1310 nm / 2nd-order Si₃N₄) |

## Relative Path in Registry

Referenced from `janus_mini16_sim/configs/mini_16t_constants.py` via:
```
../layout/janus_mini16_layout.gds
../layout/janus_mini16_cmos_base_layout.gds
```
