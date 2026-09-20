# PROJECT JANUS: OFC 2027 3-PAGE PAPER AUTHORING & REVIEWER DEFENSE GUIDE
## Critical Checklist, Material Stack Strategy, Tone Guidelines, and Reviewer Trap Mitigations

**Document ID:** JANUS-OFC-3PAGE-GUIDE-2026-V1  
**Classification:** Authoring Reference & Peer-Review Strategy  
**Target Submission:** Optical Fiber Communication Conference (OFC 2027, Los Angeles, CA)  
**Format:** Strictly 3 Pages (2 Pages Technical Text, Figures & Tables + 1 Page References) in IEEE/Optica Double-Column Style  

---

## 1. Executive Purpose

This guide outlines the non-negotiable technical framing, material stack justifications, reviewer trap mitigations, and formatting rules required to write the 3-page OFC 2027 paper for Project Janus. It translates our architectural accomplishments into a peer-review-bulletproof manuscript designed for maximum acceptance probability (>80%).

---

## 2. Core Material Stack & Heterogeneous Integration Strategy

The paper must strictly distinguish the physical role of each material stratum to eliminate reviewer doubts regarding optical damage and fabrication practicality.

### A. The Bi-Layer Heterogeneous Photonic Stack
1. **Upper Stratum: Stoichiometric Silicon Nitride ($\text{Si}_3\text{N}_4$, Layer 5/0)**
   * **Physical Role:** Multi-watt master laser routing, 4-level balanced H-tree network, and 13-stage cascaded 1:2 MMI power splitter distribution.
   * **Key Physics to Emphasize:**
     * Wide bandgap ($E_g = 5.0\,\text{eV}$): Zero Two-Photon Absorption (TPA) and zero free-carrier absorption at $\lambda = 1064\,\text{nm}$.
     * Laser Power Handling: Safely routes $2.21\,\text{W}$ CW ($+33.44\,\text{dBm}$) input without carrier-induced thermal blooming or nonlinear phase distortion.
     * Ultralow propagation loss: $\alpha = 0.10\,\text{dB/cm}$.
     * Optimized 1:2 MMI: $0.140\,\text{dB}$ excess loss per stage via $7.0\,\mu\text{m}$ adiabatic tapers and $1.25\,\mu\text{m}$ apertures.

2. **Lower Stratum: Thin-Film Lithium Tantalate on Silicon (LTO-on-Si, Layer 3/0)**
   * **Physical Role:** $100\,\text{GHz}$ ballistic electro-optic Pockels routing ($50\,\text{aJ/bit}$) and Ge/Si avalanche photodetection ($105\,\text{GHz}$).
   * **Key Physics to Emphasize:**
     * $\text{LiTaO}_3$ is bonded over **Silicon/$\text{SiO}_2$ substrate**, *not* directly onto $\text{Si}_3\text{N}_4$, leveraging mature commercial wafer-scale dielectric bonding (pioneered by EPFL/commercial foundries).
     * High electro-optic Pockels coefficient: $r_{33} = 30.5\,\text{pm/V}$.
     * Superior photorefractive damage threshold compared to conventional $\text{LiNbO}_3$.
     * Low driving voltage: $V_\pi = 2.80\,\text{V}$, yielding $E_{\text{switch}} = 50\,\text{aJ/bit}$.

3. **Inter-Stratum Optical Coupling**
   * Light transfers from the upper $\text{Si}_3\text{N}_4$ distribution layer into the active $\text{LiTaO}_3$ switching waveguides via **adiabatic 3D vertical inverse tapers** ($< 0.05\,\text{dB}$ loss per transition).

---

## 3. Academic Tone & Writing Guidelines

OFC program committee members instinctively reject papers that read like startup press releases or pitch decks.

### Rules of Engagement:
1. **Zero Hype Words (Banned Vocabulary):**
   * ❌ *Do NOT use:* "revolutionary", "groundbreaking", "unprecedented", "game-changing", "miraculous", "disruptive".
   * ✔️ *Use instead:* "demonstrated", "quantified", "achieves", "verified via full-wave multi-physics co-simulation", "evaluated against standard benchmarks".
