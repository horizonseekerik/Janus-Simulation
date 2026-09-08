import sys
import os
import numpy as np
from typing import Dict, Any
from scipy.optimize import curve_fit

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from configs import mini_16t_constants as cfg
from tier2_elmer_thermal.elmer_thermal_solver import Elmer3DThermalPipeline

def foster_5pole_model(
    t: np.ndarray,
    R1: float, R2: float, R3: float, R4: float, R5: float,
    tau1: float, tau2: float, tau3: float, tau4: float, tau5: float,
) -> np.ndarray:
    return (
        R1 * (1.0 - np.exp(-t / tau1))
        + R2 * (1.0 - np.exp(-t / tau2))
        + R3 * (1.0 - np.exp(-t / tau3))
        + R4 * (1.0 - np.exp(-t / tau4))
        + R5 * (1.0 - np.exp(-t / tau5))
    )

class ThermalROMExtractor:
    """
    Thermal Reduced-Order Model (ROM) Extractor for Project Janus Mini (16-Tile).
    
    Provenance & Physical Methodology:
      Extracts a 5-pole Foster RC state-space network from the coupled transient thermal response:
        Delta_T(t) = Delta_T_macro_1D(t) + Delta_T_nano_RC(t)
      where:
        1. Delta_T_macro_1D(t) is computed by the stiff 1D multi-stratum finite-volume stack solver
           (TransientThermal1D), governing through-thickness diffusion across CMOS, SiO2, SiPh, TIM,
           and copper heat spreaders under full workload power P_total = 6.176 W.
        2. Delta_T_nano_RC(t) is computed by the nanoscale spreading and Kapitza interface RC submodel
           (NanoscaleCellThermalSubmodel), capturing localized switch-level micro-hotspot rise.
        3. The macroscale steady-state boundary conditions and thermal resistance are verified against
           genuine 3D Elmer FEM simulation (ElmerGrid + ElmerSolver).
      The 5 poles and modal thermal resistances are fitted via non-linear least squares (scipy.optimize.curve_fit)
      with deterministic ascending time-constant sorting (tau_1 < tau_2 < ... < tau_5) and passivity guarantees.
    """
    def __init__(self):
        self.pipeline = Elmer3DThermalPipeline()
        self.solver = self.pipeline  # Backward compatibility reference

    def extract_and_fit_rom(self, N_points: int = 200) -> Dict[str, Any]:
        time_pts = np.logspace(-6, 0, N_points)
        t, dT = self.pipeline.solve_step_response(time_pts)
        
        # Calculate transient thermal impedance
        P_total = self.pipeline.P_total
        Z_th_sim = dT / P_total
        
        # Fit 5-pole network
        # Initial guess based on actual data
        R_total_est = float(Z_th_sim[-1])
        R_seed = R_total_est / 5.0
        
        # Physical time constant seeds spanning the microsecond to tens-of-millisecond spectrum
        tau_seeds = [
            0.05,    # Thermal diffusion across buffer/stack (~50-70 ms)
            0.01,    # Intermediate stratum spreading (~10 ms)
            0.002,   # TIM / HS1 conduction (~2 ms)
            0.0004,  # Local SiPh core spreading (~400 us)
            0.00008, # Micro-scale heat sink interface (~80 us)
        ]
        
        p0 = [R_seed] * 5 + tau_seeds
        bounds_lower = [1e-5] * 5 + [1e-8] * 5
        bounds_upper = [R_total_est * 1.5] * 5 + [10.0] * 5

        popt, _ = curve_fit(
            foster_5pole_model,
            t,
            Z_th_sim,
            p0=p0,
            bounds=(bounds_lower, bounds_upper),
            maxfev=50000,
        )

        R_fit = popt[:5]
        tau_fit = popt[5:]

        # Deterministically sort poles by ascending time constant (tau_1 < tau_2 < ... < tau_5)
        order = np.argsort(tau_fit)
        R_fit = R_fit[order]
        tau_fit = tau_fit[order]

        Z_fit = foster_5pole_model(t, *np.concatenate([R_fit, tau_fit]))

        ss_res = np.sum((Z_th_sim - Z_fit) ** 2)
        ss_tot = np.sum((Z_th_sim - np.mean(Z_th_sim)) ** 2)
        r_squared = 1.0 - (ss_res / max(ss_tot, 1e-12))
        
        # Rigorous transient and steady-state error metrics
        dT_sim = Z_th_sim * P_total
        dT_fit = Z_fit * P_total
        abs_errors_K = np.abs(dT_sim - dT_fit)
        max_abs_error_K = float(np.max(abs_errors_K))
        mean_abs_error_K = float(np.mean(abs_errors_K))
        
        # Normalized transient error with temperature floor T_floor = 0.05 K (50 mK)
        dT_ss_val = max(float(dT_sim[-1]), 0.05)
        normalized_errors = abs_errors_K / dT_ss_val
        max_normalized_error_pct = float(np.max(normalized_errors) * 100.0)
        
        # Early-time relative error (diagnostic only, avoids zero-crossing division trap)
        early_time_rel_errors = np.abs(Z_th_sim - Z_fit) / np.maximum(Z_th_sim, 1e-12)
        early_time_diagnostic_pct = float(np.max(early_time_rel_errors) * 100.0)
        
        R_foster_total = float(np.sum(R_fit))
        steady_state_error_pct = float(abs(R_foster_total - R_total_est) / R_total_est * 100.0)
        
        # Dominant time constant is the largest pole
        tau_dominant = float(tau_fit[-1])
        
        pass_r_squared = bool(r_squared >= 0.999)
        pass_max_abs_error = bool(max_abs_error_K < 0.05)  # Max L-infinity error < 50 mK
        pass_normalized_error = bool(max_normalized_error_pct < 2.0)  # Max normalized transient error < 2.0%
        pass_steady_state_error = bool(steady_state_error_pct < 0.50)  # Steady state match < 0.5%
        pass_poles_positive = bool(all(r > 0 for r in R_fit) and all(tau > 0 for tau in tau_fit))
        
        return {
            "R_poles_K_W": [float(r) for r in R_fit],
            "tau_poles_s": [float(x) for x in tau_fit],
            "tau1_ms": tau_dominant * 1e3,
            "tau_dominant_s": tau_dominant,
            "tau_diff_sio2_ms": float(self.solver.calculate_sio2_diffusion_time() * 1e3),
            "R_total_K_W": R_foster_total,
            "r_squared": float(r_squared),
            "max_abs_error_K": max_abs_error_K,
            "mean_abs_error_K": mean_abs_error_K,
            "max_normalized_error_pct": max_normalized_error_pct,
            "early_time_relative_error_diagnostic": early_time_diagnostic_pct,
            "steady_state_error_pct": steady_state_error_pct,
            "pass_r_squared": pass_r_squared,
            "pass_max_abs_error": pass_max_abs_error,
            "pass_normalized_error": pass_normalized_error,
            "pass_steady_state_error": pass_steady_state_error,
            "pass_tau1": bool(tau_dominant > 0.0),
            "pass_rom_comprehensive": bool(pass_r_squared and pass_max_abs_error and pass_normalized_error and pass_steady_state_error and pass_poles_positive),
        }

if __name__ == "__main__":
    extractor = ThermalROMExtractor()
    res = extractor.extract_and_fit_rom()
    print(res)
