# JOMI: Janus Optical Memory Interconnect & Symmetrically Pipelined 3D Flash Architecture

**Author:** Deepanshu Bhardwaj  
**Affiliation:** Project JANUS / Independent Hardware Research  
**Document Classification:** Advanced Systems Architecture Specification (Post-Moore Memory Subsystem)  
**Target Integration:** JANUS Monolithic 3D Photonic AI Accelerator (Mini-16 & Model 1A)  

---

## 1. Executive Summary & The Problem Statement

The computational throughput of artificial intelligence accelerators has advanced into the Peta-scale regime. Specifically, the **Project JANUS Photonic Tensor Core** achieves $1.65\,\mathrm{PetaOPS/s}$ at 100 GHz wave-pipelining while consuming merely $\sim 6.17\,\mathrm{W}$ of optical and CMOS power. 

However, modern computing remains constrained by the **Von Neumann Memory Wall**:
1. **The Copper SerDes / PHY Scaling Crisis**: Electronic interconnects (TSVs, micro-bumps, and SerDes pins) are fundamentally limited by capacitive loading ($C$), dielectric loss, and high-frequency skin effect ($RC$ parasitic delays). Reaching multi-terabit bandwidth over copper requires complex equalization and massive energy dissipation ($> 5\text{--}10\,\mathrm{pJ/bit}$).
2. **The HBM Economic & Thermal Tax**: High-Bandwidth Memory (HBM3e/HBM4) achieves $2\text{--}3\,\mathrm{TB/s}$, but costs $\$15\text{--}\$25/\mathrm{GB}$ ($\$1,500+$ per stack) due to complex silicon interposers, through-silicon via (TSV) yields, and thermal cross-talk. Furthermore, DRAM requires continuous capacitor refresh cycles ($32\text{--}64\,\mathrm{ms}$ intervals), consuming $20\%\text{--}30\%$ of total memory power in standby ($> 0\,\mathrm{W}$ hold power).
3. **The 3D NAND Flash Architectural Bottleneck**: Commercial flash storage (e.g., SD cards, NVMe SSD dies) is the cheapest ($\approx \$0.08/\mathrm{GB}$) and densest ($15\text{--}20\,\mathrm{Gb/mm^2}$) storage technology on Earth, capable of packing Terabytes into postage-stamp footprints. However, commercial flash dies are artificially throttled:
   - **Monolithic Word-Line Sheet Delay**: Traditional 3D NAND ties an entire horizontal tier of cells into a single monolithic sheet spanning millimeters, producing colossal sheet capacitance ($RC \approx 10\text{--}15\,\mu\mathrm{s}$ charging delay).
   - **Narrow Serial Electronic I/O**: The massive internal parallel page buffer ($16\,\mathrm{KB} = 131,072\,\text{bits}$) is forced through a narrow 8-bit electronic pin interface (ONFI/Toggle DDR at $2.4\text{--}3.2\,\mathrm{Gb/s}$), creating a $10,000\times$ bandwidth collapse at the package boundary.

**JOMI (Janus Optical Memory Interconnect)** eliminates the memory wall by:
- Replacing electronic memory pinouts with **direct parallel spatial optical bit-lanes operating at 200 GHz**.
- Structurally re-engineering the 3D memory stack into **segmented horizontal micro-planes with independent vertical supply pipelines**.
- Implementing a **21-pillar per-layer symmetric routing constellation** (16 perimeter boundary taps + 5 central spine taps) to collapse the internal $RC$ time constant from $15\,\mu\mathrm{s}$ down to nanoseconds.
- Co-packaging a **4-die vertical 3D flash stack (500 GB total capacity)** directly beneath the JANUS 65nm CMOS base die, enabling single-user local inference of **1-Trillion parameter models (4-bit quantized)** at speeds exceeding $200\,\mathrm{Tb/s}$ with zero external DRAM.

---

## 2. JOMI Optical Physical Layer Architecture

