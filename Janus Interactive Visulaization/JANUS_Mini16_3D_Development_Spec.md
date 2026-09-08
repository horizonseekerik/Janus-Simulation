# JANUS Mini 16-Tile (Model 1A) 3D Architectural Visualization
## Master Engineering Specification & Step-by-Step Layer-by-Layer Development Guide

---

### Executive Summary & System Identity
* **Target Hardware:** JANUS Mini 16-Tile Monolithic Planar Prototype (Model 1A)
* **Architecture Type:** Constraint-Bounded 3D Monolithic Heterogeneous Optoelectronic Processor
* **Core Technology:** One-Hot Optical Residue Number System (RNS) Spatial Permutation + 65nm LP/GP CMOS Exact Digital Reconstruction
* **Die Dimensions:** $10.0\text{ mm} \times 10.0\text{ mm}$ ($100.00\text{ mm}^2$ footprint)
* **Active Stack Thickness:** $330\ \mu\text{m}$ (SiPh $30\ \mu\text{m}$ + $\text{SiO}_2$ $250\ \mu\text{m}$ + CMOS $50\ \mu\text{m}$)
* **Total Packaged Height:** $580\ \mu\text{m}$ ($0.58\text{ mm}$) including dual-stage convective heat spreaders
* **Total Full-System Power:** $6.17\text{ W}$ continuous load envelope (zero static routing hold power)
* **Peak INT4 Throughput:** $1,392.6\text{ TMAC/s}$ ($1.39\text{ PMAC/s}$) @ $225.7\text{ TMAC/s/W}$
* **Peak INT64 Exact Throughput:** $87.0\text{ TMAC/s}$ @ $14.1\text{ TMAC/s/W}$ (Deterministic exact, zero overflow)

---

## 1. Verified Hardware Component & Specification Audit

All figures below are extracted directly from the signed-off design reports and physical co-simulations:

| Subsystem / Metric | Exact Design Value | Architectural Function / Physical Implementation |
| :--- | :--- | :--- |
| **Die Dimensions** | $10.0\text{ mm} \times 10.0\text{ mm}$ | Monolithic planar die ($100.00\text{ mm}^2$ area) |
| **Tile Floorplan** | $4 \times 4$ Grid ($16$ Tiles) | Each tile $= 2.5\text{ mm} \times 2.5\text{ mm} = 6.25\text{ mm}^2$ |
| **Intra-Tile Multipliers** | $32 \times 32$ Mesh ($1,024$ / Tile) | Modular residue multiplication nodes |
| **Total Multipliers** | **$16,384$ Multipliers** | Fully parallel optical 1×1 modular multipliers |
| **Waveguides per Multiplier** | $256$ Spatial Waveguides | One-Hot spatial basis (exactly 1 channel active, $\alpha = 1/256$) |
| **Total Waveguides on SiPh** | **$4,194,304$ Waveguides** ($4.19 \times 10^6$) | Single-mode $\text{Si}_3\text{N}_4/\text{Si}$ cores ($450\text{ nm}$ width) |
| **Total $\text{Sb}_2\text{S}_3$ Switches** | **$31,457,280$ Switches** ($31.46 \times 10^6$) | 15-stage dilated Beneš permutation fabric per multiplier ($1,920$ cells/mult) |
| **Total $\text{Ge/Si}\ \text{SAC}^2\text{M}$ APDs** | **$4,194,304$ Detectors** ($4.19 \times 10^6$) | Monolithically integrated on the SiPh layer ($1$ APD per waveguide terminus) |
| **Active APDs per Cycle** | $16,384$ Active Channels | Strict One-Hot invariant ($1$ per multiplier per $10\text{ ps}$ cycle) |
| **Master Laser Launch** | $2.21\text{ W}$ CW ($+33.44\text{ dBm}$) | $1064\text{ nm}$ Yb-doped continuous-wave fiber laser ($75\%$ WPE, $2.95\text{ W}$ elec.) |
| **Net Optical Link Margin** | **$+3.02\text{ dB}$** | Link closure: Delivered $P_{rx} = -18.59\text{ dBm}$ vs Sensitivity $P_{sens} = -21.62\text{ dBm}$ |
| **Raw Optoelectronic BER** | $2.35 \times 10^{-37}$ ($Q = 12.72$) | 100 GHz eye opening $94.2\%$, jitter $50\text{ fs rms}$ via microcomb ILO |
| **CMOS Base Die Node** | **$65\text{nm}$ LP/GP Planar CMOS** | $100.00\text{ mm}^2$ area, $50\ \mu\text{m}$ thickness, operating at $3.125\text{ GHz}$ |
| **Deserialization Ratio** | $1:32$ Polyphase Time-Interleaved | 5-bit master binary pointer converts $100\text{ GHz}$ optical stream to $3.125\text{ GHz}$ |
| **Through-Dielectric Vias (TDVs)** | $10,000\text{ mm}^{-2}$ Cu density | Traverse $250\ \mu\text{m}\ \text{SiO}_2$ buffer to connect SiPh APDs to CMOS StrongARM latches |
| **Thermal Equilibrium (JIR)** | $28.4^\circ\text{C}$ Clamped Peak Temp | 18.5 kHz dynamic modulus swapping ($+41.6^\circ\text{C}$ below $70^\circ\text{C}$ crystallization) |

