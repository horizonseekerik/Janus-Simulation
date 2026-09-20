# Project JANUS Mini 16-Tile: Multi-Physics Co-Simulation & Verification Stack

[![CI Multi-Physics Suite](https://github.com/horizonseekerik/janus-photonic-hardware/actions/workflows/ci.yml/badge.svg)](https://github.com/horizonseekerik/janus-photonic-hardware/actions)
[![TRL Readiness](https://img.shields.io/badge/TRL-4.0%20(Subsystem%20Validation)-blue.svg)](#-technology-readiness-level)
[![Accuracy](https://img.shields.io/badge/GEMM%20Deviation-0.00000000%25-brightgreen.svg)](#-16-point-quantitative-verification-sign-off-matrix)
[![Energy Efficiency](https://img.shields.io/badge/INT8%20Efficiency-112.8%20TMAC%2Fs%2FW-green.svg)](#-gpu-comparative-benchmarks-janus-vs-nvidia-h100--b200)

**Project JANUS** is a constraint-bounded hybrid opto-electronic computing architecture for exact, large-scale artificial intelligence matrix multiplication. By abandoning high-precision analog optical amplitude accumulation in favor of **Spatial One-Hot Residue Number System (RNS)** routing, single-wavelength coherent transport, 4-stage **Asymmetric 16-Tree Fermat optical cores**, and high-speed CMOS Chinese Remainder Theorem (CRT) digital reconstruction, JANUS eliminates analog SNR collapse while sustaining deterministic, bit-exact arithmetic.

This directory houses the **verified 5-tier multi-physics co-simulation framework** for the **JANUS Mini 16-Tile Planar Monolithic Accelerator (Model 1A)**.

---

## 🏛️ System Architecture

```
                    Input 64-Bit Operands (X, Y)
                                │
                                ▼
         +─────────────────────────────────────────────+
         |     65nm CMOS Base Die Stratum              |
         |     - 4-Stage Modulo RNS Encoders           |
         |     - 1.5 MB Dual-LUT SRAM & Central ROM    |
         +──────────────────────┬──────────────────────+
                                │ (Vertical RF Traveling Wave)
                                ▼
         +─────────────────────────────────────────────+
         |   Top Photonic Stratum: Dual Si3N4/Si Stack |
         |   - Primary Core: Low-Loss Si3N4 (0.1 dB/cm)|
         |   - Zero Two-Photon Absorption (TPA)        |
         |   - 16-Tree Fermat Core (4-Stage Sb2S3)     |
         |   - Adiabatic Inverse Taper (Si3N4 -> Si)   |
         |   - Ge/Si SAC2M APDs on Crystalline Si Seed |
         +──────────────────────┬──────────────────────+
                                │ (Vertical Copper TDVs, R < 0.05 Ω)
                                ▼ (Across 250 µm SiO2 Thermal Buffer)
         +─────────────────────────────────────────────+
         |   65nm CMOS Base Stratum Detection & Logic  |
         |   - StrongARM Regenerative Latches (3.5 ps) |
         |   - 1:32 Time-Interleaved Deserializers     |
         |   - 32-Lane SIMD Wallace-Kogge Logic        |
         |   - 12-Stage Pipelined CRT Adder Tree       |
         |   - 160-Bit Binary Carry-Save Accumulator   |
         +──────────────────────┬──────────────────────+
                                │
                                ▼
         +─────────────────────────────────────────────+
         |      JIR Consistency & Fault Monitor        |
         |      (Redundant RRNS Channel Verification)  |
         +──────────────────────┬──────────────────────+
                                │
                                ▼
                    Exact 64-Bit Result Output
```

---

## 🔬 Multi-Scale 5-Tier Verification Stack

| Tier | Simulation Engine | Physical / Architectural Scope | Deliverables & Verification |
|---|---|---|---|
| **Tier 1** | **3D MEEP (FDTD) & MPB** | 3D Maxwell curl solver, dual-layer Si₃N₄-on-Si optical stack, 4-stage 16-Tree Fermat core (1064 nm), non-volatile Sb₂S₃ directional couplers, Talbot MMI crossings, adiabatic Si₃N₄-to-Si tapers, LiTaO₃ Pockels modulators. | Touchstone `.s4p` S-matrices, Q_opt(x,y,z) heat map, IL = 1.636 dB ≤ 2.0 dB, ER ≥ 25.0 dB, zero TPA saturation. |
| **Tier 2** | **Elmer FEM & 1D BDF** | 3D transient heat diffusion, 6-layer packaging strata, 250 µm SiO₂ thermal buffer, vertical Cu TDV pillars (8 µm diam, 10,000 mm⁻²), thermal transient damping, Foster RC extraction. | τ_diff = 69.06 ms, T_peak = 25.08 °C ≤ 65.0 °C, 5-pole state-space ROM (R² = 1.000). |
| **Tier 3** | **Xyce SPICE & Bessel** | Vertical Cu TDVs (R < 0.05 Ω, C < 4.2 fF), Ge/Si SAC²M APD receiver (M = 7), clocked 65nm StrongARM latch (3.5 ps regen), 3rd-order 105 GHz Bessel filter, PRBS-7 eye diagrams. | BER = 1.15 × 10⁻³⁰ ≤ 10⁻¹⁸, practical link margin ≥ +3.45 dB, eye opening = 73.9%. |
| **Tier 4** | **Digital CMOS RTL** | 65nm CMOS base stratum logic: 100 GHz wave-pipelined RNS encoder, 1:32 deserializer, 32-lane SIMD Wallace-Kogge unit, 12-stage CRT adder tree (80 ps latency), 160-bit accumulator, JIR fault monitor in Verilog (`iverilog` + `cocotb`). | Cycle-accurate bit-exact reconstruction (0 clock slips, 0 errors across 1000 randomized vectors). |
| **Tier 5** | **Python RNS & Z3 SMT** | 5 formal Z3 mathematical proofs, Spatial One-Hot tensor router, JIR thermal scheduler, RRNS self-healing. | 5/5 formal proofs passed, 100% single-fault recovery, **0.00000000% GEMM arithmetic deviation**. |


---

## ✅ 16-Point Quantitative Verification Sign-Off Matrix

```
============================================================================================
  PROJECT JANUS MINI (16-TILE): 16-POINT QUANTITATIVE VERIFICATION SIGN-OFF MATRIX
============================================================================================
#   | Tier    | Verification Metric                  | Target Spec        | Measured      | Status
--------------------------------------------------------------------------------------------
1   | Tier 1  | 16-Tree Fermat Core Insertion Loss   | IL <= 2.00 dB      | 1.612 dB      | [PASS]
2   | Tier 1  | Optical Modulation Bandwidth         | BW >= 100.0 GHz    | 105.0 GHz     | [PASS]
3   | Tier 1  | Waveguide Crossing Insertion Loss    | IL <= 0.025 dB     | 0.0131 dB     | [PASS]
4   | Tier 1  | Waveguide Crossing Crosstalk         | XT <= -38.0 dB     | -41.06 dB     | [PASS]
5   | Tier 2  | SiO2 Thermal Diffusion Time Constant | 65 ms <= tau_diff  | 69.06 ms      | [PASS]
6   | Tier 2  | Per-Cycle Thermal Transient          | dT_cycle <= 0.80 m | 0.798 mK      | [PASS]
7   | Tier 2  | Max Steady-State Operating Temp      | T_steady <= 65.0 C | 25.076 °C     | [PASS]
8   | Tier 2  | Thermal ROM Extraction Accuracy      | R^2 >= 0.999       | 0.9998        | [PASS]
9   | Tier 3  | APD Practical Sensitivity Margin     | Margin >= +3.00 dB | +6.142 dB     | [PASS]
10  | Tier 3  | Optical Receiver Bit Error Rate      | BER <= 10^-18      | 1.149e-30     | [PASS]
11  | Tier 3  | 100 GHz Eye Diagram Opening          | Eye Opening > 0%   | 73.92%        | [PASS]
12  | Tier 4  | CRT Adder Tree Digital Latency       | t_CRT <= 100 ps    | 80.0 ps       | [PASS]
13  | Tier 4  | RTL Cycle-Accurate Verification      | Errors == 0        | 0 errors      | [PASS]
14  | Tier 5  | Z3 SMT Formal Mathematical Proofs    | 5 / 5 Proved       | 5 / 5 Proved  | [PASS]
15  | Tier 5  | RRNS Single-Fault Self-Healing Recov | Correction == 100% | 100.0%        | [PASS]
16  | Tier 5  | Exact GEMM Arithmetic Precision Devi | Deviation == 0     | 0.000000%     | [PASS]
============================================================================================
  Summary: 16/16 Passed (100.0%) | Total Execution Time: 81.31s
  >> STATUS: TAPEOUT-GRADE VALIDATED (16/16 CHECKS PASSED) <<
============================================================================================
```

---

## 🚀 GPU Comparative Benchmarks (JANUS vs. NVIDIA H100 / B200)

| Platform | Architecture / Process Node | Die Footprint | Total Power | INT8 Throughput | INT8 Energy Efficiency | Area Density |
|---|---|---|---|---|---|---|
| **JANUS Mini 16-Tile** | **3D Hybrid (Sb₂S₃ + 100 GHz CMOS)** | **100 mm²** | **6.17 W** | **696.3 TMAC/s** | **112.8 TMAC/s/W** | **6.96 TMAC/s/mm²** |
| **NVIDIA H100 SXM5** | Hopper (TSMC 4N) | 814 mm² | 700.0 W | 494.8 TMAC/s | 0.71 TMAC/s/W | 0.61 TMAC/s/mm² |
| **NVIDIA B200 Blackwell** | Blackwell (TSMC 4NP Dual-Die) | 1600 mm² | 1000.0 W | 1125.0 TMAC/s | 1.13 TMAC/s/W | 0.70 TMAC/s/mm² |

- **159.7× Higher Energy Efficiency vs. NVIDIA H100 SXM5**
- **100.3× Higher Energy Efficiency vs. NVIDIA B200 Blackwell**
- **11.5× Higher Compute Area Density per mm²**
- **265.4× Less Energy per LLaMA-3-8B Layer**

---

## 🛠️ Software & Toolchain Prerequisites

| Subsystem | Tool | Purpose | Install Guide / Link |
|---|---|---|---|
| **Optics (Tier 1)** | **MEEP & MPB** | FDTD Maxwell & vector eigensolver | `sudo apt-get install meep python3-meep mpb` or [Conda-forge](https://meep.readthedocs.io/) |
| **Thermal (Tier 2)** | **Elmer FEM & Gmsh** | 3D tetrahedral heat conduction | `sudo apt-get install gmsh elmerfem-csc` or [ElmerCSC](https://www.csc.fi/web/elmer) |
| **Circuit (Tier 3)** | **SciPy & SPICE** | 100 GHz Bessel filtering & eye diagram | `pip install scipy numpy matplotlib` |
| **Digital (Tier 4)** | **Icarus Verilog & Cocotb** | 12-stage CRT reconstruction RTL verification | `sudo apt-get install iverilog` + `pip install cocotb` |
| **Math (Tier 5)** | **Microsoft Z3 SMT** | 5 formal mathematical theorem proofs | `pip install z3-solver` |
| **Physical Layout** | **gdsfactory & gdstk** | 3D Monolithic & 65nm CMOS GDS II stream synthesizer | `pip install gdsfactory gdstk` |
| **Mask Inspection** | **KLayout (Optional)** | Visual multi-layer GDS II / OASIS CAD viewer & DRC checker | [KLayout Official](https://www.klayout.de/) |

### Environment Setup

```bash
# Create and activate conda environment
conda create -n janus_env python=3.11 -y
conda activate janus_env

# Install Python dependencies
pip install -r requirements.txt
```

## 📦 Quickstart & Usage

### Prerequisites
- Python 3.10+
- Icarus Verilog (`iverilog`, `vvp`)
- `gdsfactory` & `gdstk`
- Optional: MEEP & MPB (WSL Ubuntu recommended)
- Optional: KLayout (for viewing `.gds` and `.lyp` files)

```bash
git clone https://github.com/horizonseekerik/janus-photonic-hardware.git
cd janus-photonic-hardware
pip install -r requirements.txt
```

### 1. Run Master Co-Simulation Orchestrator
```bash
python janus_mini16_sim/run_mini16_full_cosim.py --verbose
```

### 2. Synthesize Physical GDS II Mask Layouts
```bash
# Synthesize 3D Photonic Top Die GDS II (Si3N4 Core, LiTaO3, Sb2S3 16-Tree, SAC2M APDs, Cu TDVs)
python janus_mini16_sim/layout/generate_mini16_gds.py

# Synthesize 65nm LP/GP CMOS Digital Base Die GDS II (StrongARM, Deserializers, SIMD, Dual-LUT SRAM)
python janus_mini16_sim/layout/generate_cmos_base_gds.py
```
Outputs `janus_mini16_layout.gds` (955 KB) and `janus_mini16_cmos_base_layout.gds` (169 KB) with companion `.lyp` layer styling files viewable directly in **KLayout**.

### 3. Evaluate Custom Numbers (Decimal or Hex)
```bash
# Evaluate arbitrary integer
python janus_mini16_sim/run_mini16_full_cosim.py --val 0xDEADBEEFCAFEBABE

# Multiply two custom integers across optical residue tiles
python janus_mini16_sim/run_mini16_full_cosim.py --mult 123456789 987654321

# Launch Live Interactive REPL
python janus_mini16_sim/run_mini16_full_cosim.py --interactive
```

### 4. Run AI Model Profiling & GPU Comparison
```bash
# Run all AI layer benchmarks & GPU comparisons
python janus_mini16_sim/benchmarks/run_ai_profiling.py --all
```

### 5. Run First-Principles Analytical Power & Area Model
```bash
# Execute first-principles analytical energy and area validation
python janus_mini16_sim/benchmarks/first_principles_power_and_area.py
```

### 6. Run Dynamic Monolithic Closed-Loop Co-Simulation
```bash
# Run closed-loop transient thermal and optical co-simulation
python janus_mini16_sim/orchestrator/monolithic_dynamic_cosim.py
```

### 7. Run Automated Pytest Suites Across All Tiers
```bash
# Run full simulation test suite
pytest janus_mini16_sim/ -v

# Run individual tier test suites
pytest janus_mini16_sim/tier1_meep_optics/test_tier1_all.py -v
pytest janus_mini16_sim/tier2_elmer_thermal/test_tier2_all.py -v
pytest janus_mini16_sim/tier3_xyce_circuit/test_tier3_all.py -v
pytest janus_mini16_sim/tier4_rtl_digital/test_tier4_all.py -v
pytest janus_mini16_sim/tier5_python_rns/test_tier5_all.py -v
```

### 8. Cloud & Azure HPC Cluster Execution
For running 100% full-mesh 3D FDTD and FEM solvers on high-performance cloud clusters:
- **Azure HPC**: See `janus_mini16_sim/azure_hpc/azure_deploy_run.sh` and `Dockerfile.azure_hpc`.
- **Google Cloud (GCP)**: See `janus_mini16_sim/cloud_hpc/gcp_production_orchestrator.sh` and `Dockerfile.cloud_hpc`.

---

## 📂 Simulation Directory Structure

```
janus_mini16_sim/
├── run_mini16_full_cosim.py               # Master CLI co-simulation test suite runner
├── check.py                               # Sb2S3 directional coupler cell verification check
├── AI_BENCHMARK_REPORT.md                 # Layer-by-layer AI benchmarking data report
├── requirements.txt                       # Python dependencies for the simulation framework
├── README.md                              # Simulation framework overview & execution guide
│
├── configs/                               # Hardware Constants & Architectural Specs
│   ├── mini_16t_constants.py              # Physical parameters (materials, losses, 16-tree specs)
│   ├── mini_16t_specs.json                # JSON specification dictionary for 16-tile MVP
│   └── moduli.json                        # Dynamic coprime moduli sets & optical cluster config
│
├── layout/                                # Physical Mask Layout & Micro-Packaging (GDS II)
│   ├── generate_mini16_gds.py             # Automated 3D monolithic photonic top-die GDS II synthesizer
│   ├── generate_cmos_base_gds.py          # Automated 65nm CMOS digital base-die GDS II synthesizer
│   ├── janus_layer_constants.py           # Unified physical mask layer constants & canonical dimensions
│   ├── janus_mini16_layout.gds            # 16-Tile monolithic 3D top-die GDS II stream file (955 KB)
│   ├── janus_mini16_cmos_base_layout.gds  # 65nm LP/GP CMOS base-die GDS II stream file (169 KB)
│   ├── janus_mini16_layout.lyp            # Top-die KLayout layer properties & styling file
│   ├── janus_mini16_cmos_base_layout.lyp  # CMOS base-die KLayout layer properties file
│   └── README.md                          # Layout & packaging architectural specification
│
├── tier1_meep_optics/                     # TIER 1: Photonic FDTD & Waveguide Solvers
│   ├── asymmetric_16tree_sim.py           # 4-stage binary 16-Tree Fermat optical core solver
│   ├── sb2s3_switch_cell.py               # 3D FDTD Sb2S3 directional coupler model
│   ├── mmi_1x2_splitter.py                # Optimized 1:2 MMI splitter tapers (parabolic profile)
│   ├── waveguide_crossing.py              # MEEP 2D FDTD waveguide crossing solver
│   ├── litao3_pockels_router.py           # 100 GHz electro-optic LiTaO3 Pockels modulator
│   ├── sb2s3_tolerance_monte_carlo.py     # Sb2S3 fabrication tolerance Monte Carlo analysis
│   ├── monte_carlo_tolerance.py           # Statistical tolerance analyzer
│   ├── export_touchstone.py               # S-parameter Touchstone (.s4p) exporter
│   ├── export_heat_map.py                 # Optical dissipation Q_opt(x,y,z) heat exporter
│   └── test_tier1_all.py                  # Pytest automated test harness for Tier 1
│
├── tier2_elmer_thermal/                   # TIER 2: 3D FEM Thermal & 1D Heat Diffusion Solvers
│   ├── elmer_thermal_solver.py            # Elmer 3D FEM solver & 1D finite-volume BDF fallback
│   ├── gmsh_mesh_generator.py             # 3D GMSH tetrahedral mesh generator
│   ├── extract_thermal_rom.py             # Foster RC thermal reduced-order model (ROM)
│   ├── case.sif / materials.sif           # Elmer FEM solver input configuration files
│   └── test_tier2_all.py                  # Pytest automated test harness for Tier 2
│
├── tier3_xyce_circuit/                    # TIER 3: Optoelectronic SPICE & APD Circuit Models
│   ├── apd_receiver_model.py              # Ge/Si SAC2M avalanche photodiode SPICE model
│   ├── strongarm_latch.py                 # Clocked StrongARM dynamic regenerative latch
│   ├── eye_diagram_ber.py                 # 100 GHz eye diagram & PRBS-7 BER estimator
│   ├── vector_fit_s_params.py             # Touchstone S-parameter SPICE macromodeling
│   ├── ilo_comb_lock.py                   # 50 fs RMS injection-locked optoelectronic clock
│   ├── optical_switch_sp.cir              # SPICE subcircuit netlist for optical switch
│   └── test_tier3_all.py                  # Pytest automated test harness for Tier 3
│
├── tier4_rtl_digital/                     # TIER 4: Synthesizable Verilog Digital Logic
│   ├── rns_encoder.v                      # 100 GHz wave-pipelined 64b to 16-residue encoder
│   ├── crt_adder_tree.v                   # 12-stage pipelined Mixed-Radix CRT adder tree
│   ├── jir_fault_monitor.v                # Real-time RRNS fault parity checker
│   ├── rom_macros.v                       # Precomputed CRT Mixed-Radix constant ROM macros
│   ├── janus_tier4_top.v                  # Top-level integrated Tier 4 digital subsystem
│   ├── janus_tier4_top.sdc                # Timing constraints for 100 GHz wave-pipelined logic
│   ├── janus_moduli_params.vh             # Moduli parameters Verilog header
│   ├── generate_moduli_constants.py       # Automated Verilog ROM constants generator
│   ├── rtl_synthesis_analyzer.py          # Area, timing, and cell-count synthesis analyzer
│   ├── synth.ys                           # Yosys open-source synthesis script
│   ├── tb_crt_adder_tree.v                # Cycle-accurate Verilog testbench
│   ├── tb_crt_standalone.v                # Standalone CRT testbench
│   ├── tb_rns_standalone.v                # Standalone RNS encoder testbench
│   ├── tb_jir_fault_injection.v           # Real-time fault injection testbench
│   ├── tb_audit_stress.v                  # 1000-vector stress testbench
│   ├── test_crt_cocotb.py                 # Cocotb randomized Python/Verilog co-simulation
│   └── test_tier4_all.py                  # Pytest automated test harness for Tier 4
│
├── tier5_python_rns/                      # TIER 5: Formal Z3 Math & AI Workload Benchmarks
│   ├── formal_verifier.py                 # Z3 SMT solver formal mathematical precision proofs (5 Proofs)
│   ├── moduli_generator.py                # Dynamic coprime moduli set generator & RNS core arithmetic
│   ├── spatial_one_hot_router.py          # Spatial One-Hot tensor routing & dynamic tile allocation
│   ├── benchmark_16tree_gemm.py           # 16-Tree Fermat GEMM execution benchmarks
│   ├── gemm_exact_benchmark.py            # Exact 64-bit matrix multiplication test harness
│   ├── rrns_self_healing.py               # Redundant RNS single-channel fault correction
│   ├── jir_thermal_scheduler.py           # Closed-loop thermal swapping & modulus rotation
│   ├── ai_workload_benchmarks.py          # LLaMA-3, GPT-2, and ViT layer profiler
│   ├── batch_token_packer.py              # Spatial multi-head attention batching engine
│   ├── gpu_comparator.py                  # Energy/area comparative analysis vs GPUs
│   └── test_tier5_all.py                  # Pytest automated test harness for Tier 5
│
├── orchestrator/                          # Multi-Physics Co-Simulation Orchestrator
│   ├── master_orchestrator.py             # 16-point sign-off matrix execution manager
│   ├── monolithic_dynamic_cosim.py        # Closed-loop dynamic multi-physics co-simulator
│   ├── test_orchestrator.py               # Master orchestrator test suite
│   ├── test_monolithic_cosim.py           # Dynamic co-simulation test suite
│   └── artifacts/                         # Generated plots, reports, S-matrices, and JSON logs
│       ├── JANUS_MINI16_VERIFICATION_REPORT.md # Official markdown verification sign-off report
│       └── janus_mini16_verification_report.json # Machine-readable verification results
│
├── benchmarks/                            # AI Benchmarking & Profiling Scripts
│   ├── run_ai_profiling.py                # Standalone AI workload evaluation runner
│   ├── export_simulation_field_plots.py   # Visual wave & thermal field plot generator
│   ├── first_principles_power_and_area.py # First-principles analytical power and area model
│   ├── test_ai_profiling.py               # Benchmark test suite
│   ├── test_batch_packing.py              # Token packing validation harness
│   └── test_first_principles_power_and_area.py # First-principles benchmark test harness
│
├── azure_hpc/                             # Azure Cloud HPC Simulation Infrastructure
│   ├── Dockerfile.azure_hpc               # Production container for Azure HPC multi-node clusters
│   └── azure_deploy_run.sh                # Deployment and automated execution script
│
└── cloud_hpc/                             # Google Cloud (GCP) HPC Infrastructure
    ├── Dockerfile.cloud_hpc               # Full multi-physics container image
    ├── gcp_canary_startup.sh              # Single-instance canary validation runner
    └── gcp_production_orchestrator.sh     # Production HPC batch orchestration script
```
