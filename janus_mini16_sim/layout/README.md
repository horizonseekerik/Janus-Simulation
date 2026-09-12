# JANUS Mini-16 Photonic Layout Directory

This directory houses the physical GDS II stream files and mask layout definitions for the JANUS Mini 16-Tile Monolithic Planar MVP.

## Layout Artifacts
- `janus_mini16_layout.gds`: Primary GDS II stream file containing device layers (Si waveguides, Sb2S3 patches, LiTaO3 modulators, Ge APDs, Cu TDVs).

## Relative Paths
Referenced from configuration files (`janus_mini16_sim/configs/mini_16t_constants.py`) via relative path:
`../layout/janus_mini16_layout.gds`