---

## 2. Micro-to-Macro Z-Axis Physical Strata Architecture

```
═════════════════════════════════════════════════════════════════════════════════════
 Z-AXIS EXPLODED STRATIGRAPHY (JANUS MINI 16-TILE MODEL 1A)
═════════════════════════════════════════════════════════════════════════════════════

▲ +Z (Upward Directional Heat Removal, Rth,up = 0.227 K/W)
│
├── [MACRO PACKAGE LID] Heat Spreader 2 (HS2)
│   • Thickness: 250 µm | Material: Convective microchannel copper lid
│   • Purpose: Direct upward liquid microchannel heat extraction (clamps die to 28.4°C)
│
├── [SPREADER GAP & PILLAR ARRAY]
│   • Thickness: 50 µm | Density: 950,000 mm⁻² Cu-Cu micro-pillars + structural vacuum
│
├── [HEAT SPREADER 1 (HS1)]
│   • Thickness: 30 µm | Density: 900,000 mm⁻² dense copper-pillar micro-matrix
│
├── [STRATUM 1: SILICON PHOTONICS (SiPh) LAYER] ────────────────────────── (30 µm)
│   • Area: 10.0 mm × 10.0 mm (100.00 mm²) | Thickness: 30 µm
│   • 4×4 Optical Tile Grid (16 Tiles, 2.5 mm × 2.5 mm each)
│   • Integrated Components (Monolithic on SiPh):
│     1. 1:16 Global MMI Optical Tree + 1:1024 Intra-Tile Splitters (1064 nm CW)
│     2. 16,384 LiTaO3 Pockels Electro-Optic Ring Routers (1×256 input one-hot injection)
│     3. 4,194,304 Single-Mode Waveguides (450 nm Si3N4/Si cores, 256 per multiplier)
│     4. 31,457,280 Sb2S3 Non-Volatile PCM Switches (15-stage dilated Beneš fabrics)
│     5. Parabolic MMI Low-Loss Waveguide Crossings (1.6 µm waist, Ltaper = 6.4 µm)
│     6. 4,194,304 Ge/Si SAC²M Avalanche Photodetectors (APDs at waveguide termini)
│
├── [STRATUM 2: MONOLITHIC SiO₂ THERMAL BUFFER] ───────────────────────── (250 µm)
│   • Area: 10.0 mm × 10.0 mm | Thickness: 250 µm
│   • Properties: Fused silica insulation (Rth,down = 0.488 K/W, τdiff = 69.06 ms)
│   • Interconnects:
│     - Vertical Through-Dielectric Vias (Cu TDVs): 10,000 mm⁻² density (Lwire ≈ 200–250 µm)
│     - Function: Directly routes avalanche charge from SiPh APDs down to StrongARM latches
│   • Perimeter Border: Solid copper thermal shunt & 100 GHz EMI Faraday shield ring
│
└── [STRATUM 3: CMOS 65nm DIGITAL BASE DIE] ───────────────────────────── (50 µm)
    • Area: 10.0 mm × 10.0 mm (100.00 mm²) | Thickness: 50 µm | Process: 65nm LP/GP
    • Clock: 3.125 GHz (320.0 ps cycle) | Power: 2.55 W digital (6.17 W full system)
    • Floorplan Allocation:
      1. StrongARM Dynamic Latches & 1:32 Deserializers: 3.00 mm² (3.0%)
      2. 32-Lane SIMD Calculation Array: 4.50 mm² (4.5%)
         (Wallace Tree 8:2 CSA + 64-bit Kogge-Stone Adder + Montgomery Reducer)
      3. 1.5 MB Localized SRAM (32 Slices × 48 KB): 6.20 mm² (6.2%)
         (Dual-LUT Cross-Term Engine for 64-bit PRNS)
      4. 1.5 MB Central Non-Volatile ROM Macro: 1.80 mm² (1.8%)
         (Master CRT constants Mi, Ni and permanent LUT tables at 0 V)
      5. JIR Master Control Unit & Sequencer: 0.50 mm² (0.5%)
         (18.5 kHz dynamic modulus rotation & closed-loop thermal FSM)
      6. 160-bit Binary Carry-Save Accumulator (CSA): Inside SIMD datapath
      7. Wide Power Mesh, Decoupling Capacitors & Routing: 84.00 mm² (84.0%)
▼ -Z (Substrate Ground Plane)
```