2. **Cold, Precise Academic Passive Voice:**
   * ❌ *"We invented an amazing zero-ADC method that destroys GPUs."*
   * ✔️ *"By directly coupling the avalanche photodetector capacitance ($C_{\text{node}} \approx 5\,\text{fF}$) to a regenerative StrongARM latch, analog transimpedance amplifiers and ADCs are eliminated, reducing per-MAC sensing energy to $16.9\,\text{fJ}$."*
3. **Always Ground Performance in Clear Trade-Offs:**
   * Acknowledge trade-offs honestly (e.g., optical power distribution across 16,384 paths requires a $2.21\,\text{W}$ CW source; however, the $1/17$ spatial one-hot sparsity restricts simultaneous active detection power to only $0.16\,\text{W}$).

---

## 4. The 3 Primary Reviewer Traps & Mandatory Defenses

| Reviewer Objection / Trap | What the Reviewer Thinks | The Mandatory Defense to Include in the Paper |
| :--- | :--- | :--- |
| **Trap 1: "Laser Power Damage"**<br>*(2.21 W into a photonic chip will burn the waveguides or cause thermal runaway).* | Reviewer assumes silicon waveguides ($1550\,\text{nm}$) where TPA triggers massive nonlinear absorption at high power. | **State explicitly:** Laser input is delivered entirely through **stoichiometric $\text{Si}_3\text{N}_4$ ($E_g = 5.0\,\text{eV}$)** at $1064\,\text{nm}$. The photon energy ($1.165\,\text{eV}$) is less than one-fourth the bandgap ($h\nu < E_g/4$), making two-photon absorption physically impossible. |
| **Trap 2: "Optical Link Budget Failure"**<br>*(16,384 spatial channels will drop optical power below detector sensitivity).* | Reviewer assumes standard $0.5\,\text{dB}$ splitter loss and $15\,\text{dB}$ routing loss, starving the photodiode. | **Include Table 1 (Optical Link Budget):** Show exact waterfall from $+33.44\,\text{dBm}$ ($2.21\,\text{W}$) through 13 cascaded $0.140\,\text{dB}$ MMI stages to $-16.64\,\text{dBm}$ ($21.68\,\mu\text{W}$) at the APD, proving a closed **$+8.41\,\text{dB}$ optical margin** above the $-25.05\,\text{dBm}$ receiver sensitivity. |
| **Trap 3: "Thermal Drift & Resonance Shift"**<br>*(Laser heating will detune the photonic switches).* | Reviewer assumes resonant microrings which drift by $100\,\text{pm/K}$. | **State explicitly:** Janus uses **non-resonant, broadband Mach-Zehnder / Pockels directional routers** (operating bandwidth $> 40\,\text{nm}$), completely immune to fractional thermal wavelength shifts. 3D FEM confirms max local temperature rise $< 1.18\,\text{K}$. |

---

## 5. Page-by-Page Allocation & Layout Blueprint

### Page 1: Architecture, Physical Principles & Floorplan
* **Title:** Compact, technical, numbers-driven (e.g., *"A 104.8-PetaMAC/s, 16.9-fJ/MAC Receiverless Photonic Residue Number System Processor via Heterogeneous $\text{LiTaO}_3$-on-Si and Low-Loss $\text{Si}_3\text{N}_4$ Distribution"*).
* **Abstract (100–120 words):** Problem (ADC bottleneck, thermal runaway) $\to$ Janus architecture $\to$ Key experimental/simulation metrics ($104.8\,\text{PetaMAC/s}$, $16.9\,\text{fJ/MAC}$, $+8.41\,\text{dB}$ margin).
* **Section I: Introduction & Motivation:** The electrical interconnect wall; failure of resonant and analog photonic computing; introduction of spatial RNS.
* **Figure 1:** Dual-panel hero diagram:
  * *(a)* End-to-end optical compute pipeline (Laser $\to$ H-tree $\to$ 13-stage MMI $\to$ $\text{LiTaO}_3$ router $\to$ Ge/Si APD $\to$ StrongARM latch $\to$ CRT).
  * *(b)* Physical GDS II layout micrograph floorplan showing the 16 tiles, balanced optical tree, and layer breakdown.

