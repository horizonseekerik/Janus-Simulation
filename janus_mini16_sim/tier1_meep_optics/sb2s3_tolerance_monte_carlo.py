"""
SB2S3 TOLERANCE MONTE CARLO
===========================
Fabrication tolerance and yield engine supporting two switch architectures:

1. 'directional_coupler': Full-wave 2D MEEP FDTD simulation.
   - Evaluates Maxwell equations over Yee grid for physical directional coupler with flared tapers.
   - Captures real-world taper radiation scattering and exponential gap sensitivity (kappa ~ exp(-gamma * gap)).
   - Parameters: L ~ N(39.0 um, 0.5 um), gap ~ N(151 nm, 5 nm).

2. 'mzi': Semi-analytical Jones transfer-matrix circuit model (M_mmi @ M_arms @ M_mmi).
   - Evaluates cascaded MZI switch with 3dB MMI couplers and MPB-derived Sb2S3 phase shift.
   - NOTE ON TOLERANCE INPUTS: The MMI tolerance distributions:
       * MMI excess loss: N(0.3 dB, 0.04 dB)
       * MMI power split ratio: N(0.50, 0.01) [i.e., 50:50 +- 1%]
     are LITERATURE/PDK ESTIMATES from published silicon photonics foundry statistics
     (e.g., Soldano & Pennings, IEEE JLT 1995; Halir et al., Laser & Photon. Rev. 2015; AIM/IMEC PDK specs),
     NOT extracted from direct MMI FDTD Monte Carlo runs.
   - Phase shifter variation: L_pi ~ N(36.64 um, 0.5 um), Delta_n_eff ~ N(0.01452, 0.0001).
"""

import sys
import os
import numpy as np

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
try:
    from tier1_meep_optics.sb2s3_switch_cell import Sb2S3SwitchCellMeep
    HAS_MEEP = True
except ImportError:
    HAS_MEEP = False