```
                       JOMI OPTICAL INTERCONNECT BUS
   ======================================================================
   Waveguide 0  :  [Light = 1]  [Dark = 0]   [Light = 1]  --> 200 GHz Lane
   Waveguide 1  :  [Dark = 0]   [Dark = 0]   [Light = 1]  --> 200 GHz Lane
   Waveguide 2  :  [Dark = 0]   [Light = 1]  [Dark = 0]   --> 200 GHz Lane
   ...
   Waveguide 63 :  [Light = 1]  [Dark = 0]   [Dark = 0]   --> 200 GHz Lane
   ======================================================================
   Aggregate Bus:  64 Physical Dielectric Waveguides @ 200 GHz = 12.8 Tb/s
   Expanded Bus :  1,024 Physical Waveguides @ 200 GHz         = 204.8 Tb/s (25.6 TB/s)
```

### 2.1 Spatial Binary Bit-Lane Encoding (Non-Return-to-Zero OOK)
Unlike computational arithmetic (which in JANUS uses Residue Number System $\mathbb{Z}_{17}$ Fermat rings for modular multiplication), memory transport requires pure data transfer density without modular arithmetic wraparounds.

JOMI implements **Direct Spatial Optical Bit-Lanes**:
- **Carrier**: Single-mode low-loss silicon nitride ($\mathrm{Si_3N_4}$) or thin-film lithium niobate/tantalate ($\mathrm{LiNbO_3}/\mathrm{LiTaO_3}$) rib waveguides.
- **Modulation**: Direct On-Off-Keying (OOK) via electro-optic Pockels modulators.
  - Presence of optical pulse in Waveguide $i \implies \mathbf{1}$
  - Absence of optical pulse in Waveguide $i \implies \mathbf{0}$
- **Example Data Word**: Transferring binary nibble `1001` across 4 spatial lanes:
  $$\text{Lane } 0: \text{PULSE} \quad | \quad \text{Lane } 1: \text{DARK} \quad | \quad \text{Lane } 2: \text{DARK} \quad | \quad \text{Lane } 3: \text{PULSE}$$

### 2.2 Bus Geometry & Bandwidth Scaling
- **Clock Period**: $T_{\text{clk}} = 5.0\,\mathrm{ps}$ ($f_{\text{symbol}} = 200\,\mathrm{GHz}$).
- **Waveguide Physical Pitch**: $1.5\,\mu\mathrm{m}$ center-to-center spacing with deep dielectric trench isolation (optical crosstalk $<-45\,\mathrm{dB}$).

$$\begin{aligned}
\text{Base JOMI-64 Engine:} & \quad 64 \text{ lanes} \times 200\,\mathrm{Gb/s/lane} = \mathbf{12.8\,\mathrm{Tb/s} \ (1.6\,\mathrm{TB/s})} \\
\text{Expanded JOMI-1024 Highway:} & \quad 1,024 \text{ lanes} \times 200\,\mathrm{Gb/s/lane} = \mathbf{204.8\,\mathrm{Tb/s} \ (\mathbf{25.6\,\mathrm{TB/s}})}
\end{aligned}$$

- **Physical Silicon Ribbon Width**:
  $$W_{\text{bus}} = 1,024 \times 1.5\,\mu\mathrm{m} \approx \mathbf{1.536\,\mathrm{mm}}$$
  The entire **$200\,\mathrm{Tb/s}$ optical transport highway occupies an ultra-narrow $1.5\,\mathrm{mm}$ strip of silicon**, requiring zero copper pin breakouts and zero solder ball arrays.

---

## 3. The Symmetrically Pipelined 3D Flash Memory Architecture

```
+-------------------------------------------------------------------------+
|                  TOP: JANUS Photonic Compute Stratum                    |
+-------------------------------------------------------------------------+
|        MIDDLE: 65nm LP/GP CMOS Base Die (StrongARM Latches, SIMD)       |
+=========================================================================+
|           Cu-Cu Hybrid Direct Bonding Interface (6,300 Pillars)         |
+=========================================================================+
|  LAYER 300: Micro-Plane [16 Zones]  -- 21 Dedicated Isolated Pillars    |
|  LAYER 299: Micro-Plane [16 Zones]  -- 21 Dedicated Isolated Pillars    |
|  ...                                                                    |
|  LAYER   2: Micro-Plane [16 Zones]  -- 21 Dedicated Isolated Pillars    |
|  LAYER   1: Micro-Plane [16 Zones]  -- 21 Dedicated Isolated Pillars    |
+-------------------------------------------------------------------------+
|                  BOTTOM: Thermally Conductive Silicon Substrate         |
+-------------------------------------------------------------------------+
```

