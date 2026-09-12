# JANUS Mini-16 Photonic Layout Directory

This directory houses the physical GDS II stream files, generator scripts, and mask layout definitions for the JANUS Mini 16-Tile Monolithic Planar MVP.

## Layout Artifacts
- **`janus_mini16_layout.gds`**: Primary GDS II stream file containing the full physical mask stack:
  - **Layer 1/0**: Silicon Waveguide Core (450 nm x 220 nm strip waveguides)
  - **Layer 2/0**: SiO2 Cladding / BOX isolation
  - **Layer 3/0**: Thin-Film LiTaO3 Electro-Optic Pockels Modulator slabs
  - **Layer 4/0 & 4/1**: Sb2S3 Phase-Change Material Directional Coupler Switch Patches
  - **Layer 5/0**: Si3N4 Subwavelength Grating Coupler Teeth
  - **Layer 10/0**: Metal 1 Copper RF Traveling-Wave Electrodes & Interconnects
  - **Layer 20/0**: SAC2M Ge/Si Avalanche Photodiode (APD) Mesas
  - **Layer 30/0**: Through-Dielectric Vias (TDV) & CMOS Hybrid Micro-Bump Array
  - **Layer 99/0**: Chip Guard Ring & Tile Boundaries

- **`generate_mini16_gds.py`**: Automated physical layout synthesis script built on `gdsfactory` and `klayout`. Generates the full 4x4 array of 16 Fermat Arithmetic Tiles, optical fiber I/O couplers, and micro-bump grids.

## Layout Verification & Dimensions
- **Total Die Footprint**: 3.22 mm x 3.20 mm (10.3 mm² monolithic active die)
- **Tile Architecture**: 16 Fermat residue tiles with 4-stage binary switch trees (240 Sb2S3 switches/multiplier)
- **Optical I/O**: Dual 17-channel standard Fiber V-Groove Array (127 µm pitch)
- **CMOS Hybrid Integration**: 576+ Through-Dielectric Via micro-bumps per tile for 22nm CMOS stratum bonding

## Relative Path in Registry
Referenced from `janus_mini16_sim/configs/mini_16t_constants.py` via:
`../layout/janus_mini16_layout.gds`
