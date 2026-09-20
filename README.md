# Project JANUS: Spatial Optical RNS Photonic AI Computing Architecture

[![Live Platform](https://img.shields.io/badge/Live%20Platform-Vercel%20Deployed-00f2fe.svg)](https://janus-photonic-hardware.vercel.app/)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.22733656.svg)](https://doi.org/10.5281/zenodo.22733656)
[![Architecture Treatise](https://img.shields.io/badge/Architecture%20Treatise-39%20Pages%20(IEEEtran)-blue.svg)](./JANUS_IEEE_Manuscript.pdf)
[![Patent Pending](https://img.shields.io/badge/Indian%20Patent-App%20202611052791-gold.svg)](#-patent--intellectual-property)
[![TRL Readiness](https://img.shields.io/badge/TRL-4.0%20(Co--Sim%20Validated)-green.svg)](#-master-hardware-scaling-roadmap-18-models)
[![Simulation Matrix](https://img.shields.io/badge/Simulation%20Targets-16%2F16%20Met%20(100%25)-brightgreen.svg)](#-16-point-multi-physics-sign-off-matrix)
[![Modeled Efficiency](https://img.shields.io/badge/Modeled%20Efficiency-112.8%20TMAC%2Fs%2FW-cyan.svg)](#-ai-workload-benchmarks--gpu-comparison)
[![Static Power](https://img.shields.io/badge/Static%20Hold%20Power-0%20Watts-purple.svg)](#-architectural-pillars)

---

## 📖 Executive Summary

**Project JANUS** is a constraint-aware, bounded-exact optoelectronic tensor computing architecture engineered for high-throughput, low-power deep learning acceleration. 

Conventional optical AI processors encode numbers in continuous analog amplitudes (Mach-Zehnder Interferometers / MZIs), accumulating optical power across analog meshes. For a 128 × 128 matrix multiplication, unreduced analog accumulation requires an impossible **138.4 dB SNR** (demanding a 21-bit ADC at 100 GHz sampling) and continuous milliwatt thermal tuning that consumes kilowatts of static hold power.

**JANUS solves the fundamental optical computing bottleneck by replacing analog amplitude accumulation with:**
1. **Spatial One-Hot Residue Number System (RNS):** Numbers are mapped to spatial waveguide indices (which discrete waveguide carries light) rather than optical intensity levels.
2. **Asymmetric 16-Tree Fermat Optical Multipliers:** Optical multiplication is mapped to cyclic permutations over Fermat prime fields (ℤ₁₇* ≅ ℤ₁₆) using a 4-stage binary decision tree of non-volatile Sb₂S₃ phase-change switches—slashing insertion loss to **1.61 dB** (down from 6.06 dB in traditional 15-stage Beneš networks) with **zero static hold power (P_hold = 0 W)**.
3. **Dynamic Greedy Descending Coprime Moduli Engine:** Dynamically selects optimal minimal coprime sets incorporating Fermat modulus F₂ = 257 and composite modulus 255. Dynamically power-gates unused optical tiles (saving up to 87.5% dynamic energy for narrow bit-widths), with seamless fallback to **The Memory Trick & Three Equations (Hybrid Optical-Memory PRNS)** for arbitrary large dynamic range.
4. **Receiverless Ge/Si SAC²M Avalanche Photodiodes (APDs):** 1-bit binary arrival detection co-integrated with clocked StrongARM dynamic latches (3.5 ps latching time, ~100 aJ per sensing event).
5. **Pipelined CMOS Mixed-Radix CRT Adder Tree:** Cycle-accurate 12-stage Garner CRT reconstruction operating with deterministic exact arithmetic up to **INT64 precision with 0 deviation**.

---

## 🏛️ Architectural Pillars

```
                      Input 64-Bit Operands (X, Y)
                                  │
                                  ▼
           +─────────────────────────────────────────────+
           |     CMOS 4-Stage RNS Modulo Encoders        |
           |     (Decomposes into 16 coprime channels)   |
           +──────────────────────┬──────────────────────+
                                  │
                                  ▼
           +─────────────────────────────────────────────+
           |   16-Tile Asymmetric 16-Tree Fermat Core    |
           |   - 1-of-17 Spatial Optical Waveguide Mesh  |
           |   - 4-Stage Non-Volatile Sb2S3 Switch Tree  |
           |   - Zero Static Hold Power (P_hold = 0 W)   |
           |   - Dynamic Optical Tile Gating (Up to 16)  |
           +──────────────────────┬──────────────────────+
                                  │
                                  ▼
           +─────────────────────────────────────────────+
           |   Ge/Si SAC2M APDs + Clocked StrongARM      |
           |   (Event-Driven Binary Sensing, ~100 aJ)    |
           +──────────────────────┬──────────────────────+
                                  │
                                  ▼
           +─────────────────────────────────────────────+
           |   12-Stage Pipelined CRT Adder Tree (80 ps) |
           |   - 256-Entry ROM Precomputed Scaling LUTs  |
           |   - Cycle-Exact Garner Mixed-Radix Engine   |
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

## 📁 Repository Directory & File Guide

Below is the complete inventory and navigation guide for every folder and file in this repository:

```
Janus Update/
├── README.md                                  # Complete Project Documentation & Navigation Guide
├── index.html                                 # Production Single-Page Web Platform & Interactive Dashboard
├── manifest.json                              # PWA Web App Manifest (Standalone App Installability)
├── vercel.json                                # Vercel deployment routing and cache headers
├── requirements.txt                           # Python environment dependencies
├── run_dashboard.py                           # Dedicated zero-dependency local WSGI runner
├── start_dashboard.vbs                        # Background launcher script for Windows
├── JANUS_IEEE_Manuscript.pdf                  # Complete 39-page formally verified IEEE manuscript
├── JANUS_Mini16_Simulation_Report.pdf         # Multi-physics co-simulation sign-off report (9-Page with GDS II)
├── JANUS_Mini16_CMOS_Architecture.pdf         # CMOS digital backend & silicon blueprint
├── janus_mini16_layout.gds                    # Tapeout-grade photonic 3D top-die GDS II mask (955 KB)
├── janus_mini16_cmos_base_layout.gds          # 65nm CMOS digital base-die GDS II mask (169 KB)
├── janus_mini16_layout.lyp                    # KLayout layer properties & styling definition
├── fig_gds_die_and_tile_floorplan.png         # 300 DPI composite full-die & single-tile mask floorplan
├── main.pdf                                   # Compiled root manuscript
├── deep-research-report.md                    # In-depth architectural synthesis research report
├── JANUS_ASYMMETRIC_16TREE_ARCHITECTURE.md    # 4-Stage Fermat Core mathematical & physical specification
├── apple-touch-icon.png                       # iOS / Mobile web app icon
├── favicon-16x16.png / favicon-32x32.png      # Browser tab favicons
│
├── api/                                       # Serverless API Runtime (Vercel & Local WSGI)
│   └── index.py                               # Unified REST API router & multi-physics solver dispatcher
│
├── public/                                    # Static Distribution Directory (CDN / Vercel Mirror)
│   ├── index.html                             # Synced web interface for CDN hosting
│   ├── manifest.json                          # Synced PWA web app manifest
│   ├── apple-touch-icon.png                   # Synced mobile web icon
│   ├── favicon-16x16.png / favicon-32x32.png  # Synced browser favicons
│   ├── JANUS_IEEE_Manuscript.pdf              # Hosted IEEE manuscript
│   ├── JANUS_Mini16_Simulation_Report.pdf     # Hosted simulation report
│   ├── JANUS_Mini16_CMOS_Architecture.pdf     # Hosted CMOS specification
│   ├── main.pdf                               # Hosted paper
│   ├── documentation_reports/                 # Mirror of technical documentation reports
│   └── Simulation Changes for 100%/           # Mirror of 100% simulation & OFC guides
│
├── scripts/                                   # Automation & Synchronization Tooling
│   └── sync_simulation_repo.py                # Automated synchronization tool for janus-simulation repository
│
├── Simulation Changes for 100%/               # Uncompromised Simulation & Paper Submission Guides
│   ├── OFC_2027_3PAGE_PAPER_AUTHORING_GUIDE.md # Critical checklist, tone guidelines & reviewer defenses
│   ├── PROJECT_JANUS_AZURE_HPC_UPGRADE_ROADMAP.md # Azure Cloud HPC migration & simulation fidelity roadmap
│   ├── PROJECT_JANUS_GCP_100_PERCENT_SIMULATION_GUIDE.md # Google Cloud (GCP) 100% uncompromised simulation guide
│   └── PROJECT_JANUS_HIGHER_ORDER_EDGE_CASES.md # Comprehensive 32-point physical edge-case audit
│
├── Janus Interactive Visulaization/           # 3D Architectural Visualization & Frame Renders
│   ├── JANUS_Mini16_3D_Development_Spec.md    # Master engineering specification & layer-by-layer guide
│   └── renders/                               # 3D cinematic frame sequences & architectural renders
│
├── janus_mini16_sim/                          # 5-Tier Multi-Physics Co-Simulation Framework
│   ├── run_mini16_full_cosim.py               # Master CLI co-simulation test suite runner
│   ├── check.py                               # Sb2S3 directional coupler cell verification check
│   ├── AI_BENCHMARK_REPORT.md                 # Layer-by-layer AI benchmarking data report
│   ├── requirements.txt                       # Python dependencies for the simulation framework
│   ├── README.md                              # Simulation framework overview & execution guide
│   │
│   ├── configs/                               # Hardware Constants & Architectural Specs
│   │   ├── mini_16t_constants.py              # Physical parameters (materials, losses, 16-tree specs)
│   │   ├── mini_16t_specs.json                # JSON specification dictionary for 16-tile MVP
│   │   └── moduli.json                        # Dynamic coprime moduli sets & optical cluster config
│   │
│   ├── layout/                                # Physical Mask Layout & Micro-Packaging (GDS II)
│   │   ├── generate_mini16_gds.py             # Automated 3D monolithic photonic top-die GDS II synthesizer
│   │   ├── generate_cmos_base_gds.py          # Automated 65nm CMOS digital base-die GDS II synthesizer
│   │   ├── janus_layer_constants.py           # Unified physical mask layer constants & canonical dimensions
│   │   ├── janus_mini16_layout.gds            # 16-Tile monolithic 3D top-die GDS II stream file (955 KB)
│   │   ├── janus_mini16_cmos_base_layout.gds  # 65nm LP/GP CMOS base-die GDS II stream file (169 KB)
│   │   ├── janus_mini16_layout.lyp            # Top-die KLayout layer properties & styling file
│   │   ├── janus_mini16_cmos_base_layout.lyp  # CMOS base-die KLayout layer properties file
│   │   └── README.md                          # Layout & packaging architectural specification
│   │
│   ├── tier1_meep_optics/                     # TIER 1: Photonic FDTD & Waveguide Solvers
│   │   ├── asymmetric_16tree_sim.py           # 4-stage binary 16-Tree Fermat optical core solver
│   │   ├── sb2s3_switch_cell.py               # 3D FDTD Sb2S3 directional coupler model
│   │   ├── mmi_1x2_splitter.py                # Optimized 1:2 MMI splitter tapers (parabolic profile)
│   │   ├── waveguide_crossing.py              # MEEP 2D FDTD waveguide crossing solver
│   │   ├── litao3_pockels_router.py           # 100 GHz electro-optic LiTaO3 Pockels modulator
│   │   ├── sb2s3_tolerance_monte_carlo.py     # Sb2S3 fabrication tolerance Monte Carlo analysis
│   │   ├── monte_carlo_tolerance.py           # Statistical tolerance analyzer
│   │   ├── export_touchstone.py               # S-parameter Touchstone (.s4p) exporter
│   │   ├── export_heat_map.py                 # Optical dissipation Q_opt(x,y,z) heat exporter
│   │   └── test_tier1_all.py                  # Pytest automated test harness for Tier 1
│   │
│   ├── tier2_elmer_thermal/                   # TIER 2: 3D FEM Thermal & 1D Heat Diffusion Solvers
│   │   ├── elmer_thermal_solver.py            # Elmer 3D FEM solver & 1D finite-volume BDF fallback
│   │   ├── gmsh_mesh_generator.py             # 3D GMSH tetrahedral mesh generator
│   │   ├── extract_thermal_rom.py             # Foster RC thermal reduced-order model (ROM)
│   │   ├── case.sif / materials.sif           # Elmer FEM solver input configuration files
│   │   └── test_tier2_all.py                  # Pytest automated test harness for Tier 2
│   │
│   ├── tier3_xyce_circuit/                    # TIER 3: Optoelectronic SPICE & APD Circuit Models
│   │   ├── apd_receiver_model.py              # Ge/Si SAC2M avalanche photodiode SPICE model
│   │   ├── strongarm_latch.py                 # Clocked StrongARM dynamic regenerative latch
│   │   ├── eye_diagram_ber.py                 # 100 GHz eye diagram & PRBS-7 BER estimator
│   │   ├── vector_fit_s_params.py             # Touchstone S-parameter SPICE macromodeling
│   │   ├── ilo_comb_lock.py                   # 50 fs RMS injection-locked optoelectronic clock
│   │   ├── optical_switch_sp.cir              # SPICE subcircuit netlist for optical switch
│   │   └── test_tier3_all.py                  # Pytest automated test harness for Tier 3
│   │
│   ├── tier4_rtl_digital/                     # TIER 4: Synthesizable Verilog Digital Logic
│   │   ├── rns_encoder.v                      # 100 GHz wave-pipelined 64b to 16-residue encoder
│   │   ├── crt_adder_tree.v                   # 12-stage pipelined Mixed-Radix CRT adder tree
│   │   ├── jir_fault_monitor.v                # Real-time RRNS fault parity checker
│   │   ├── rom_macros.v                       # Precomputed CRT Mixed-Radix constant ROM macros
│   │   ├── janus_tier4_top.v                  # Top-level integrated Tier 4 digital subsystem
│   │   ├── janus_tier4_top.sdc                # Timing constraints for 100 GHz wave-pipelined logic
│   │   ├── janus_moduli_params.vh             # Moduli parameters Verilog header
│   │   ├── generate_moduli_constants.py       # Automated Verilog ROM constants generator
│   │   ├── rtl_synthesis_analyzer.py          # Area, timing, and cell-count synthesis analyzer
│   │   ├── synth.ys                           # Yosys open-source synthesis script
│   │   ├── tb_crt_adder_tree.v                # Cycle-accurate Verilog testbench
│   │   ├── tb_crt_standalone.v                # Standalone CRT testbench
│   │   ├── tb_rns_standalone.v                # Standalone RNS encoder testbench
│   │   ├── tb_jir_fault_injection.v           # Real-time fault injection testbench
│   │   ├── tb_audit_stress.v                  # 1000-vector stress testbench
│   │   ├── test_crt_cocotb.py                 # Cocotb randomized Python/Verilog co-simulation
│   │   └── test_tier4_all.py                  # Pytest automated test harness for Tier 4
│   │
│   ├── tier5_python_rns/                      # TIER 5: Formal Z3 Math & AI Workload Benchmarks
│   │   ├── formal_verifier.py                 # Z3 SMT solver formal mathematical precision proofs (5 Proofs)
│   │   ├── moduli_generator.py                # Dynamic coprime moduli set generator & RNS core arithmetic
│   │   ├── spatial_one_hot_router.py          # Spatial One-Hot tensor routing & dynamic tile allocation
│   │   ├── benchmark_16tree_gemm.py           # 16-Tree Fermat GEMM execution benchmarks
│   │   ├── gemm_exact_benchmark.py            # Exact 64-bit matrix multiplication test harness
│   │   ├── rrns_self_healing.py               # Redundant RNS single-channel fault correction
│   │   ├── jir_thermal_scheduler.py           # Closed-loop thermal swapping & modulus rotation
│   │   ├── ai_workload_benchmarks.py          # LLaMA-3, GPT-2, and ViT layer profiler
│   │   ├── batch_token_packer.py              # Spatial multi-head attention batching engine
│   │   ├── gpu_comparator.py                  # Energy/area comparative analysis vs GPUs
│   │   └── test_tier5_all.py                  # Pytest automated test harness for Tier 5
│   │
│   ├── orchestrator/                          # Multi-Physics Co-Simulation Orchestrator
│   │   ├── master_orchestrator.py             # 16-point sign-off matrix execution manager
│   │   ├── monolithic_dynamic_cosim.py        # Closed-loop dynamic multi-physics co-simulator
│   │   ├── test_orchestrator.py               # Master orchestrator test suite
│   │   ├── test_monolithic_cosim.py           # Dynamic co-simulation test suite
│   │   └── artifacts/                         # Generated plots, reports, S-matrices, and JSON logs
│   │       ├── JANUS_MINI16_VERIFICATION_REPORT.md # Official markdown verification sign-off report
│   │       └── janus_mini16_verification_report.json # Machine-readable verification results
│   │
│   ├── benchmarks/                            # AI Benchmarking & Profiling Scripts
│   │   ├── run_ai_profiling.py                # Standalone AI workload evaluation runner
│   │   ├── export_simulation_field_plots.py   # Visual wave & thermal field plot generator
│   │   ├── first_principles_power_and_area.py # First-principles analytical power and area model
│   │   ├── test_ai_profiling.py               # Benchmark test suite
│   │   ├── test_batch_packing.py              # Token packing validation harness
│   │   └── test_first_principles_power_and_area.py # First-principles benchmark test harness
│   │
│   ├── azure_hpc/                             # Azure Cloud HPC Simulation Infrastructure
│   │   ├── Dockerfile.azure_hpc               # Production container for Azure HPC multi-node clusters
│   │   └── azure_deploy_run.sh                # Deployment and automated execution script
│   │
│   └── cloud_hpc/                             # Google Cloud (GCP) HPC Infrastructure
│       ├── Dockerfile.cloud_hpc               # Full multi-physics container image
│       ├── gcp_canary_startup.sh              # Single-instance canary validation runner
│       └── gcp_production_orchestrator.sh     # Production HPC batch orchestration script
│
├── documentation_reports/                     # Complete Engineering Specifications & Roadmaps
│   ├── JANUS_MINI_16T_CO_SIMULATION_SPEC.pdf  # Comprehensive Multi-Physics Spec (PDF/MD/HTML)
│   ├── JANUS_MINI_16T_ALGORITHMS_AND_FLOWCHARTS.pdf # Mathematical algorithms & pipeline charts
│   ├── PROJECT_JANUS_STRATEGIC_ROADMAP.pdf    # Commercialization & 18-Model Matrix Guide
│   ├── PROJECT_JANUS_AZURE_HPC_UPGRADE_ROADMAP.md # Azure Cloud HPC upgrade guide
│   ├── deep-research-report.md                # In-depth architectural synthesis research report
│   └── figures/                               # Architectural diagrams, field plots, and schematics
│
├── paper_latex/                               # 39-Page Primary IEEE Architecture Manuscript
│   ├── main.tex                               # Full LaTeX source code (IEEEtran format)
│   ├── references.bib                         # Academic bibliography database
│   ├── main.pdf                               # Formally compiled PDF manuscript
│   ├── PCM_MATERIAL_SELECTION_RATIONALE.md    # Thermodynamic & optical analysis of Sb2S3
│   └── rns_64bit_architecture_update.md       # 64-bit RNS architecture update report
│
├── cmos_paper_latex/                          # IEEE CMOS Backend Architecture Specification
│   ├── JANUS_Mini16_CMOS_Architecture.tex     # LaTeX source for companion CMOS paper
│   ├── references.bib                         # CMOS bibliography database
│   ├── figures/                               # CMOS high-resolution figures
│   ├── JANUS_Mini16_CMOS_Architecture.pdf     # Compiled CMOS architecture PDF
│   └── JANUS_MINI16_CMOS_ARCHITECTURE_SPEC.md # Full CMOS architecture specification
│
├── simulation_paper_latex/                    # IEEE Co-Simulation Sign-Off Paper
│   ├── JANUS_Mini16_Simulation_Report.tex     # LaTeX source for companion simulation paper
│   ├── references.bib                         # Simulation bibliography database
│   ├── figures/                               # Multi-physics simulation figures
│   └── JANUS_Mini16_Simulation_Report.pdf     # Compiled simulation sign-off PDF
│
└── CMOS RECONSTRUCTION/                       # Archival Silicon Specifications
    └── JANUS_CMOS_Architecture.pdf            # Initial CMOS reconstruction spec
```

---

## 🔬 Multi-Scale 5-Tier Verification Stack

| Tier | Simulation Engine | Physical / Architectural Scope | Deliverables & Verification |
|---|---|---|---|
| **Tier 1** | **3D MEEP (FDTD) & MPB** | 3D Maxwell curl solver, 4-stage 16-Tree Fermat optical core (1064 nm), non-volatile Sb₂S₃ directional couplers, MMI crossings, LiTaO₃ Pockels routers. | Touchstone `.s4p` S-matrices, Q_opt(x,y,z) heat map, IL = 1.612 dB ≤ 2.0 dB, ER ≥ 25.0 dB. |
| **Tier 2** | **Elmer FEM & 1D BDF** | 3D transient heat diffusion, 6-layer packaging strata, 250 µm SiO₂ buffer, thermal transient damping, Foster RC extraction. | τ_diff = 69.06 ms, T_peak = 25.08 °C ≤ 65.0 °C, 5-pole state-space ROM (R² = 1.000). |
| **Tier 3** | **Xyce SPICE & Bessel** | Ge/Si SAC²M APD receiver (M = 7), clocked StrongARM latch (3.5 ps regen), 3rd-order 105 GHz Bessel filter, PRBS-7 eye diagrams. | BER = 1.15 × 10⁻³⁰ ≤ 10⁻¹⁸, practical link margin ≥ +3.45 dB, eye opening = 73.9%. |
| **Tier 4** | **Digital CMOS RTL** | 100 GHz wave-pipelined RNS encoder, 12-stage CRT adder tree (80 ps latency), JIR fault monitor in Verilog (`iverilog` + `cocotb`). | Cycle-accurate bit-exact reconstruction (0 clock slips, 0 errors across 1000 randomized vectors). |
| **Tier 5** | **Python RNS & Z3 SMT** | 5 formal Z3 mathematical proofs, Spatial One-Hot tensor router, JIR thermal scheduler, RRNS self-healing. | 5/5 formal proofs passed, 100% single-fault recovery, **0.00000000% GEMM arithmetic deviation**. |

---

## ✅ 16-Point Multi-Physics Sign-Off Matrix

The automated multi-physics co-simulation suite completes in **~81.31s** with a **100.0% pass rate** across all 16 verification checks:

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
  Summary: 16/16 Passed (100.0%) | Execution Time: 81.31s | STATUS: TAPEOUT-READY (TRL 4)
============================================================================================
```

---

## 🗺️ Master Hardware Scaling Roadmap (18 Models)

Project JANUS scales from an entry **Model 1A Monolithic Planar MVP (6.17 W)** up to a **Model 6B 5-Stratum 3D Hyperscale Apex Module (104.85 PetaMAC/s at 392 W)** across 6 generations and 18 distinct hardware configurations:

| Model | Generation & Stack | Strata | Tiles | Mesh Size | Total Switches | Die Area | Total Power | INT8 Throughput | INT64 Throughput | TRL Status |
|:---:|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **1A** | Gen-1 Monolithic Planar MVP | 1 | 16 | 32 x 32 | 31.46 M | 100.0 mm² | **6.17 W** | 696.3 TMAC/s | 87.0 TMAC/s | **TRL 4 (Co-Sim Verified)** |
| **1B** | Gen-1 Monolithic Planar Full | 1 | 32 | 32 x 32 | 62.91 M | 200.0 mm² | **12.67 W** | 1,392.6 TMAC/s | 174.1 TMAC/s | TRL 3 (Analytical Proof) |
| **2A** | Gen-2 Monolithic Planar Edge | 1 | 16 | 64 x 64 | 125.83 M | 400.0 mm² | 23.49 W | 2,785.3 TMAC/s | 348.2 TMAC/s | TRL 3 (Analytical Proof) |
| **2B** | Gen-2 3D Mini Stack (50 mm²) | 2 | 16 | 32 x 32 | 31.46 M | 50.0 mm² | **6.17 W** | 696.3 TMAC/s | 87.0 TMAC/s | TRL 3 (Analytical Proof) |
| **2C** | Gen-2 3D Mini Stack (100 mm²) | 2 | 32 | 32 x 32 | 62.91 M | 100.0 mm² | **12.67 W** | 1,392.6 TMAC/s | 174.1 TMAC/s | TRL 3 (Analytical Proof) |
| **3A** | Gen-3 3D Mini Stack (200 mm²) | 2 | 64 | 32 x 32 | 125.83 M | 200.0 mm² | 23.49 W | 2,785.3 TMAC/s | 348.2 TMAC/s | TRL 3 (Analytical Proof) |
| **3B** | Gen-3 3D Edge Stack (200 mm²) | 2 | 16 | 64 x 64 | 125.83 M | 200.0 mm² | 23.49 W | 2,785.3 TMAC/s | 348.2 TMAC/s | TRL 3 (Analytical Proof) |
| **3C** | Gen-3 3D Edge Stack (400 mm²) | 2 | 32 | 64 x 64 | 251.66 M | 400.0 mm² | 45.91 W | 5,570.6 TMAC/s | 696.3 TMAC/s | TRL 3 (Analytical Proof) |
| **4E** | Gen-4 3D Edge Flagship | 3 | 64 | 64 x 64 | 503.32 M | 533.3 mm² | 92.97 W | 11,141.1 TMAC/s | 1,392.6 TMAC/s | TRL 3 (Analytical Proof) |
| **5D** | Gen-5 3D Datacenter MVP | 4 | 16 | 128 x 128 | 503.32 M | 400.0 mm² | 90.39 W | 11,141.1 TMAC/s | 1,392.6 TMAC/s | TRL 3 (Analytical Proof) |
| **6A** | Gen-6 3D Datacenter Master | 5 | 32 | 128 x 128 | **1.0066 B** | 640.0 mm² | 186.65 W | 22,282.2 TMAC/s | 2,785.3 TMAC/s | TRL 3 (Analytical Proof) |
| **6B** | Gen-6 3D Hyperscale Apex Module | 5 | 64 | 128 x 128 | **2.0132 B** | 1,280.0 mm² | **392.36 W** | **52.42 PMAC/s** | **5,570.6 TMAC/s** | TRL 3 (Analytical Proof) |

---

## 🤖 AI Workload Benchmarks & GPU Comparison

### Model Inference Performance (Model 1A: 6.17 W)
* **LLaMA-3-8B (INT8):** 1.938 µJ per autoregressive token (112.55 TMAC/s/W average efficiency).
* **GPT-2 Base (INT8):** 0.098 µJ per token (113.82 TMAC/s/W).
* **ViT-Huge (INT8):** 1.423 µJ per image patch pass (112.98 TMAC/s/W).

### Hardware Efficiency Comparison Table

| Accelerator Platform | Architecture & Process | TDP Power (W) | Peak INT8 Throughput | Energy Efficiency (TMAC/s/W) | Advantage vs Platform |
|---|---|:---:|:---:|:---:|:---:|
| **Project JANUS (Model 1A)** | **Spatial RNS Photonic (3D Heterogeneous)** | **6.17 W** | **696.3 TMAC/s** | **112.8 TMAC/s/W** | **Baseline (1.0x)** |
| NVIDIA H100 SXM5 | 4N Silicon Electronic GPU | 700 W | 494.0 TMAC/s | 0.706 TMAC/s/W | **159.7x JANUS Advantage** |
| NVIDIA B200 (Blackwell) | 4NP Silicon Electronic GPU | 1,000 W | 1,125.0 TMAC/s | 1.125 TMAC/s/W | **100.3x JANUS Advantage** |
| Google TPU v5p | 4nm Electronic TPU | 450 W | 459.0 TMAC/s | 1.020 TMAC/s/W | **110.6x JANUS Advantage** |

---

## 🌐 Web Platform & Interactive User Experience

The web platform ([janus-photonic-hardware.vercel.app](https://janus-photonic-hardware.vercel.app/)) hosts a complete interactive research laboratory:

1. **🍪 GDPR / CCPA Cookie & Local Storage Consent Banner:**
   - First-arrival floating consent banner offering **Accept All**, **Decline Non-Essential**, and **Preferences**.
   - Persistent **Cookie & Storage Settings** modal accessible anytime via the footer.
2. **🔒 Privacy Governance & Transparency Modals:**
   - **Privacy Policy Modal:** Zero-surveillance guarantee, no PII collection, local storage disclosure, and GDPR/CCPA data rights.
   - **Terms of Research Use Modal:** Academic open-access terms (CC BY 4.0), non-commercial replication rights, and simulation disclaimers.
   - **Academic Citation Export Modal:** Instant 1-click clipboard export for **BibTeX**, **IEEE format**, and **APA 7th edition** with Zenodo DOI badge.
   - **Keyboard Shortcuts Modal:** Interactive hotkey cheat sheet (`?` or `H`).
3. **⌨️ Global Keyboard Navigation:**
   - `1` – `8`: Jump directly to Pages 1 through 8.
   - `T`: Toggle between Light and Dark mode with live toast feedback.
   - `S`: Quick jump to the Co-Simulation Suite.
   - `Esc`: Dismiss any open modal dialog.
4. **▲ Floating Utilities & Toasts:**
   - Scroll-triggered **Back to Top** floating action button.
   - Glassmorphic toast notification stack for instant feedback.
5. **📱 Installable Progressive Web App (PWA):**
   - Configured with `manifest.json`, high-resolution touch icons, and standalone display support.
6. **🖨️ Optimized Print Stylesheet:**
   - Clean, publication-grade paper/PDF output via browser printing (`Ctrl+P`).

---

## 🛠️ Complete Software & Toolchain Prerequisites

Project JANUS combines multi-physics photonic wave mechanics, 3D FEM thermal diffusion, optoelectronic circuit SPICE, digital CMOS RTL logic, and SMT formal theorem proving. Below is the complete layer-by-layer dependency breakdown:

### 🧩 Tier-by-Tier Dependency Matrix

| Tier / Subsystem | Tool / Engine | Purpose in Project JANUS | Supported OS | Official Link / Docs |
|---|---|---|---|---|
| **Environment** | **Miniconda / Conda** | Python virtual environment management & binary package resolution | Windows, Linux, macOS | [Miniconda Docs](https://docs.conda.io/en/latest/miniconda.html) |
| **Tier 1 (Optics)** | **MEEP (Python API)** | Finite-Difference Time-Domain (FDTD) 3D Maxwell curl solver for optical couplers, crossings, and pulse routing | Linux, WSL (Ubuntu), macOS | [MEEP FDTD Docs](https://meep.readthedocs.io/en/latest/) |
| **Tier 1 (Optics)** | **MPB (Photonic Bands)** | Frequency-domain vector Maxwell eigensolver for optical modes, n_eff, and L_π | Linux, WSL (Ubuntu), macOS | [MPB Documentation](https://mpb.readthedocs.io/en/latest/) |
| **Tier 2 (Thermal)** | **Elmer FEM** | 3D finite-element multiphysics solver for transient and steady-state thermal diffusion across packaging strata | Linux, WSL, Windows | [Elmer FEM Official](https://www.csc.fi/web/elmer) |
| **Tier 2 (Thermal)** | **Gmsh** | 3D tetrahedral finite-element mesh generator for heterogeneous chiplet geometries | Linux, Windows, macOS | [Gmsh Reference](https://gmsh.info/) |
| **Tier 2 (Thermal)** | **SciPy (BDF Solver)** | 1D multi-layer finite-volume stiff ODE backward differentiation solver (built-in physical fallback) | All Platforms | [SciPy solve_ivp](https://docs.scipy.org/doc/scipy/reference/generated/scipy.integrate.solve_ivp.html) |
| **Tier 3 (Circuits)**| **SciPy & NumPy** | 3rd-order Bessel-Thomson anti-aliasing filter, Gustavsen vector rational pole-fitting, and PRBS-7 eye diagrams | All Platforms | [SciPy Signal Docs](https://docs.scipy.org/doc/scipy/reference/signal.html) |
| **Tier 3 (Circuits)**| **Xyce / Ngspice (Opt)** | Open-source parallel analog circuit simulator for StrongARM regenerative latch transient analysis | Linux, Windows, macOS | [Xyce SPICE Guide](https://xyce.sandia.gov/) |
| **Tier 4 (Digital)** | **Icarus Verilog (`iverilog`)** | IEEE-1364 standard-compliant Verilog HDL compiler & simulation engine (`vvp`) for CRT reconstruction tree | Windows, Linux, macOS | [Icarus Verilog Official](http://iverilog.icarus.com/) |
| **Tier 4 (Digital)** | **Cocotb** | Python-based coroutine cycle-accurate testbench verification environment for Verilog RTL | Windows, Linux, macOS | [Cocotb Documentation](https://docs.cocotb.org/en/stable/) |
| **Tier 5 (Formal)**  | **Z3 Theorem Prover** | Microsoft Research SMT solver for formal mathematical proofs (group isomorphism, non-overflow, bijectivity) | All Platforms | [Z3 SMT Solver GitHub](https://github.com/Z3Prover/z3) |
| **Physical Layout**  | **gdsfactory & gdstk** | Parametric cell generator & OASIS / GDS II stream synthesizer for photonic and CMOS mask sets | All Platforms | [gdsfactory Docs](https://gdsfactory.github.io/gdsfactory/) |
| **Mask Inspection**  | **KLayout (Optional)** | Visual multi-layer GDS II / OASIS CAD viewer and DRC rule checker with companion `.lyp` files | Windows, Linux, macOS | [KLayout Official](https://www.klayout.de/) |
| **Web / Dashboard**  | **Node.js (Optional)** | Syntax validation and tooling for single-page WebGL interactive dashboard | Windows, Linux, macOS | [Node.js Official](https://nodejs.org/) |

---

## 📦 Step-by-Step Installation Guide

### Option 1: Quickstart (Windows Native & Linux / macOS)
*Ideal for Web Dashboard, REST APIs, AI Benchmarks, Z3 Formal Proofs, and Verilog RTL Simulation:*

1. **Install Miniconda:**
   - Download the installer from the [Official Miniconda Page](https://docs.conda.io/en/latest/miniconda.html).
   - Verify installation: `conda --version`

2. **Create and Activate the Virtual Environment:**
   ```bash
   conda create -n janus_env python=3.11 -y
   conda activate janus_env
   ```

3. **Install Icarus Verilog:**
   - **Windows:** Download the installer from [bleyer.org/icarus](https://bleyer.org/icarus/) or install via Chocolatey:
     ```powershell
     choco install icarus-verilog
     ```
     *(Ensure `C:\iverilog\bin` is added to your System `PATH`)*.
   - **Ubuntu / Debian:**
     ```bash
     sudo apt-get update && sudo apt-get install -y iverilog
     ```
   - **macOS (Homebrew):**
     ```bash
     brew install icarus-verilog
     ```

4. **Clone Repository & Install Python Dependencies:**
   ```bash
   git clone https://github.com/horizonseekerik/janus-photonic-hardware.git
   cd janus-photonic-hardware
   pip install -r requirements.txt
   ```

---

### Option 2: Full Multi-Physics Scientific Stack (Linux / WSL 2 Ubuntu)
*Required for live MEEP 3D FDTD Maxwell solvers, MPB eigensolvers, and Elmer 3D FEM:*

1. **Enable WSL 2 (Windows Users):**
   ```powershell
   wsl --install -d Ubuntu
   ```
   Launch the Ubuntu terminal: `wsl -d Ubuntu`.

2. **Install MEEP & MPB Photonic Solvers:**
   - **Method A (Ubuntu Native APT - Recommended):**
     ```bash
     sudo apt-get update
     sudo apt-get install -y meep libmeep-dev python3-meep mpb
     ```
   - **Method B (Conda-Forge):**
     ```bash
     conda create -n janus_meep -c conda-forge pymeep mpb python=3.11 -y
     conda activate janus_meep
     ```

3. **Install Elmer FEM & Gmsh (3D Heat Diffusion):**
   ```bash
   sudo apt-get install -y gmsh
   # On Ubuntu / Debian:
   sudo apt-add-repository -y ppa:elmer-csc-ubuntu/elmer-csc-ppa
   sudo apt-get update
   sudo apt-get install -y elmerfem-csc
   ```
   *(Note: If Elmer binaries are absent, JANUS automatically executes its 1D multi-layer finite-volume BDF ODE heat diffusion solver).*

4. **Install Python Scientific Stack & Verification Engines:**
   ```bash
   sudo apt-get install -y iverilog python3-pip python3-numpy python3-scipy python3-matplotlib
   pip3 install -r requirements.txt
   ```

---

### 🔍 Toolchain Health Check

Verify your installed toolchain with this diagnostic checklist:

```bash
# 1. Check Python & Core Math
python -c "import numpy, scipy, matplotlib, z3; print('Scientific Core: OK, Z3 Version:', z3.__version__)"

# 2. Check Icarus Verilog RTL Compiler
iverilog -V

# 3. Check MEEP FDTD Photonic Solver (Linux/WSL)
python3 -c "import meep as mp; print('MEEP FDTD Version:', mp.__version__)"

# 4. Check Elmer FEM Solver (Optional)
ElmerSolver --version
```

## 💻 Quick Start & Running Tests


### 1. Prerequisites
* Python 3.10+ (Windows, macOS, or Linux / WSL)
* `git`
* Optional for full multi-physics simulation:
  * `meep` and `mpb` (FDTD wave solver, Linux / WSL Ubuntu recommended)
  * `iverilog` (Icarus Verilog for RTL digital verification)
  * `z3-solver` (Formal mathematical proof theorem prover)

### 2. Installation
Clone the official repository:
```bash
git clone https://github.com/horizonseekerik/janus-photonic-hardware.git
cd janus-photonic-hardware
pip install -r requirements.txt
```

### 3. Running the Full 16-Test Multi-Physics Co-Simulation
Execute the 16-point sign-off matrix solver suite:
```bash
python janus_mini16_sim/run_mini16_full_cosim.py
```

### 4. Running Individual Verification Tiers & Benchmarks
Run test suites using `pytest`:
```bash
# Tier 1: FDTD Optics & 16-Tree Fermat Core
pytest janus_mini16_sim/tier1_meep_optics/test_tier1_all.py -v

# Tier 2: 3D Thermal Elmer FEM & 1D Finite-Volume Diffusion
pytest janus_mini16_sim/tier2_elmer_thermal/test_tier2_all.py -v

# Tier 3: Optoelectronic SPICE APD, StrongARM Latches & 100 GHz Eye Diagram
pytest janus_mini16_sim/tier3_xyce_circuit/test_tier3_all.py -v

# Tier 4: Digital Verilog CRT Reconstruction & Cocotb
pytest janus_mini16_sim/tier4_rtl_digital/test_tier4_all.py -v

# Tier 5: Z3 Formal Mathematical Proofs & Exact GEMM Benchmarks
pytest janus_mini16_sim/tier5_python_rns/test_tier5_all.py -v

# First-Principles Power & Area Analytical Validation
pytest janus_mini16_sim/benchmarks/test_first_principles_power_and_area.py -v

# Monolithic Dynamic Co-Simulation Closed-Loop Test
pytest janus_mini16_sim/orchestrator/test_monolithic_cosim.py -v
```

### 5. Synthesizing Physical GDS II Stream Files
Synthesize the tapeout-ready physical mask layout streams for both strata:
```bash
# Synthesize 3D Photonic Top Die GDS II (Si3N4, LiTaO3, Sb2S3 16-Tree, SAC2M APDs, Cu TDVs)
python janus_mini16_sim/layout/generate_mini16_gds.py

# Synthesize 65nm LP/GP CMOS Digital Base Die GDS II (StrongARM, Deserializers, SIMD, Dual-LUT SRAM)
python janus_mini16_sim/layout/generate_cmos_base_gds.py
```
Outputs `janus_mini16_layout.gds` (955 KB) and `janus_mini16_cmos_base_layout.gds` (169 KB) with companion `.lyp` layer styling files viewable directly in **KLayout**.

### 6. Launching the Interactive Local Web Dashboard
To launch the web dashboard locally:
```bash
# Option A: Standard Python WSGI runner
python run_dashboard.py

# Option B: Windows background VBScript
wscript start_dashboard.vbs
```
Then navigate your browser to **`http://127.0.0.1:8080`**.

---

## 📜 Patent & Intellectual Property

The algorithms, spatial residue mapping architectures, circuit topologies, and thermal management mechanisms of Project JANUS are protected under:

* **Patent Application:** Indian Patent Application No. **202611052791** *(Patent Pending)*
* **Title:** *A Spatial Residue Number System Photonic AI Architecture with Non-Volatile Phase-Change Routing and Monolithic 3D Heterogeneous Stacking*
* **Lead Architect & Inventor:** Deepanshu Bhardwaj

---

## 📌 Citation (IEEE & BibTeX Format)

To cite Project JANUS in academic publications:

```bibtex
@article{janus2026photonic,
  title={Project JANUS: Deterministic Spatial Residue Optical Computing Architecture for Peta-Scale Deep Learning Acceleration},
  author={Horizon Seeker IK and Project JANUS Contributors},
  journal={IEEE Transactions on Emerging Topics in Computing (Preprint)},
  year={2026},
  doi={10.5281/zenodo.22733656},
  url={https://janus-photonic-hardware.vercel.app/}
}
```

---

## 📄 License & Legal Notice

Copyright © 2026 Project JANUS / Deepanshu Bhardwaj. All Rights Reserved.  
Project JANUS architectural manuscripts, simulation tools, RTL source codes, and mathematical proofs are published under open-access academic research terms for non-commercial educational and scientific evaluation.