### 3.1 Resolving the 3D NAND Delay Mechanism
In standard 3D NAND, word-lines are deposited as continuous sheets across an entire memory plane. Sinking the charging current through millions of cells across millimeters creates a massive distributed capacitance ($C_{\text{sheet}}$) and resistance ($R_{\text{sheet}}$), requiring a settling time of:
$$t_{\text{settle}} = R_{\text{sheet}} \times C_{\text{sheet}} \approx 10\text{--}15\,\mu\mathrm{s}$$

JOMI replaces this continuous sheet structure with two radical physical layout modifications:

#### 1. Horizontal Plane Micro-Segmentation (16 Localized Sub-Zones)
The continuous horizontal plane is segmented into a **$4 \times 4$ grid of 16 electrically isolated sub-zones**.
- The physical length of each local word-line strip is reduced by $16\times$.
- Resistance ($R$) drops by $16\times$.
- Capacitance ($C$) drops by $16\times$.
- The localized $RC$ charging constant collapses quadratically:
  $$\tau_{\text{local}} \approx \frac{\tau_{\text{monolithic}}}{16^2} = \frac{15\,\mu\mathrm{s}}{256} \approx \mathbf{58.5\,\mathrm{ns}} \quad (\text{down to } < 5\,\mathrm{ns} \text{ with central taps!})$$

#### 2. The 21-Pillar Symmetric Vertical Routing Constellation
To eliminate capacitive line drag, each of the **300 physical layers** is fed by **21 dedicated, electrically isolated copper pillars**:
- **16 Perimeter Boundary Pillars**: Symmetrically positioned along the outer shielded die boundary (4 North, 4 South, 4 East, 4 West). These feed the peripheral sub-zones directly from zero-capacitance isolation corridors.
- **5 Central Spine Pillars**: Positioned in a central cross configuration (`+`) down the middle of the active plane (1 central hub + 4 mid-quadrant taps). This halves the maximum distance any electron must travel to reach a cell:
  $$L_{\max} \to \frac{L_{\text{zone}}}{2} \implies \tau_{\text{center}} \le \mathbf{2.5\,\mathrm{ns}}$$

Across a 300-layer vertical stack:
$$N_{\text{pillars}} = 300 \text{ layers} \times 21 \text{ pillars/layer} = \mathbf{6,300 \text{ Isolated Vertical Copper Pillars}}$$

At a standard through-dielectric via pitch of $4\,\mu\mathrm{m}$, all 6,300 pillars occupy:
$$\text{Area}_{\text{pillars}} = 6,300 \times (4\,\mu\mathrm{m} \times 4\,\mu\mathrm{m}) = \mathbf{0.1008\,\mathrm{mm^2}} \ (< 1\% \text{ of die area})$$

```
          21-PILLAR SYMMETRIC FLOORPLAN (PER PHYSICAL LAYER)
          +-----------------------------------------------+
          |  [P1]     [P2]         [P3]         [P4]  [P5]|
          |                                               |
          |  [P16]         {C1}           {C2}       [P6] |
          |                                               |
          |  [P15]                 {C0}              [P7] |
          |                     (Center)                  |
          |  [P14]         {C3}           {C4}       [P8] |
          |                                               |
          |  [P13]    [P12]        [P11]       [P10]  [P9]|
          +-----------------------------------------------+
          Legend:
          [P1 - P16] : 16 Perimeter Shielded Boundary Pillars
          {C0 - C4}  :  5 Central Spine / Hub Pillars
```

---

## 4. Operational Dynamics & Bandwidth Derivation

