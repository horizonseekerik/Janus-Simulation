# JANUS Mini-16 Photonic & 3D Monolithic Layout Directory

This directory houses the physical GDS II stream files, generator scripts, and mask layout definitions for the JANUS Mini 16-Tile Monolithic 3D Planar MVP.

## Layout Artifacts
- **`janus_mini16_layout.gds`**: Primary GDS II stream file containing the complete 3D monolithic mask stack:
  - **Optical & Photonic Stratum (Top)**:
    - **Layer 5/0 (`LAYER_SIN_CORE`)**: Low-Loss Silicon Nitride ($\text{Si}_3\text{N}_4$, $800\text{ nm} \times 300\text{ nm}$) primary routing, Talbot MMI crossbars, and 4-stage binary tree switching network ($0.1\ \text{dB/cm}$ propagation loss, zero Two-Photon Absorption).
    - **Layer 1/0 (`LAYER_SI_CORE`)**: Crystalline Silicon ($\text{Si}$, $450\text{ nm} \times 220\text{ nm}$) core sections for epitaxial Germanium seed substrates, interfaced from $\text{Si}_3\text{N}_4$ via adiabatic tapers ($\text{IL} < 0.05\ \text{dB}$).
    - **Layer 3/0 (`LAYER_LITAO3_EO`)**: Thin-Film Lithium Tantalate ($\text{LiTaO}_3$) Electro-Optic Pockels Modulator slabs ($r_{33} \approx 30.5\ \text{pm/V}$).
    - **Layer 4/0 & 4/1 (`LAYER_SB2S3_AMORPH` / `LAYER_SB2S3_CRYST`)**: Non-volatile Antimony Trisulfide ($\text{Sb}_2\text{S}_3$) directional coupler switches.
    - **Layer 10/0 (`LAYER_CU_M1`)**: Metal 1 Copper RF Traveling-Wave Coplanar Electrodes & Micro-Heaters.
    - **Layer 11/0 (`LAYER_CU_M2`)**: Metal 2 Copper Global Power/Clock Mesh.
    - **Layer 20/0 (`LAYER_APD_GE`)**: Separate Absorption, Charge, and Multiplication ($\text{SAC}^2\text{M}$) Germanium Epitaxial Mesas ($1.2\ \mu\text{m} \times 10\ \mu\text{m}$).
  - **3D Heterogeneous Inter-Stratum**:
    - **Layer 30/0 (`LAYER_TDV_PILLAR`)**: Vertical Copper Through-Dielectric Vias ($8\ \mu\text{m}$ diameter, $10,000\ \text{mm}^{-2}$ array density across the $250\ \mu\text{m}\ \text{SiO}_2$ thermal buffer).
    - **Layer 31/0 (`LAYER_UBM_BUMP`)**: Under-Bump Metallization & Micro-Bump array ($50\ \mu\text{m}$ pitch).
    - **Layer 32/0 (`LAYER_THERMAL_BUF`)**: Monolithic $250\ \mu\text{m}\ \text{SiO}_2$ thermal buffer boundary.
  - **65nm LP/GP CMOS Base Die Stratum (Bottom)**:
    - **Layer 40/0 (`LAYER_CMOS_STRONGARM`)**: Regenerative StrongARM sensing latches (1:1 vertically aligned beneath APD TDVs).
    - **Layer 41/0 (`LAYER_CMOS_DESER`)**: 1:32 polyphase time-interleaved deserializer block.
    - **Layer 42/0 (`LAYER_CMOS_SIMD`)**: 32-lane SIMD Wallace-Kogge arithmetic unit.
    - **Layer 43/0 (`LAYER_CMOS_SRAM`)**: 1.5 MB Dual-LUT volatile local SRAM.
    - **Layer 44/0 (`LAYER_CMOS_ROM`)**: 1.5 MB Central non-volatile ROM macro and JIR FSM.
    - **Layer 45/0 (`LAYER_CMOS_ACC160`)**: 160-bit binary carry-save accumulator.
    - **Layer 46/0 (`LAYER_CMOS_THERMAL`)**: JIR thermal diodes and 10-bit $\Delta\Sigma$ ADCs.
  - **Perimeter & Metrology**:
    - **Layer 90/0 (`LAYER_SEAL_RING`)**: 4-Layer Moisture Seal Ring.
    - **Layer 99/0 (`LAYER_FLOORPLAN`)**: Chip Guard Ring & Tile Keep-Out Boundaries.