---

## 3. Four-Level Micro-to-Macro Visual Hierarchy (Blender Collections)

To ensure that **every component from sub-micron physics to the macro package** is accurately represented without choking viewport performance, the 3D model is organized into four hierarchical levels of detail (LOD):

### Level 4: Macro Package & 100 mm² Full Die
* **Dimensions:** $10.0\text{ mm} \times 10.0\text{ mm} \times 0.58\text{ mm}$
* **Components:**
  * External convective microchannel heat sink lid (HS2) with fluid ports.
  * Intermediate Cu-pillar micro-matrix gap (HS1).
  * Peripheral Solid Copper Thermal Shunt & 100 GHz EMI Faraday ring running around all 4 edges of the chip.
  * $4 \times 4$ array of 16 optical tiles with laser launch fiber coupling interface on the chip facet ($1064\text{ nm}$ single-mode input).
  * Bottom ball grid array (BGA) / wire bond pad ring for 65nm CMOS power rails and PCIe/Host digital I/O.

### Level 3: Meso Tile Architecture (Single Tile = 6.25 mm²)
* **Dimensions:** $2.5\text{ mm} \times 2.5\text{ mm} \times 330\ \mu\text{m}$ (representing Tile `[i, j]`)
* **Components:**
  * Optical power input from the 1:16 global distribution tree.
  * $1:1024$ binary MMI tree branching power across the tile's $32 \times 32$ multiplier matrix.
  * $32 \times 32$ multiplier array layout ($1,024$ multiplier engines).
  * Vertical Cu TDV array ($10,000\text{ mm}^{-2}$) descending through the $250\ \mu\text{m}\ \text{SiO}_2$ buffer.
  * Corresponding $6.25\text{ mm}^2$ CMOS 65nm tile sector below (local SRAM slice, StrongARM bank, and SIMD lane).

### Level 2: Micro Multiplier Engine (Single Multiplier Node)
* **Components:**
  * **$1 \times 256$ Active $\text{LiTaO}_3$ Pockels Input Router:** Ring resonator modulator bank injecting the optical pulse into exactly 1 of 256 waveguides.
  * **256 Waveguide Routing Bus:** Single-mode channels spaced along the multiplier width.
  * **15-Stage Dilated Beneš Permutation Fabric:** $15$ columns of $128$ switching cells ($1,920$ cells total), arranged with dilated non-blocking topology.
  * **Parabolic MMI Waveguide Crossing Grid:** Low-loss crossings ($0.018\text{ dB}$, $-42.1\text{ dB}$ crosstalk) where waveguide paths intersect.
  * **256 $\text{Ge/Si}\ \text{SAC}^2\text{M}$ APD Array:** Positioned on the SiPh layer directly at the terminus of each output waveguide.
  * **256 Vertical Cu TDV Stems:** Dropping vertically from each APD into the CMOS substrate.

### Level 1: Sub-Micron Device Physics Models
* **Components:**
  * **Sb₂S₃ 2×2 Switch Cell ($60\ \mu\text{m} \times 1.2\ \mu\text{m}$):**
    * Dual-core directional coupler with an active $\text{Sb}_2\text{S}_3$ patch ($L = 60.0\ \mu\text{m}$, modal overlap $\Gamma = 2.56\%$).
    * Monolayer Graphene electro-thermal micro-heater ($1.0\text{ nm}$) directly atop the $\text{Sb}_2\text{S}_3$ patch with gold contact vias.
    * Visual state representation: Amorphous cross-state (deep amber, $n_a = 2.70$) vs. Crystalline bar-state (metallic silvery-blue, $n_c = 3.30$).
  * **Parabolic MMI Crossing ($1.6\ \mu\text{m} \times 6.4\ \mu\text{m}$):**
    * Adiabatic parabolic expansion from $450\text{ nm}$ single-mode core to $1.6\ \mu\text{m}$ Gaussian waist.
  * **$\text{Ge/Si}\ \text{SAC}^2\text{M}$ APD Mesa ($1.5\ \mu\text{m}^2$):**
    * Pure Germanium absorption layer ($R = 1.2\text{ A/W}$) atop a thin pure Silicon multiplication cliff ($M = 7$, $k_{eff} \approx 0.05$).
  * **CMOS StrongARM Dynamic Comparator:**
    * Clocked differential regenerative latch circuit schematic layout on 65nm base.