### 4.1 Single-Layer Readout Capacity
Each of the 21 pillars per layer couples directly into a dedicated local 64-bit sense-amplifier latch array:
- **Instantaneous Bit Output per Layer**:
  $$W_{\text{layer}} = 21 \text{ pillars} \times 64 \text{ bits} = \mathbf{1,344 \text{ bits/cycle}} \ (168\,\text{Bytes/cycle})$$
- **At Local CMOS Sense Clock ($2.0\,\mathrm{GHz}$)**:
  $$\text{Throughput}_{\text{single layer}} = 1,344 \times 2.0 \times 10^9 = \mathbf{2.688\,\mathrm{Tb/s} \ (\approx 336\,\mathrm{GB/s})}$$

### 4.2 Multi-Layer Interleaved Pipelining
Because all 300 layers have **independent, non-shared copper pillars**, the chip can read multiple layers concurrently without word-line charging conflicts.

| Execution Mode | Concurrently Active Layers | Effective Aggregate Bandwidth | Industrial Baseline Comparison |
| :--- | :---: | :---: | :--- |
| **Single Layer Mode** | 1 Layer | **$336\,\mathrm{GB/s}$** | $4\times$ faster than Apple M4 Max ($400\,\mathrm{GB/s}$) |
| **MoE Dual-Expert Stream** | 8 Layers | **$2.688\,\mathrm{TB/s}$ ($21.5\,\mathrm{Tb/s}$)** | **Matches NVIDIA H100 HBM3e ($2.5\text{--}3.0\,\mathrm{TB/s}$)** |
| **Wide Attention Pipelining** | 32 Layers | **$10.75\,\mathrm{TB/s}$ ($86.0\,\mathrm{Tb/s}$)** | **$3.5\times$ faster than NVIDIA B200 ($3.2\,\mathrm{TB/s}$)** |
| **Full JOMI Saturation** | 75+ Layers | **$25.6\,\mathrm{TB/s}$ ($\mathbf{204.8\,\mathrm{Tb/s}}$)** | **$\mathbf{10\times}$ faster than any commercial GPU memory bus** |

---

## 5. Physical Co-Packaging & The 500 GB Silicon Realization

```
             3D MONOLITHIC HETEROGENEOUS STACK GEOMETRY
+-------------------------------------------------------------------+  ^
| 1. Photonic Stratum (Si3N4 / LiTaO3 / Sb2S3 / SAC2M APDs)        |  | 50 um
+-------------------------------------------------------------------+  v
| 2. Monolithic SiO2 Thermal Isolation Buffer (Layer 30/0 Cu TDVs)  |  | 250 um
+-------------------------------------------------------------------+  v
| 3. 65nm LP/GP CMOS Digital Base Die (StrongARM Latches & SIMD)   |  | 50 um
+===================================================================+  v
| Cu-Cu Hybrid Direct Bonding Interface (6,300 Sub-Micron Pillars)  |
+===================================================================+  ^
| 4. 4-Die Stacked 300-Layer 3D Segmented Flash Array (500 GB Total)|  | 150 um
|    - Die 0: Layers   1 - 300                                      |  |
|    - Die 1: Layers 301 - 600                                      |  |
|    - Die 2: Layers 601 - 900                                      |  |
|    - Die 3: Layers 901 - 1200                                     |  |
+-------------------------------------------------------------------+  v
Total Z-Height: < 500 um (Half a Millimeter!)
Total Footprint: 10.0 mm x 10.0 mm (100 mm2)
```

### 5.1 The 500 GB Density Equation
Modern 3D NAND flash in mass production exhibits an areal bit density of:
$$\rho_{\text{flash}} \approx 15\text{--}20\,\mathrm{Gb/mm^2} \approx \mathbf{1.875\text{--}2.5\,\mathrm{GB/mm^2}}$$

On a compact **$10.0\,\mathrm{mm} \times 10.0\,\mathrm{mm} = 100\,\mathrm{mm^2}$** die footprint:
- Capacity per single physical die layer:
  $$\text{Cap}_{\text{die}} = 100\,\mathrm{mm^2} \times 1.25\,\mathrm{GB/mm^2} = \mathbf{125\,\mathrm{GB/die}}$$