### Page 2: Physical Verification, Link Budget & Proof of Concept
* **Section II: Heterogeneous Optical Distribution & 1:2 MMI Optimization:**
  * $\text{Si}_3\text{N}_4$ vs. $\text{LiTaO}_3$-on-Si stratification.
  * 1:2 MMI taper extension ($4.50 \to 7.00\,\mu\text{m}$) reducing excess loss from $0.290 \to 0.140\,\text{dB/stage}$.
  * **Figure 2:** 3D FDTD wave propagation contour through optimized 1:2 MMI taper + $\text{LiTaO}_3$ phase modulation curve ($V_\pi = 2.80\,\text{V}$).
* **Section III: Receiverless Sensing, SPICE Transient & Thermal Verification:**
  * StrongARM regenerative latching dynamics ($t_{\text{regen}} = 1.03\text{–}3.5\,\text{ps}$).
  * 3D package thermal dissipation ($< 1.18\,\text{K}$ rise).
  * **Table 1:** Complete Model 1A Optical Link Budget (Laser $+33.44\,\text{dBm} \to$ Margin $+8.41\,\text{dB}$).
  * **Figure 3:** 100-GHz transient SPICE eye-diagram with BER bath-tub curve.
  * **Figure 4:** 3D FEM thermal dissipation temperature map of the 16-tile die stack.
* **Section IV: Architectural Projections & Efficiency Analysis (No Commercial Comparison Table):**
  * **Humble Tone & Contextual Positioning**: Rather than an aggressive commercial comparison table (e.g. against NVIDIA H100 or Lightmatter Envise, which triggers reviewer skepticism for a simulated design), use a concise, humble 2-sentence analytical projection:
    > *"While commercial digital accelerators operate in the hundreds of femtojoules per operation range (e.g., ~500–800 fJ/op for 4nm FP8 tensor cores) and typical analog coherent photonic meshes are constrained by multi-picojoule ADC conversion penalties, the presented receiverless spatial RNS architecture projects an energy efficiency of 16.9 fJ/MAC at the core level based on multi-physics co-simulation."*
  * **Maximized Figure Space**: Reallocating table space ensures Figures 2, 3, and 4 and Table 1 are displayed at large, crisp, fully readable dimensions without crowding.

### Page 3: Conclusion & References
* **Section V: Conclusion:** 1 concise paragraph summarizing the physical viability of receiverless RNS photonic computing and future tape-out verification.
* **References [1]–[18]:** Clean IEEE format. Must include:
  * Love adiabatic taper criteria (IEEE JQE 1991).
  * Thin-film lithium tantalate/niobate integrated photonics (recent Nature / Optica papers).
  * Stoichiometric $\text{Si}_3\text{N}_4$ nonlinear thresholds at $1064\,\text{nm}$.
  * McIntyre avalanche multiplication noise theory.
  * Open-source Janus repository DOI / URL for reproducibility.

---

## 6. Pre-Submission Authoring Checklist

- [ ] **Word count check**: Main body text $\le 1,100$ words across Pages 1–2 to leave ample room for 4 figures and 2 tables.
- [ ] **No hype adjectives**: Scanned and purged of all marketing terminology.
- [ ] **Figure legibility**: All axis labels, legends, and colorbars readable at 100% zoom on standard print size ($\ge 7\,\text{pt}$ font).
- [ ] **Material distinction clearly stated**: $\text{Si}_3\text{N}_4$ for multi-watt passive distribution; $\text{LiTaO}_3$ on Silicon for active modulation.
- [ ] **Optical link budget closed**: Table 1 proves $+8.41\,\text{dB}$ margin without hand-waving.
- [ ] **Reproducibility statement included**: Pointer to GitHub repository and simulation artifacts.
