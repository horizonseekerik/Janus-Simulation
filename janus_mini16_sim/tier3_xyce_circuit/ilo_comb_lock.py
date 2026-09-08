import sys
import os
import math
import numpy as np
from scipy.integrate import solve_ivp
from typing import Dict, Any

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from configs import mini_16t_constants as cfg

class ILOCombLockModel:
    """Injection-Locked Oscillator (ILO) physical solver."""

    def __init__(self,
                 f_rep_Hz: float = 100.0e9,
                 Q_tank: float = 15.0,
                 I_osc_A: float = 2.0e-3,
                 P_comb_avg_W: float = 100.0e-6):
        self.f_rep = f_rep_Hz
        self.omega_rep = 2.0 * math.pi * self.f_rep
        self.Q_tank = Q_tank
        self.I_osc = I_osc_A
        self.P_comb_avg = P_comb_avg_W
        
        self.R = cfg.R_responsivity
        self.M0 = cfg.M_apd
        
        # Lock range from Adler theory: Delta_omega_lock = omega_inj * (P_inj/P_osc)^0.5
        # Since we use currents: omega_L = (omega_rep / (2 * Q_tank)) * (I_inj / I_osc)
        self.I_inj = self.P_comb_avg * self.R * self.M0
        self.omega_L = (self.omega_rep / (2.0 * self.Q_tank)) * (self.I_inj / self.I_osc)
        self.f_lock_Hz = self.omega_L / (2.0 * math.pi)

    def simulate_phase_locking_transient(self, delta_f0_Hz: float = 150.0e6, t_sim_s: float = 1.0e-9) -> Dict[str, Any]:
        """Solve Adler's eq using solve_ivp and verify dynamic convergence."""
        delta_omega_0 = 2.0 * math.pi * delta_f0_Hz
        
        def adler_ode(t, phi):
            return delta_omega_0 - self.omega_L * np.sin(phi)
            
        sol = solve_ivp(adler_ode, [0, t_sim_s], [0.5], method='RK45', max_step=1e-12)
        
        phi_ss = float(sol.y[0][-1])
        # Verify dynamic settling by evaluating final phase derivative
        dphi_dt_final = abs(delta_omega_0 - self.omega_L * math.sin(phi_ss))
        is_statically_in_range = abs(delta_f0_Hz) < self.f_lock_Hz
        is_locked = bool(is_statically_in_range and dphi_dt_final < 0.1 * self.omega_L)
        
        return {
            "is_locked": is_locked,
            "f_lock_bandwidth_GHz": self.f_lock_Hz / 1e9,
            "phi_ss_rad": phi_ss,
            "delta_f0_MHz": delta_f0_Hz / 1e6,
            "dphi_dt_final": dphi_dt_final,
        }

    def calculate_phase_noise_and_jitter(self, delta_f0_Hz: float = 0.0) -> Dict[str, Any]:
        """Compute proper frequency-dependent phase noise model (Leeson's model)"""
        delta_omega_0 = 2.0 * math.pi * delta_f0_Hz
        sin_phi = np.clip(delta_omega_0 / self.omega_L, -0.99, 0.99)
        cos_phi = math.sqrt(1.0 - sin_phi**2)
        omega_3db = self.omega_L * cos_phi
        
        # High-resolution frequency grid across 6 decades (10 kHz to 10 GHz)
        freqs = np.logspace(4, 10, 5000)
        
        # Leeson's phase noise model for free-running oscillator
        f_corner = 1.0e6
        L_free_10M = 10.0 ** (-105.0 / 10.0)
        floor_free = 10.0 ** (-155.0 / 10.0)
        S_phi_free = 2.0 * (L_free_10M * (10.0e6 / freqs)**2 * (1.0 + f_corner / freqs) + floor_free)
        
        # Comb phase noise
        L_comb_10M = 10.0 ** (-148.0 / 10.0)
        floor_comb = 10.0 ** (-168.0 / 10.0)
        S_phi_comb = 2.0 * (L_comb_10M * (10.0e6 / freqs)**2 + floor_comb)
        
        # Transfer functions
        H_mag2 = (omega_3db**2) / (omega_3db**2 + (2.0 * math.pi * freqs)**2)
        HP_mag2 = ((2.0 * math.pi * freqs)**2) / (omega_3db**2 + (2.0 * math.pi * freqs)**2)
        
        S_phi_out = S_phi_comb * H_mag2 + S_phi_free * HP_mag2
        
        # Integrate using NumPy 2.x compatible trapezoid integration with logarithmic
        # coordinate transform: int S_phi(f) df = int [S_phi(f) * f] d(ln f).
        # This eliminates non-uniform step skew across decades.
        trapz_fn = getattr(np, "trapezoid", getattr(np, "trapz", None))
        if trapz_fn is None:
            from scipy.integrate import trapezoid as trapz_fn
            
        ln_freqs = np.log(freqs)
        sigma_phi_sq = float(trapz_fn(S_phi_out * freqs, ln_freqs))
        sigma_phi_rad = math.sqrt(max(0.0, sigma_phi_sq))
        sigma_t_fs = (sigma_phi_rad / self.omega_rep) * 1e15
        
        return {
            "sigma_t_fs": sigma_t_fs,
            "pass_jitter_budget": sigma_t_fs <= 50.0
        }

if __name__ == "__main__":
    ilo = ILOCombLockModel()
    print(ilo.simulate_phase_locking_transient())