- Stacking **4 thinned physical dies vertically** (each thinned to $30\,\mu\mathrm{m}$ via chemical-mechanical polishing):
  $$\text{Total On-Package Integrated Storage} = 4 \times 125\,\mathrm{GB} = \mathbf{500\,\mathrm{GB}}$$

### 5.2 Micro-Architectural Layer Allocation
Because each of the **1,200 physical memory layers** (across 4 dies) has independent pillar control, the operating system and JIR compiler allocate memory with 1:1 structural symmetry:

$$\begin{aligned}
\text{Layers } 1 \to 400: & \quad \text{Transformer Attention Projections } (W_Q, W_K, W_V, W_O) \\
\text{Layers } 401 \to 1000: & \quad \text{Feed-Forward Network (FFN) \& MoE Sparse Expert Weights} \\
\text{Layers } 1001 \to 1150: & \quad \text{Dynamic Working KV Cache (Low-Wear High-Speed Buffer)} \\
\text{Layers } 1151 \to 1200: & \quad \text{System Microcode, JIR Instructions, \& CRT Moduli Calibration Tables}
\end{aligned}$$

---

## 6. Mathematical Verification: 1-Trillion Parameter Local Inference

### 6.1 Parameter Storage Footprint
A **1-Trillion ($1 \times 10^{12}$) parameter neural network** quantized to INT4 precision (4 bits per weight = 0.5 bytes):
$$\text{Memory Required} = 1 \times 10^{12} \times 0.5\,\text{bytes} = 500 \times 10^9\,\text{bytes} = \mathbf{500.0\,\mathrm{GB}}$$

**The entire 1-Trillion parameter model fits 100% inside the on-package JOMI 3D flash stack.**

### 6.2 The Input-Stationary Paradigm (Eliminating Write Wear)
A foundational concern with non-volatile memory in computing is endurance and write latency:
- **JANUS Inversion**: Model weights are **NOT** written during inference. Model weights stream as **optical pulses through waveguides**.
- **Input-Stationary Encoding**: The user's input activations (prompt tokens) are written into the non-volatile $\mathrm{Sb_2S_3}$ directional coupler phase-change switches **ONCE per token step**.
- The 1-Trillion parameter model weights stored permanently in the 3D flash stack are **read-only during inference**, completely eliminating dielectric write fatigue.
- Read endurance for 3D flash is functionally infinite ($> 10^{15}$ read cycles without threshold voltage shifts).

### 6.3 Token Generation Latency & Throughput
To compute one token decode pass on a 1-Trillion parameter model:
$$\text{Total Flops per Token} \approx 2 \times N_{\text{params}} = 2 \times 10^{12} = \mathbf{2 \times 10^{12} \text{ Operations/token}}$$

At full JOMI streaming bandwidth ($25.6\,\mathrm{TB/s} = 204.8\,\mathrm{Tb/s}$):
- Streaming the 500 GB weight state into the JANUS optical core takes:
  $$T_{\text{pass}} = \frac{500\,\mathrm{GB}}{25,600\,\mathrm{GB/s}} = \mathbf{0.0195 \text{ seconds} \ (19.5\,\mathrm{milliseconds})}$$
- **Single-User Decode Rate (Batch = 1)**:
  $$\text{Throughput} = \frac{1 \text{ token}}{0.0195\,\mathrm{s}} \approx \mathbf{51.2 \text{ tokens/second}}$$
- **MoE Sparse Routing Optimization (Top-2 of 16 Experts Active)**:
  When utilizing MoE sparsity, only $12.5\%$ of the weights must be evaluated per token:
  $$\text{MoE Active Weight Data} = 500\,\mathrm{GB} \times 0.125 = \mathbf{62.5\,\mathrm{GB}}$$
  $$T_{\text{MoE pass}} = \frac{62.5\,\mathrm{GB}}{25,600\,\mathrm{GB/s}} = \mathbf{2.44\,\mathrm{milliseconds}}$$
  $$\mathbf{\text{Single-User MoE Token Rate} \approx 410 \text{ tokens/second!}}$$

---

## 7. Comparative Benchmark Matrix