---

## 4. Layer-by-Layer Procedural 3D Development Plan

The implementation in Blender 5.2 LTS is divided into 8 distinct sequential steps:

### Phase 1: Environment, Scale Mapping & Base Strata Geometry
* **Step 1.1: World & Units Calibration**
  * Set Blender scene unit system to Metric, scale factor $1.0\times 10^{-4}$ (or $1\text{ Blender Unit} = 100\ \mu\text{m}$) so that a $10.0\text{ mm}$ die is $100\text{ BU}$ across, avoiding floating-point precision clipping while preserving micrometer details.
* **Step 1.2: Layered Substrate Blocks**
  * Generate the 3 monolithic slabs with exact thickness ratios:
    * CMOS Base Die: $10.0\text{ mm} \times 10.0\text{ mm} \times 50\ \mu\text{m}$.
    * $\text{SiO}_2$ Thermal Buffer: $10.0\text{ mm} \times 10.0\text{ mm} \times 250\ \mu\text{m}$.
    * SiPh Photonic Stratum: $10.0\text{ mm} \times 10.0\text{ mm} \times 30\ \mu\text{m}$.
  * Generate the Perimeter Copper Thermal Shunt: Solid rectangular border ($250\ \mu\text{m}$ wide) framing the active die.

### Phase 2: CMOS 65nm Base Die Floorplan & Internal Topology
* **Step 2.1: Procedural Floorplan Mapping**
  * Model the physical floorplan partitions directly on the CMOS surface according to Table 1:
    * Central ROM ($1.80\text{ mm}^2$): Gold/silicon embossed pattern.
    * 32 Localized SRAM Slices ($6.20\text{ mm}^2$ total, $48\text{ KB}$ per slice): Memory bitcell tile arrays.
    * 32-Lane SIMD Calculation Array ($4.50\text{ mm}^2$): Arithmetic datapath layout.
    * JIR Controller & Sequencer ($0.50\text{ mm}^2$): FSM logic block with thermal sensor routing.
    * StrongARM Sensing & Deserializer Front-End ($3.00\text{ mm}^2$).
    * Power Mesh & Decoupling Capacitor Grid ($84.00\text{ mm}^2$): Cross-hatched high-density Cu power distribution grid.

### Phase 3: $\text{SiO}_2$ Thermal Buffer & Vertical Cu TDVs
* **Step 3.1: Through-Dielectric Via Array**
  * Create procedural instances of vertical Cu TDVs spanning the full $250\ \mu\text{m}$ Z-gap.
  * Connect each terminal SiPh APD pad down to its corresponding CMOS StrongARM input pad.
* **Step 3.2: Thermal Moat Material Definition**
  * Develop the translucent Fused Silica glass material with realistic subsurface scattering (IOR 1.45, slight cyan-blue tint) showing the internal copper via forest suspended within.

### Phase 4: SiPh 16-Tile Stratum & Optical Distribution Network
* **Step 4.1: $4 \times 4$ Optical Tile Layout**
  * Subdivide the $100\text{ mm}^2$ SiPh plane into 16 distinct $2.5\text{ mm} \times 2.5\text{ mm}$ tiles separated by optical isolation streets.
* **Step 4.2: Global Laser Distribution Tree**
  * Model the single-mode $1064\text{ nm}$ fiber input coupler at the die facet.
  * Model the 1:16 global MMI distribution tree splitting the $2.21\text{ W}$ CW laser equally into the 16 tile ports.
* **Step 4.3: Intra-Tile $1:1024$ Multiplier Splitter**
  * Within each tile, model the 10-stage cascaded MMI tree feeding the $1,024$ multiplier rows.

### Phase 5: Multiplier Engine & 15-Stage Dilated Beneš Permutation Fabric
* **Step 5.1: $1 \times 256$ $\text{LiTaO}_3$ Electro-Optic Pockels Router**
  * Model the active micro-ring resonator bank at the multiplier input where optical pulses are injected into the active One-Hot waveguide.
