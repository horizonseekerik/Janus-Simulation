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

- **`generate_mini16_gds.py`**: Automated physical layout synthesis script built on `gdsfactory` and `klayout`.

## Layout Verification & Dimensions
- **Total Die Footprint**: 3.24 mm x 3.20 mm (10.37 mm² monolithic active die)
- **Top Cell**: `JANUS_MINI16_TOP_CORE` (36 hierarchically instantiated subcells)
- **Tile Architecture**: 16 Fermat residue tiles with 4-stage binary switch trees (240 $\text{Sb}_2\text{S}_3$ switches/multiplier)
- **Optical I/O**: Dual 17-channel standard Fiber V-Groove Array (127 µm pitch)
- **Vertical Interconnect**: Cu TDVs linking APD anodes to CMOS StrongARM regenerative latches ($R_{\text{via}} < 0.05\ \Omega$, $C_{\text{via}} < 4.2\ \text{fF}$)

## Relative Path in Registry
Referenced from `janus_mini16_sim/configs/mini_16t_constants.py` via:
`../layout/janus_mini16_layout.gds`

