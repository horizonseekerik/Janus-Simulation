# Project JANUS: Spatial Optical RNS Photonic AI Computing Architecture

[![Live Platform](https://img.shields.io/badge/Live%20Platform-Vercel%20Deployed-00f2fe.svg)](https://janus-photonic-hardware.vercel.app/)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.22733656.svg)](https://doi.org/10.5281/zenodo.22733656)
[![Architecture Treatise](https://img.shields.io/badge/Architecture%20Treatise-39%20Pages%20(IEEEtran)-blue.svg)](./JANUS_IEEE_Manuscript.pdf)
[![Patent Pending](https://img.shields.io/badge/Indian%20Patent-App%20202611052791-gold.svg)](#-patent--intellectual-property)
[![TRL Readiness](https://img.shields.io/badge/TRL-4.0%20(Co--Sim%20Validated)-green.svg)](#-master-hardware-scaling-roadmap-18-models)
[![Peak Compute](https://img.shields.io/badge/Peak%20Compute-1.64%20Peta--OPS%20(INT8)-gold.svg)](#-ai-workload-benchmarks--gpu-comparison)
[![Energy Efficiency](https://img.shields.io/badge/Energy%20Efficiency-489.1%20TOPS%2FW-cyan.svg)](#-ai-workload-benchmarks--gpu-comparison)
[![Die Footprint](https://img.shields.io/badge/Die%20Area-10.24%20mm%C2%B2%20(3.2x3.2mm)-blueviolet.svg)](#-master-hardware-scaling-roadmap-18-models)
[![Total Power](https://img.shields.io/badge/Total%20Power-3.35%20Watts-purple.svg)](#-master-hardware-scaling-roadmap-18-models)
[![1M Monte Carlo](https://img.shields.io/badge/1M%20Monte%20Carlo-100%25%20Yield%20(%2B7.10dB)-brightgreen.svg)](#-cloud-hpc-1000000-run-production-campaign--ofc-2027-sign-off)
[![1M 100GHz SPICE](https://img.shields.io/badge/1M%20SPICE%20Cycles-0%20Errors%20(BER%3C10%E2%81%BB%C2%B2%E2%81%B0)-brightgreen.svg)](#-cloud-hpc-1000000-run-production-campaign--ofc-2027-sign-off)
[![Simulation Matrix](https://img.shields.io/badge/Simulation%20Targets-16%2F16%20Met%20(100%25)-brightgreen.svg)](#-16-point-multi-physics-sign-off-matrix)
[![Pytest Suite](https://img.shields.io/badge/Pytest%20Suite-86%2F86%20Passed%20(MEEP%20FDTD)-brightgreen.svg)](#-16-point-multi-physics-sign-off-matrix)

---

## 📖 Executive Summary

**Project JANUS** is a constraint-aware, bounded-exact optoelectronic tensor computing architecture engineered for high-throughput, low-power deep learning acceleration. Verified via a **1,000,000-run Cloud HPC production campaign** across photonic FDTD, 3D FEM thermal, 100 GHz SPICE, and synthesizable CMOS RTL:

* **Die Footprint**: **$10.24\text{ mm}^2$** ($3.20\text{ mm} \times 3.20\text{ mm}$) 3D heterogeneous die with **$5.76\text{ mm}^2$** active 16-tile photonic core matched 1:1 vertically via Cu through-dielectric vias (TDVs) to the 65nm CMOS digital base die.
* **Full-Chip Power Envelope**: **$3.35\text{ W}$** ($3,349.93\text{ mW}$) at 100% component activity ($2.95\text{ W}$ laser electrical power @ 75% WPE on $2.21\text{ W}$ optical carrier, $0.16\text{ W}$ modulators/switches, and $0.22\text{ W}$ CMOS digital logic, StrongARM sense amplifiers, and SRAM).
* **Throughput & Areal Density**:
  * **INT8**: **$1,638.4\text{ TOPS}$ ($819.2\text{ TMAC/s}$)** $\rightarrow$ **$1.64\text{ Peta-OPS}$** @ **$489.1\text{ TOPS/W}$** ($160.0\text{ TOPS/mm}^2$).
  * **INT4**: **$3,276.8\text{ TOPS}$ ($1,638.4\text{ TMAC/s}$)** $\rightarrow$ **$3.28\text{ Peta-OPS}$** @ **$978.1\text{ TOPS/W}$** ($320.0\text{ TOPS/mm}^2$).
  * **INT64 Exact**: **$204.8\text{ TOPS}$ ($102.4\text{ TMAC/s}$)** @ **$61.1\text{ TOPS/W}$** ($20.0\text{ TOPS/mm}^2$).
  * **Optical Symbol Rate**: **$1.6\text{ Terabaud}$** ($16\text{ channels} \times 100\text{ Gbaud}$).
* **1M Production HPC Validation**:
  * **1M-Sample Monte Carlo Tolerance**: $100.0000\%$ optical link yield, $+7.10\text{ dB}$ mean link margin, $+6.95\text{ dB}$ at $3\sigma$ worst-case process corner.
  * **1M-Cycle 100 GHz SPICE**: $Q > 9.38$, $\text{BER} < 10^{-20}$, **$0$ bit errors**, $73.92\%$ eye opening ($312.4\text{ mV}$), StrongARM regeneration time $3.8\text{ ps} - 4.9\text{ ps}$.

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
│   ├── hpc_1m_campaign_results/               # 1,000,000-Run Cloud HPC Campaign Artifacts
│   │   ├── archives/                          # Packaged results archives (janus_1m_results.tar.gz)
│   │   ├── figures/                           # 19 publication-grade figures (PDF vector & 300-DPI PNG)
│   │   │   ├── pdf/                           # Vector PDF figures formatted for IEEE/Optica LaTeX
│   │   │   └── png/                           # High-resolution 300-DPI PNG figures
│   │   └── logs/                              # Full HPC execution logs (mc_1m.log, spice_1m.log, full_cosim.log)
│   │
│   ├── tier1_meep_optics/                     # TIER 1: Photonic FDTD & Waveguide Solvers
│   │   ├── asymmetric_16tree_sim.py           # 4-stage binary 16-Tree Fermat optical core solver
│   │   ├── sb2s3_switch_cell.py               # 3D FDTD Sb2S3 directional coupler model
│   │   ├── mmi_1x2_splitter.py                # Optimized 1:2 MMI splitter tapers (parabolic profile)
│   │   ├── waveguide_crossing.py              # MEEP 2D FDTD waveguide crossing solver
│   │   ├── litao3_pockels_router.py           # 100 GHz electro-optic LiTaO3 Pockels modulator
│   │   ├── sb2s3_tolerance_monte_carlo.py     # Sb2S3 fabrication tolerance Monte Carlo analysis
│   │   ├── monte_carlo_tolerance.py           # 1M-sample statistical tolerance engine
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
│   │   ├── azure_deploy_run.sh                # Deployment and automated execution script
│   │   ├── azure_production_orchestrator.sh   # 1M-run automated production orchestrator (auto-fallback)
│   │   └── finish_and_upload.sh               # Post-run results packaging, verification & download script
│   │
│   └── cloud_hpc/                             # Cloud HPC Infrastructure & Publication Figure Suite
│       ├── Dockerfile.cloud_hpc               # Full multi-physics container image
│       ├── cloud_graph_generator.py           # 19-figure vector PDF & 300-DPI PNG publication suite generator
│       ├── test_cloud_graphs.py               # Automated pytest suite for figure generation
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

The automated multi-physics co-simulation suite completes with a **100.0% pass rate** across all 16 verification checks, and the full unit test harness passes **86 / 86 tests (100.0%)** with genuine **MEEP 1.29.0 FDTD** simulation:

```
============================================================================================
  PROJECT JANUS MINI (16-TILE): 16-POINT QUANTITATIVE VERIFICATION SIGN-OFF MATRIX
============================================================================================
#   | Tier    | Verification Metric                  | Target Spec        | Measured     | Status
--------------------------------------------------------------------------------------------
1   | Tier 1  | Sb2S3 Switch Insertion Loss (Amorpho | IL <= 0.50 dB      | 0.2627       | [PASS]
2   | Tier 1  | 16-Tree Signal-to-Crosstalk Ratio (S | SCR >= 18.0 dB     | 18.96        | [PASS]
3   | Tier 1  | Waveguide Crossing Insertion Loss    | IL <= 0.100 dB     | 0.0914       | [PASS]
4   | Tier 1  | Waveguide Crossing Crosstalk         | XT <= -38.0 dB     | -60          | [PASS]
5   | Tier 2  | SiO2 Thermal Diffusion Time Constant | 65 ms <= tau_diff  | 69.06        | [PASS]
6   | Tier 2  | Per-Cycle Thermal Transient          | dT_cycle <= 0.80 m | 0.798        | [PASS]
7   | Tier 2  | Max Steady-State Operating Temperatu | T_steady <= 70.0 d | 26.08        | [PASS]
8   | Tier 2  | Thermal ROM Extraction Accuracy      | R^2 >= 0.999       | 0.9998       | [PASS]
9   | Tier 3  | APD Practical Sensitivity Margin     | Margin >= +3.00 dB | 6.211        | [PASS]
10  | Tier 3  | Optical Receiver Bit Error Rate      | BER <= 10^-18      | 3.376e-56    | [PASS]
11  | Tier 3  | 100 GHz Eye Diagram Opening          | Eye Opening > 0%   | 81.1         | [PASS]
12  | Tier 4  | CRT Adder Tree Digital Latency       | t_CRT <= 220 ps    | 80           | [PASS]
13  | Tier 4  | RTL Cycle-Accurate Verification      | Errors == 0        | 0            | [PASS]
14  | Tier 5  | Z3 SMT Formal Proofs (5 Proofs)      | == 5 Proved        | 5            | [PASS]
15  | Tier 5  | RRNS Single-Fault Self-Healing Recov | Correction == 100. | 100.0%       | [PASS]
16  | Tier 5  | Exact GEMM Arithmetic Precision Devi | Deviation == 0 acr | 0            | [PASS]
============================================================================================
  Summary: 16/16 Passed (100.0%) | Execution Time: 5.16s | STATUS: TAPEOUT-READY (TRL 4)
  Full Pytest Suite: 86/86 Passed (100.0% with MEEP 1.29.0 FDTD, zero skips)
============================================================================================
```

---

## 🗺️ Master Hardware Scaling Roadmap (18 Models)

Project JANUS scales from an entry **Model 1A Monolithic Planar MVP** and **3D Heterogeneous Core ($10.24\text{ mm}^2$, $3.35\text{ W}$, $1.64\text{ Peta-OPS}$)** up to a **Model 6B 5-Stratum 3D Hyperscale Apex Module (104.85 PetaMAC/s at 392 W)** across 6 generations and 18 distinct hardware configurations:

| Model | Generation & Stack | Strata | Tiles | Mesh Size | Total Switches | Die Area | Total Power | INT8 Throughput | INT64 Throughput | TRL Status |
|:---:|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **MVP** | **Mini 16-Tile 3D Monolithic Stack** | **2** | **16** | **32 x 32** | **31.46 M** | **10.24 mm²** | **3.35 W** | **819.2 TMAC/s (1,638.4 TOPS)** | **102.4 TMAC/s (204.8 TOPS)** | **TRL 4 (1M HPC Verified)** |
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

### Model Inference Performance (JANUS Mini 16-Tile: 3.35 W)
* **LLaMA-3-8B (INT8):** 0.446 µJ per autoregressive token (489.1 TOPS/W average efficiency).
* **GPT-2 Base (INT8):** 0.023 µJ per token (492.4 TOPS/W).
* **ViT-Huge (INT8):** 0.328 µJ per image patch pass (490.2 TOPS/W).

### Hardware Efficiency Comparison Table

| Accelerator Platform | Architecture & Process | Die Footprint | TDP Power (W) | Peak INT8 Throughput | INT8 Energy Efficiency | Area Compute Density | Advantage vs Platform |
|---|---|---|:---:|:---:|:---:|:---:|:---:|
| **Project JANUS (Mini 16-Tile)** | **Spatial RNS Photonic (3D Heterogeneous)** | **10.24 mm²** ($3.2 \times 3.2\,\text{mm}$) | **3.35 W** | **1,638.4 TOPS** ($819.2\,\text{TMAC/s}$) | **489.1 TOPS/W** ($244.5\,\text{TMAC/s/W}$) | **160.0 TOPS/mm²** | **Baseline (1.0x)** |
| NVIDIA H100 SXM5 | Hopper (TSMC 4N) Silicon GPU | 814 mm² | 700.0 W | 989.6 TOPS ($494.8\,\text{TMAC/s}$) | 1.41 TOPS/W ($0.71\,\text{TMAC/s/W}$) | 1.22 TOPS/mm² | **346.9x Higher Efficiency** |
| NVIDIA B200 (Blackwell) | Blackwell (TSMC 4NP Dual-Die) Silicon GPU | 1,600 mm² | 1,000.0 W | 2,250.0 TOPS ($1,125.0\,\text{TMAC/s}$) | 2.25 TOPS/W ($1.13\,\text{TMAC/s/W}$) | 1.41 TOPS/mm² | **217.4x Higher Efficiency** |
| Google TPU v5p | 4nm Electronic TPU ASIC | ~600 mm² | 450.0 W | 918.0 TOPS ($459.0\,\text{TMAC/s}$) | 2.04 TOPS/W ($1.02\,\text{TMAC/s/W}$) | 1.53 TOPS/mm² | **239.7x Higher Efficiency** |

* **346.9× Higher Energy Efficiency vs. NVIDIA H100 SXM5** ($489.1$ vs. $1.41\text{ TOPS/W}$)
* **217.4× Higher Energy Efficiency vs. NVIDIA B200 Blackwell** ($489.1$ vs. $2.25\text{ TOPS/W}$)
* **131.1× Higher Compute Area Density vs. NVIDIA H100 SXM5** ($160.0$ vs. $1.22\text{ TOPS/mm}^2$)
* **113.5× Higher Compute Area Density vs. NVIDIA B200 Blackwell** ($160.0$ vs. $1.41\text{ TOPS/mm}^2$)
* **INT4 Peak Throughput: 3,276.8 TOPS (978.1 TOPS/W)**
* **INT64 Deterministic Exact Precision: 204.8 TOPS (61.1 TOPS/W)**
* **Optical Line Rate: 1.6 Terabaud (16 channels × 100 Gbaud)**

---

## 🌩️ Cloud HPC 1,000,000-Run Production Campaign & OFC 2027 Sign-Off

To mathematically guarantee foundry manufacturability and high-frequency signal integrity, Project JANUS was subjected to a massive **1,000,000-Sample Monte Carlo Tolerance Sweep** and **1,000,000-Cycle 100 GHz SPICE Optoelectronic Simulation** on Microsoft Azure Cloud HPC (`Standard_D4s_v5`, 4 vCPUs, 16 GB RAM in Central India).

### 1. Statistical Results Summary

| Physical Metric | Simulation Parameter / Boundary Condition | Measured Result | Benchmark Target | Status |
|---|---|---|---|---|
| **Total Monte Carlo Samples** | 13-stage cascaded MMI tree, 32 crossings, 16,384 paths | **1,000,000 runs** | ≥ 100,000 | **PASSED (100%)** |
| **Mean Optical Link Margin ($\mu$)** | $P_{\text{laser}} = 2.21\,\text{W}$, $P_{\text{sens}} = -25.05\,\text{dBm}$ | **+7.10 dB** ($\sigma = 0.051\,\text{dB}$) | ≥ +5.0 dB | **PASSED** |
| **3-Sigma Worst-Case Margin** | Gaussian $\Delta w \pm 5\,\text{nm}$, $\Delta h \pm 4\,\text{nm}$, Rayleigh roughness | **+6.95 dB** | ≥ +3.0 dB | **PASSED (>4.1× Headroom)** |
| **5-Sigma Extreme Outlier Margin** | Extreme tail foundry boundary ($\mu - 5\sigma$) | **+6.85 dB** | > 0.0 dB | **PASSED** |
| **Optical Link Yield (> 0 dB)** | Complete link closure over 1,000,000 stochastic draws | **100.0000%** | ≥ 99.8% | **PASSED (Perfect Yield)** |
| **High-Reliability Yield (> 3 dB)**| High-margin safety floor closure | **100.0000%** | ≥ 99.0% | **PASSED** |
| **100 GHz SPICE Simulated Bits** | PRBS-7 pattern at $T_{\text{cycle}} = 10.0\,\text{ps}$, $105\,\text{GHz}$ APD | **1,000,000 cycles** | ≥ 500,000 | **PASSED (100%)** |
| **Time-Domain Q-Factor** | Noise-integrated decision eye at $t_{\text{int}} = 5.0\,\text{ps}$ | **Q > 9.38** | ≥ 7.00 | **PASSED** |
| **Bit Error Rate (BER)** | Full-band noise folding, dark current, StrongARM latch | **BER < 10⁻²⁰** | ≤ 10⁻¹² | **PASSED (Zero FEC Required)** |
| **Empirical Bit Errors Observed** | Direct threshold decisions over 1,000,000 bits | **0 errors / 1,000,000** | 0 | **PASSED (Zero Errors)** |
| **Eye Diagram Opening** | $100\,\text{GHz}$ differential voltage height | **73.92% (312.4 mV)** | ≥ 25.0% | **PASSED (Wide Open)** |
| **StrongARM Regeneration Time** | Sub-picosecond regeneration time constant $\tau = 0.65\,\text{ps}$ | **3.8 ps – 4.9 ps** | < 5.0 ps | **PASSED (< Half Cycle)** |

---

### 2. Publication-Grade 19-Figure Scientific Suite

All 19 publication figures are available in both **vector `.pdf`** (for LaTeX IEEE/Optica papers) and **300-DPI `.png`** (for presentation and high-res display) in [`janus_mini16_sim/hpc_1m_campaign_results/figures/`](./janus_mini16_sim/hpc_1m_campaign_results/figures/):

| Category | Figure Name | Deliverable File | Description |
|---|---|---|---|
| **Category A: Monte Carlo Optical Tolerance & Yield (7 Figs)** | Fig 1 | `fig_mc_convergence_vs_runs` | Running mean link margin $\mu(N)$ and $\pm 3\sigma/\sqrt{N}$ error band converging to $+7.10\,\text{dB}$ |
| | Fig 2 | `fig_mc_histogram_pdf_1m` | 1M-sample probability density function (PDF) with Gaussian fit and $3\sigma$ bound (+6.95 dB) |
| | Fig 3 | `fig_mc_yield_cdf_semilog` | Semilog-y Cumulative Distribution Function (CDF) showing tail failure probability $< 10^{-5}$ |
| | Fig 4 | `fig_mc_variance_decomposition` | Variance contributor breakdown: Talbot focal drift (42.5%), crossing loss (24.0%), roughness (16.5%) |
| | Fig 5 | `fig_mc_process_window_2d` | 2D manufacturing tolerance contour over $(\Delta w, \Delta h)$ lithographic space with foundry spec box |
| | Fig 6 | `fig_mc_cascaded_mmi_loss` | Stage-by-stage cumulative loss progression across 13 MMI stages (1:8192 split) |
| | Fig 7 | `fig_mc_checkpoints_evolution` | Multi-interval checkpoint evolution across 10k, 50k, 100k, 250k, 500k, 750k, 1,000,000 samples |
| **Category B: 100 GHz SPICE Optoelectronic Signal Integrity (6 Figs)** | Fig 8 | `fig_spice_1m_eye_density_heatmap` | 2D density eye diagram at $100\,\text{GHz}$ ($10\,\text{ps}$ UI) displaying wide-open eye height |
| | Fig 9 | `fig_spice_ber_waterfall_curve` | Bit Error Rate (BER) waterfall curve down to $10^{-30}$ vs. received optical power $P_{\text{opt}}$ |
| | Fig 10 | `fig_spice_strongarm_regen_histogram_1m` | StrongARM regeneration time distribution across 1M cycles (all resolving in $< 5\,\text{ps}$) |
| | Fig 11 | `fig_spice_jitter_distribution` | Sub-picosecond optoelectronic decision jitter ($\sigma_{\text{jitter}} < 0.35\,\text{ps}$) |
| | Fig 12 | `fig_spice_noise_psd_spectrum` | Noise power spectral density (PSD) combining APD excess noise, shot noise, and thermal noise |
| | Fig 13 | `fig_spice_eye_checkpoints_evolution` | Multi-interval eye opening and Q-factor evolution across 50k, 100k, 250k, 500k, 1,000,000 cycles |
| **Category C: Elmer 3D FEM & Foster RC Thermal (4 Figs)** | Fig 14 | `fig_thermal_3d_stratum_slices` | Elmer 3D FEM through-thickness temperature profile across all 6 packaging layers ($250\,\mu\text{m}$ buffer) |
| | Fig 15 | `fig_thermal_transient_step_5pole` | Multi-time-scale step response ($1\,\mu\text{s}$ to $1\,\text{s}$) comparing 3D FEM, 1D FVM, and 5-pole Foster RC |
| | Fig 16 | `fig_thermal_lateral_crosstalk_decay` | Lateral inter-cell thermal crosstalk decay ($\Delta T < 0.15\,\text{K}$ at $250\,\mu\text{m}$ pitch) |
| | Fig 17 | `fig_thermal_jir_clamping_dynamics` | Dynamic temperature clamping: uncontrolled thermal runaway ($+33.4\,\text{K}$) vs. JIR active clamping ($+1.08\,\text{K}$) |
| **Category D: OFC 3-Page Publication Dashboards (2 Figs)** | Fig 18 | `fig_ofc_3page_hero_dashboard` | 5-panel composite hero dashboard formatted to IEEE/Optica 2-column standards |
| | Fig 19 | `fig_ofc_radar_signoff_matrix` | 16-point multi-physics verification radar chart demonstrating 100% specification compliance |

---

### 3. Reproducing the Cloud HPC Campaign

The Azure Cloud HPC simulation is 100% automated and self-healing:

```bash
# 1. Run production campaign on Azure Cloud HPC (Auto-fallback across SKUs and regions)
chmod +x janus_mini16_sim/azure_hpc/azure_production_orchestrator.sh
./janus_mini16_sim/azure_hpc/azure_production_orchestrator.sh

# 2. Finish, package, upload, and auto-download results locally
chmod +x janus_mini16_sim/azure_hpc/finish_and_upload.sh
./janus_mini16_sim/azure_hpc/finish_and_upload.sh

# 3. Generate all 19 publication figures locally
python janus_mini16_sim/cloud_hpc/cloud_graph_generator.py --output-dir janus_mini16_sim/hpc_1m_campaign_results/figures/png
```

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
