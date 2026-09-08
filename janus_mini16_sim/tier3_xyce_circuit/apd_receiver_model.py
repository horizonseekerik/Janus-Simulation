import sys
import os
import math
from typing import Dict, Any

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from configs import mini_16t_constants as cfg

class APDReceiverAnalytical:
    """SAC2M Ge/Si Avalanche Photodetector (APD) Physical Equivalent Circuit."""

    def __init__(self,
                 eta: float = 0.932, # Quantum efficiency yielding R = 0.80 A/W at 1064 nm
                 M_gain: int = cfg.M_apd,
                 k_ion: float = cfg.k_ionization,
                 tau_transit_s: float = getattr(cfg, "t_pd_clearance", 1.52e-12), # Thin SAC2M clearance time
                 v_sat: float = 5e4, # Carrier saturation velocity (m/s)
                 C_j_fF: float = cfg.C_j_apd * 1e15,
                 R_s_ohm: float = cfg.R_s_apd,
                 I_surface_nA: float = cfg.I_surface_leakage * 1e9,
                 I_bulk_nA: float = cfg.I_bulk_dark * 1e9,
                 sigma_latch_noise_uA: float = cfg.sigma_latch_noise * 1e6):
        
        self.eta = eta
        self.M = M_gain
        self.k = k_ion
        self.tau_transit = tau_transit_s
        self.v_sat = v_sat
        self.W_i = self.v_sat * self.tau_transit  # Thin high-field SAC2M depletion width (~76 nm)
        self.C_j = C_j_fF * 1e-15
        self.R_s = R_s_ohm
        self.I_surface = I_surface_nA * 1e-9
        self.I_bulk = I_bulk_nA * 1e-9
        self.I_dark = self.I_surface + self.I_bulk * self.M
        self.sigma_latch_noise = sigma_latch_noise_uA * 1e-6
        
        self.q = cfg.q_electron
        self.lambda_0 = cfg.lambda_0
        self.h = cfg.h_planck
        self.c = cfg.c_vacuum

        # Derive responsivity from material absorption (R = eta * q * lambda / (h * c))
        self.R = self.eta * self.q * self.lambda_0 / (self.h * self.c)
        
        # Derive 3 dB electrical bandwidth from transit time and RC parasitic pole
        self.tau_RC = self.C_j * self.R_s
        self.f_3db = 1.0 / (2.0 * math.pi * math.sqrt(self.tau_transit**2 + self.tau_RC**2))
        self.GBP = self.f_3db * self.M

        # McIntyre Excess Noise Factor: F(M) = k*M + (1-k)*(2 - 1/M)
        self.F = self.k * self.M + (1.0 - self.k) * (2.0 - 1.0 / self.M)

    def calculate_photocurrent(self, P_opt_W: float) -> float:
        assert P_opt_W >= 0, "Optical power cannot be negative"
        return P_opt_W * self.R * self.M

    def calculate_noise_variance(self, P_opt_W: float, bandwidth_Hz: float = None) -> Dict[str, float]:
        if bandwidth_Hz is None:
            bandwidth_Hz = self.f_3db
            
        assert P_opt_W >= 0, "Optical power cannot be negative"
        I_ph = self.calculate_photocurrent(P_opt_W)

        sigma_shot_sq = 2.0 * self.q * (P_opt_W * self.R) * (self.M**2) * self.F * bandwidth_Hz
        sigma_dark_sq = 2.0 * self.q * (self.I_surface + self.I_bulk * (self.M**2) * self.F) * bandwidth_Hz

        # Input-referred latch noise spectral density: S_I_latch = sigma_latch_noise^2 / B_ref
        # where B_ref = 1 / (2 * t_int) is the integrate-and-dump reference bandwidth
        t_int = getattr(cfg, "t_int_strongarm", 5.0e-12)
        B_ref = 1.0 / (2.0 * t_int)
        S_I_latch = (self.sigma_latch_noise**2) / B_ref
        sigma_latch_sq = S_I_latch * bandwidth_Hz
        sigma_total_sq = sigma_shot_sq + sigma_dark_sq + sigma_latch_sq
        sigma_total = math.sqrt(sigma_total_sq)

        return {
            "I_photo_uA": I_ph * 1e6,
            "sigma_shot_uA": math.sqrt(sigma_shot_sq) * 1e6,
            "sigma_dark_uA": math.sqrt(sigma_dark_sq) * 1e6,
            "sigma_total_uA": sigma_total * 1e6,
            "sigma_total_A": sigma_total,
        }

    def calculate_sensitivity(self, SNR_target: float = 6.0, bandwidth_Hz: float = None) -> float:
        """Computes optical sensitivity given a target SNR"""
        if bandwidth_Hz is None:
            bandwidth_Hz = self.f_3db
            
        # P = SNR * sigma_total / (R * M) (simplified linear approximation for sensitivity)
        # Using a simple iterative solver to find P where I_ph / sigma_total = SNR
        P_lo = 1e-12
        P_hi = 1e-3
        for _ in range(50):
            P_mid = (P_lo + P_hi) / 2
            I_ph = self.calculate_photocurrent(P_mid)
            noise = self.calculate_noise_variance(P_mid, bandwidth_Hz)
            if I_ph / noise["sigma_total_A"] > SNR_target:
                P_hi = P_mid
            else:
                P_lo = P_mid
        return P_hi

    def generate_spice_netlist(self) -> str:
        """Generates REAL SPICE netlist subcircuit for the SAC2M APD."""
        return f"""* SAC2M Ge/Si APD Subcircuit Model
.SUBCKT SAC2M_APD OPT_IN CATHODE ANODE
* Responsivity R={self.R:.3f} A/W, Gain M={self.M}, F={self.F:.2f}
* Photodiode current source dependent on optical input power
G_PHOTO CATHODE_INT ANODE VALUE = {{ V(OPT_IN) * {self.R * self.M} }}
* Junction capacitance
C_JUNCTION CATHODE_INT ANODE {self.C_j}
* Series resistance
R_SERIES CATHODE_INT CATHODE {self.R_s}
* Dark current source
I_DARK CATHODE_INT ANODE {self.I_dark}
* Note: Add external noise sources during transient/AC analysis as needed.
.ENDS SAC2M_APD
"""

if __name__ == "__main__":
    apd = APDReceiverAnalytical()
    print(f"R: {apd.R}, BW: {apd.f_3db/1e9} GHz")