* **Step 5.2: 15-Stage Dilated Beneš Network**
  * Procedurally generate the 15 switching columns with 128 $2 \times 2$ cells per column ($1,920$ cells total).
  * Interconnect the stages using the standard dilated butterfly shuffle permutation topology.
* **Step 5.3: Parabolic MMI Waveguide Crossings**
  * Model the diamond/parabolic widened crossings at all waveguide intersections.
* **Step 5.4: Terminal $\text{SAC}^2\text{M}$ APD Array (On SiPh)**
  * Place the 256 Ge/Si APD photodetector blocks directly at the output of the 256 waveguides on the SiPh surface.

### Phase 6: Sub-Micron Physics Deep-Dive Models (Focus Cutouts)
* **Step 6.1: High-Detail $\text{Sb}_2\text{S}_3$ Directional Coupler Cell**
  * Construct an isolated, high-detail macro model of the $60\ \mu\text{m}$ switch cell:
    * Silicon strip waveguides ($450\text{ nm} \times 220\text{ nm}$).
    * $\text{Sb}_2\text{S}_3$ phase-change patch overlay.
    * Monolayer graphene heater strip with gold electrode contact pads.
* **Step 6.2: Single $\text{SAC}^2\text{M}$ Ge/Si APD Diode Cross-Section**
  * High-detail cutaway showing the pure Germanium absorption layer on top of the pure Silicon avalanche multiplication mesa with top and bottom cathode/anode contacts.

### Phase 7: Photorealistic PBR Materials & Shaders
* **Silicon Base:** Brushed dark metallic gray with micro-roughness and thin-film iridescence.
* **Copper / Gold Interconnects:** High metallic reflectance ($0.95$), slight warm hue.
* **$1064\text{ nm}$ Optical Guided Wave:** Volumetric / emission shader with bright neon-cyan/amber core representing in-flight optical pulses.
* **Amorphous $\text{Sb}_2\text{S}_3$:** Translucent amber-brown ($n = 2.70$, low loss).
* **Crystalline $\text{Sb}_2\text{S}_3$:** Silvery reflective metallic-blue ($n = 3.30$).
* **Germanium APD Mesa:** Dark glossy purple-black semiconductor finish.

### Phase 8: Exploded Z-Axis Animation Rig & Cinematic Lighting
* **Step 8.1: Procedural Exploded-View Rig**
  * Add a single master driver property (`Explode_Progress: 0.0 -> 1.0`):
    * `0.0`: Fully assembled monolithic die ($330\ \mu\text{m}$ active / $580\ \mu\text{m}$ packaged).
    * `1.0`: Layers smoothly lift apart vertically along the Z-axis (HS2 moves up $15\text{ mm}$, SiPh moves up $8\text{ mm}$, $\text{SiO}_2$ stays at $+4\text{ mm}$ with extended TDVs, CMOS stays at base $0\text{ mm}$).
* **Step 8.2: Signal Pulse Flow Animation**
  * Animate the passage of a light pulse:
    1. Laser pulse enters die via optical bus.
    2. Modulator injects pulse into 1 active waveguide (One-Hot).
    3. Traverses the 15-stage Beneš switch network.
    4. Absorbed at the $\text{SAC}^2\text{M}$ APD on SiPh.
    5. Avalanche electrical charge shoots down the Cu TDV.
    6. Triggers the StrongARM latch on the 65nm CMOS base.
* **Step 8.3: Thermal Comparison Visualization**
  * Surface heatmap overlay toggle comparing Static Hotspot ($58.4^\circ\text{C}$) vs. Dynamic 18.5 kHz JIR Swapping ($28.4^\circ\text{C}$).

---

## 5. Output Verification & Automation Pipeline

1. **Procedural Blender Python Generator:** Scripted entirely in Python using the `bpy` API, fully compatible with headless execution via `blender_runner.py` or interactive exploration in Blender GUI.
2. **Deterministic Geometry Checks:** Automated assertions verifying:
   - Exactly 16 tiles in a $4 \times 4$ array.
   - Exact $10.0\text{ mm} \times 10.0\text{ mm}$ die dimensions.
   - Correct vertical layer thickness ($30\ \mu\text{m}$ SiPh, $250\ \mu\text{m}\ \text{SiO}_2$, $50\ \mu\text{m}$ CMOS).
   - Monolithic APDs placed on SiPh, and TDVs bridging SiPh to CMOS.
3. **Artifacts & Renders:** High-resolution multi-angle beauty renders, exploded technical schematics, and animated camera flythroughs compiled via FFmpeg.