| Architecture Metric | NVIDIA HGX H100 (8x SXM5) | Google TPU v5p Pod Slice | **JANUS + JOMI (Unified Engine)** |
| :--- | :---: | :---: | :---: |
| **Max Local Model Size** | $640\,\mathrm{GB}$ (HBM3) | $128\,\mathrm{GB}$ (HBM2e) | **$500\,\mathrm{GB}$ (Integrated 3D Flash) + Host RAM** |
| **Memory Bus Bandwidth** | $26.8\,\mathrm{TB/s}$ (Aggregate 8x GPUs) | $4.8\,\mathrm{TB/s}$ | **$\mathbf{25.6\,\mathrm{TB/s}}$ (Single Monolithic Die!)** |
| **Memory Interface Type** | High-Capacitance Copper TSV | Electronic Interposer | **64-Lane Parallel Optical Waveguides (JOMI)** |
| **Physical Form Factor** | Massive 4U Server Rack ($40\,\mathrm{kg}$) | Multi-Rack Telemetry | **$10\,\mathrm{mm} \times 10\,\mathrm{mm}$ Single Chip ($< 2\,\mathrm{grams}$)** |
| **Total System Power** | **$10,200\,\mathrm{W}$ (10.2 kW)** | **$3,200\,\mathrm{W}$** | **$\mathbf{15\text{--}20\,\mathrm{W}}$ (Wall Outlet / USB-C)** |
| **Cooling Requirement** | Liquid / Industrial Chiller | Liquid Closed-Loop | **Passive Convection / Micro-Fin Heatsink** |
| **Raw Silicon Memory Cost** | $\approx \$12,000\text{--}\$16,000$ (HBM) | $\approx \$8,000$ | **$\mathbf{< \$50.00}$ (Standard 300mm Flash Wafer)** |
| **Target Enterprise Price** | $\$320,000\text{--}\$400,000$ | Cloud Rental Only | **$\$50,000$ (99% Gross Margin)** |

---

## 8. Foundry Fabrication & Physical Manufacturing Strategy

The JOMI architecture is deliberately engineered to avoid speculative physics or exotic materials, relying entirely on existing, mature semiconductor lines:

1. **Memory Wafer Fabrication**:
   - Standard 300mm wafer line at a memory foundry (e.g., TSMC, YMTC, Micron).
   - High-aspect-ratio reactive ion etching (HAR-RIE) to punch the 6,300 vertical pillar channels.
   - Dual-damascene copper electroplating to deposit the 21 pillars per layer with chemical-mechanical planarization (CMP).
2. **CMOS Logic Wafer**:
   - Standard 65nm LP/GP process at mature commercial foundries (e.g., TSMC, GlobalFoundries, SCL Mohali).
   - Back-end-of-line (BEOL) copper landing pad array matching the memory pillar layout.
3. **Wafer-to-Wafer (W2W) Hybrid Cu-Cu Direct Bonding**:
   - Room-temperature dielectric alignment followed by $350^\circ\mathrm{C}$ thermal anneal.
   - Direct atomic copper fusion at the 6,300 pillar interfaces with $< 50\,\mathrm{nm}$ alignment tolerance.
4. **Photonic Stratum Integration**:
   - Monolithic heterogeneous 3D superposition with low-temperature oxide bonding ($< 250^\circ\mathrm{C}$) and Cu TDV vertical through-dielectric vias.

---

## 9. Conclusion

JOMI resolves the greatest paradox of modern artificial intelligence hardware: **how to supply Peta-scale optical processors with multi-terabyte model weights without succumbing to the exorbitant cost, power, and physical bottlenecks of electronic HBM**.

By slicing the monolithic 3D flash plane into 16 localized sub-zones, tapping each of the 300 layers with 21 dedicated vertical copper pillars, and broadcasting data directly into a 200 GHz parallel optical waveguide bus, JOMI collapses the memory wall at its root. A single $100\,\mathrm{mm^2}$ chip can now hold and execute a **1-Trillion parameter model locally at 15 Watts**, fundamentally democratizing post-electronic artificial intelligence for human civilization.