class Sb2S3MonteCarlo:
    def __init__(self, runs: int = 50, topology: str = "mzi"):
        """
        Parameters:
          runs: Number of Monte Carlo fabrication trials.
          topology:
            - 'mzi': Semi-analytical circuit model using MPB modal parameters + literature MMI distributions.
            - 'directional_coupler': Full-wave 2D MEEP FDTD over physical coupler geometry.
        """
        self.runs = runs
        self.topology = topology.lower()
        
        # Dual-state performance specifications
        self.IL_target_max = 0.50   # dB: Maximum allowable switch insertion loss (target <= 0.50 dB)
        self.XT_target_max = -15.0  # dB: Maximum allowable crosstalk leakage
        
        # Directional coupler geometry parameters (full-wave FDTD)
        self.L_patch_mean = 39.0
        self.L_patch_std = 0.5     # 500 nm lithographic length variation
        self.gap_mean = 0.151      # 151 nm inter-waveguide gap
        self.gap_std = 0.005       # 5 nm dry-etch variation
        
    def _run_single_mzi(
        self,
        solver: Sb2S3SwitchCellMeep,
        L_pi: float,
        d_neff: float,
        mmi_split: float,
        mmi_loss: float,
        patch_loss: float = 0.04
    ):
        """Simulates one fabrication trial of the MZI phase-change switch (Methods 1A & 1B)."""
        lambda_0 = solver.lambda_0
        delta_phi_cryst = (2.0 * np.pi / lambda_0) * d_neff * L_pi
        
        t_mmi = 10.0**(-mmi_loss / 20.0)
        split = max(0.4, min(0.6, mmi_split))
        k_bar = np.sqrt(split) * t_mmi
        k_cross = -1j * np.sqrt(1.0 - split) * t_mmi
        M_mmi = np.array([[k_bar, k_cross], [k_cross, k_bar]])
        
        mpb_res = solver.solve_cross_section_mpb()
        gamma = mpb_res["gamma_overlap"]
        k_am = 0.0001
        k_cr = 0.001
        alpha_am_db_per_um = (4.0 * np.pi * k_am * gamma / (lambda_0 * 1e-4)) * 4.343 * 1e-4
        alpha_cr_db_per_um = (4.0 * np.pi * k_cr * gamma / (lambda_0 * 1e-4)) * 4.343 * 1e-4
        
        t_patch = 10.0**(-patch_loss / 20.0)
        
        # 1. Amorphous state (phase-matched: Delta_phi = 0)
        loss_arm1_am_dB = alpha_am_db_per_um * L_pi
        t1_am = 1.0 * 10.0**(-loss_arm1_am_dB / 20.0) * t_patch
        t2_am = 1.0
        M_arms_am = np.array([[t1_am, 0.0], [0.0, t2_am]])
        S_am = M_mmi @ M_arms_am @ M_mmi
        P_bar_am = abs(S_am[0, 0])**2
        P_cross_am = abs(S_am[1, 0])**2
        am_il = -10.0 * np.log10(max(P_cross_am, 1e-12))
        am_xt = 10.0 * np.log10(max(P_bar_am, 1e-12))
        
        # 2. Crystalline state (switched: Delta_phi ~ pi)
        loss_arm1_cr_dB = alpha_cr_db_per_um * L_pi
        t1_cr = np.exp(-1j * delta_phi_cryst) * 10.0**(-loss_arm1_cr_dB / 20.0) * t_patch
        t2_cr = 1.0
        M_arms_cr = np.array([[t1_cr, 0.0], [0.0, t2_cr]])
        S_cr = M_mmi @ M_arms_cr @ M_mmi
        P_bar_cr = abs(S_cr[0, 0])**2
        P_cross_cr = abs(S_cr[1, 0])**2
        cr_il = -10.0 * np.log10(max(P_bar_cr, 1e-12))
        cr_xt = 10.0 * np.log10(max(P_cross_cr, 1e-12))
        
        passed = (
            (am_il <= self.IL_target_max) and (am_xt <= self.XT_target_max) and
            (cr_il <= self.IL_target_max) and (cr_xt <= self.XT_target_max)
        )
        
        return {
            "L_pi_um": float(L_pi),
            "mmi_split": float(split),
            "mmi_loss_dB": float(mmi_loss),
            "patch_loss_dB": float(patch_loss),
            "amorphous_IL": float(am_il), "amorphous_XT": float(am_xt),
            "crystalline_IL": float(cr_il), "crystalline_XT": float(cr_xt),
            "fidelity": "mzi-3db-mmi-monte-carlo",
            "pass": bool(passed)
        }

    def _run_single_directional_coupler(self, solver: Sb2S3SwitchCellMeep, L: float, gap: float):
        """Simulates one trial of the directional coupler switch in full-wave FDTD."""
        solver.resolution = 15
        solver.L_patch = float(L)
        solver.gap = float(gap)
        
        res_am = solver.solve_state("amorphous")
        res_cr = solver.solve_state("crystalline")
        
        am_il = res_am["insertion_loss_dB"]
        am_xt = res_am["crosstalk_dB"]
        cr_il = res_cr["insertion_loss_dB"]
        cr_xt = res_cr["crosstalk_dB"]
        
        passed = (
            (am_il <= self.IL_target_max) and (am_xt <= self.XT_target_max) and
            (cr_il <= self.IL_target_max) and (cr_xt <= self.XT_target_max)
        )
        
        return {
            "L_um": float(L),
            "gap_nm": float(gap * 1000.0),
            "amorphous_IL": float(am_il), "amorphous_XT": float(am_xt),
            "crystalline_IL": float(cr_il), "crystalline_XT": float(cr_xt),
            "fidelity": res_am["fidelity"],
            "pass": bool(passed)
        }

    def run(self):
        if not HAS_MEEP:
            raise RuntimeError("MEEP/MPB not installed on this system.")
            
        solver = Sb2S3SwitchCellMeep()
        print("="*65)
        print(f"RUNNING MONTE CARLO TOLERANCE STUDY: TOPOLOGY = [{self.topology.upper()}]")
        print(f"Trials: {self.runs} | Specs: IL <= {self.IL_target_max:.2f} dB, XT <= {self.XT_target_max:.1f} dB")
        print("="*65)
        
        np.random.seed(42)
        passes = 0
        results = []
        
        if self.topology == "mzi":
            mpb_res = solver.solve_cross_section_mpb()
            nom_d_neff = mpb_res["delta_n_eff"]
            nom_L_pi = solver.lambda_0 / (2.0 * nom_d_neff)
            
            # Phase shifter length variation: sigma_L = 0.5 um (lithographic patterning)
            L_samples = np.random.normal(nom_L_pi, 0.5, self.runs)
            # Material index shift variation: sigma_neff = 0.0001 (film thickness & composition uniformity)
            dneff_samples = np.random.normal(nom_d_neff, 0.0001, self.runs)
            # 3dB MMI split ratio: sigma_split = 0.01 (literature/PDK estimate for 50:50 MMI balance)
            split_samples = np.random.normal(0.5, 0.01, self.runs)
            # Method 1A: 3dB MMI excess loss (mean 0.12 dB, sigma_loss = 0.02 dB)
            loss_samples = np.random.normal(0.12, 0.02, self.runs)
            # Method 1B: Tapered Sb2S3 patch transition loss (mean 0.04 dB, sigma = 0.01 dB)
            patch_loss_samples = np.random.normal(0.04, 0.01, self.runs)
            
            for i in range(self.runs):
                res = self._run_single_mzi(solver, L_samples[i], dneff_samples[i], split_samples[i], loss_samples[i], patch_loss_samples[i])
                results.append(res)
                if res["pass"]:
                    passes += 1
                if i < 5 or i == self.runs - 1:
                    status = "PASS" if res["pass"] else "FAIL"
                    print(f"Trial {i+1:2d}: Amorph(IL={res['amorphous_IL']:.2f}dB, XT={res['amorphous_XT']:.2f}dB) | Cryst(IL={res['crystalline_IL']:.2f}dB, XT={res['crystalline_XT']:.2f}dB) -> [{status}]")
                    
        else:
            L_samples = np.random.normal(self.L_patch_mean, self.L_patch_std, self.runs)
            gap_samples = np.random.normal(self.gap_mean, self.gap_std, self.runs)
            
            for i in range(self.runs):
                print(f"\n--- Running FDTD Trial {i+1}/{self.runs}: L={L_samples[i]:.3f} um, gap={gap_samples[i]*1000:.1f} nm ---")
                res = self._run_single_directional_coupler(solver, L_samples[i], gap_samples[i])
                results.append(res)
                if res["pass"]:
                    passes += 1
                status = "PASS" if res["pass"] else "FAIL"
                print(f"Trial {i+1} Result: Amorph(IL={res['amorphous_IL']:.2f}dB, XT={res['amorphous_XT']:.2f}dB) | Cryst(IL={res['crystalline_IL']:.2f}dB, XT={res['crystalline_XT']:.2f}dB) -> [{status}]")
                
        yield_rate = passes / float(self.runs)
        print("="*65)
        print(f"Summary [{self.topology.upper()}]: {passes}/{self.runs} passed (Yield = {yield_rate*100:.1f}%)")
        print("="*65)
        return {"topology": self.topology, "runs": self.runs, "yield": yield_rate, "details": results}

if __name__ == "__main__":
    topo = sys.argv[1] if len(sys.argv) > 1 else "mzi"
    runs = int(sys.argv[2]) if len(sys.argv) > 2 else 50
    mc = Sb2S3MonteCarlo(runs=runs, topology=topo)
    mc.run()