- **`janus_mini16_cmos_base_layout.gds`**: Standalone GDS II stream file for the complete 65nm LP/GP CMOS digital base die:
  - **Process Node**: Standard 65nm LP/GP CMOS (1P7M to 1P9M BEOL).
  - **Die Footprint**: $3.24\text{ mm} \times 3.20\text{ mm}$ ($10.37\ \text{mm}^2$), matching the top optical die 1:1 vertically.
  - **Mask Layers**:
    - **Layer 1/0 (`LAYER_NW_DIFF`)**: N-Well & Active Silicon Diffusion (P/N OD).
    - **Layer 2/0 (`LAYER_POLY_GATE`)**: 65nm drawn polysilicon gates.
    - **Layer 6/0 (`LAYER_CONTACT`)**: Tungsten contact plugs.
    - **Layer 11/0 (`LAYER_METAL1`)**: Metal 1 local interconnect & StrongARM sense nodes.
    - **Layer 12/0 (`LAYER_VIA1`)**: Via 1 inter-metal plugs & Via-ROM matrix.
    - **Layer 21/0 (`LAYER_METAL2`)**: Metal 2 intra-tile signal routing & memory banks.
    - **Layer 31/0 (`LAYER_METAL3`)**: Metal 3 lane bus & SIMD cross-routing.
    - **Layer 41/0 (`LAYER_METAL4`)**: Metal 4 SRAM wordline/bitline strapping.
    - **Layer 51/0 (`LAYER_METAL5`)**: Metal 5 accumulator & CRT adder bus.
    - **Layer 61/0 (`LAYER_METAL6_CLK`)**: Metal 6 global balanced 3.125 GHz H-Tree clock distribution.
    - **Layer 71/0 (`LAYER_TOP_METAL_PWR`)**: Top thick metal VDD/VSS power mesh and peripheral power ring.
    - **Layer 81/0 (`LAYER_PASSIVATION_UBM`)**: Passivation openings & Under-Bump Metallization (UBM) landing pads for vertical Cu TDVs ($8\ \mu\text{m}$ diameter, $50\ \mu\text{m}$ pitch).
    - **Layer 82/0 (`LAYER_PAD_IO`)**: Standard peripheral wire-bond & solder bump I/O pads ($75\ \mu\text{m}$ pad size).
    - **Layer 90/0 (`LAYER_SEAL_RING`)**: 4-layer moisture barrier chip seal ring.
    - **Layer 99/0 (`LAYER_FLOORPLAN`)**: Die boundary & tile keep-out margins.
  - **Top Cell**: `JANUS_MINI16_CMOS_BASE_DIE` (24 hierarchical cells, 866 shapes across 19 mask layers).

- **`generate_mini16_gds.py`**: Automated physical layout synthesis script for the 3D heterogeneous stack.
- **`generate_cmos_base_gds.py`**: Dedicated automated physical synthesis script for the 65nm LP/GP CMOS base die.

## Layout Verification & Dimensions
- **Total Die Footprint**: 3.24 mm x 3.20 mm (10.37 mm² monolithic active die)
- **3D Top Cell**: `JANUS_MINI16_TOP_CORE` (Complete 3D heterogeneous stack)
- **CMOS Top Cell**: `JANUS_MINI16_CMOS_BASE_DIE` (Standalone 65nm CMOS digital base die)
- **Tile Architecture**: 16 Fermat residue tiles with 4-stage binary switch trees (240 $\text{Sb}_2\text{S}_3$ switches/multiplier)
- **Optical I/O**: Dual 17-channel standard Fiber V-Groove Array (127 µm pitch)
- **Vertical Interconnect**: Cu TDVs linking APD anodes to CMOS StrongARM regenerative latches ($R_{\text{via}} < 0.05\ \Omega$, $C_{\text{via}} < 4.2\ \text{fF}$)

## Relative Path in Registry
Referenced from `janus_mini16_sim/configs/mini_16t_constants.py` via:
`../layout/janus_mini16_layout.gds`
`../layout/janus_mini16_cmos_base_layout.gds`


