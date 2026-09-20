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

        # Physical Edge Case 4: Band-to-Band (BBT) & Trap-Assisted Tunneling in Ge/Si APD
        # Kane's quantum tunneling model at E_field > 5e5 V/cm across 76 nm mesa
        self.E_field_V_per_m = 4.0 / max(self.W_i, 1e-9)  # ~5.26e7 V/m = 5.26e5 V/cm
        self.I_tunnel = self._calculate_bbt_tunneling_current(self.E_field_V_per_m)
        self.I_dark = self.I_surface + (self.I_bulk + self.I_tunnel) * self.M
        self.sigma_latch_noise = sigma_latch_noise_uA * 1e-6
        
        self.q = cfg.q_electron
        self.lambda_0 = cfg.lambda_0
        self.h = cfg.h_planck
        self.c = cfg.c_vacuum
        self.A_apd = getattr(cfg, "A_apd_single", 1.5e-12)

        # Derive responsivity from material absorption (R = eta * q * lambda / (h * c))
        self.R_base = self.eta * self.q * self.lambda_0 / (self.h * self.c)
        # Physical Edge Case 5: Franz-Keldysh Electro-Absorption in APD Mesa
        self.R = self.calculate_franz_keldysh_responsivity(self.E_field_V_per_m)["R_field_perturbed"]
        
        # Derive 3 dB electrical bandwidth from transit time and RC parasitic pole
        self.tau_RC = self.C_j * self.R_s
        self.f_3db = 1.0 / (2.0 * math.pi * math.sqrt(self.tau_transit**2 + self.tau_RC**2))
        self.GBP = self.f_3db * self.M

        # McIntyre Excess Noise Factor: F(M) = k*M + (1-k)*(2 - 1/M)
        self.F = self.k * self.M + (1.0 - self.k) * (2.0 - 1.0 / self.M)

    def _calculate_bbt_tunneling_current(self, E_field_V_per_m: float) -> float:
        """
        Edge Case 4: Kane's Quantum Band-to-Band Tunneling (BBT) current model.
        J_BBT = (sqrt(2*m*) * q^3 * E^2) / (4 * pi^3 * hbar^2 * Eg^(1/2)) * exp(-pi * sqrt(m*) * Eg^(3/2) / (2*sqrt(2) * q * hbar * E))
        """
        # SAC2M architecture: Si multiplication layer supports the high electric field (Wi = 76 nm)
        # Si direct/transverse tunneling effective mass m* = 0.165 m0, bandgap Eg = 1.12 eV
        m_star = 0.165 * 9.109e-31  # Si tunneling effective mass (kg)
        E_g = 1.12 * 1.602e-19     # Si bandgap (J)
        hbar = cfg.h_planck / (2.0 * math.pi)
        q = cfg.q_electron
        E = max(E_field_V_per_m, 1e5)

        prefactor = (math.sqrt(2.0 * m_star) * (q ** 3) * (E ** 2)) / (4.0 * (math.pi ** 3) * (hbar ** 2) * math.sqrt(E_g))
        exponent = -(math.pi * math.sqrt(m_star) * (E_g ** 1.5)) / (2.0 * math.sqrt(2.0) * q * hbar * E)
        J_bbt = prefactor * math.exp(max(exponent, -80.0))  # A/m^2

        A_mesa = math.pi * ((1.0e-6) ** 2)  # 1 um radius mesa area
        I_bbt = J_bbt * A_mesa
        I_tat = 2.3e-9  # Trap-assisted tunneling component (A)
        return float(I_bbt + I_tat)

    def calculate_franz_keldysh_responsivity(self, E_field_V_per_m: float = None) -> Dict[str, float]:
        """
        Edge Case 5: Franz-Keldysh Electro-Absorption in APD Mesa.
        High reverse electric field tilts the band edge, dynamically perturbing responsivity.
        """
        if E_field_V_per_m is None:
            E_field_V_per_m = self.E_field_V_per_m
        E_ref = 5.26e7  # 5.26e5 V/cm
        field_ratio = E_field_V_per_m / E_ref
        delta_R_fraction = 0.018 * (field_ratio ** 1.5)
        R_perturbed = self.R_base * (1.0 + delta_R_fraction)
        return {
            "R_base": float(self.R_base),
            "R_field_perturbed": float(R_perturbed),
            "delta_R_fraction_pct": float(delta_R_fraction * 100.0),
            "E_field_V_per_cm": float(E_field_V_per_m / 100.0),
        }

    def evaluate_space_charge_screening(
        self,
        P_opt_uW: float = 21.42,
        M_nominal: float = 7.0,
        w_mult_nm: float = 76.0,
        v_sat_m_per_s: float = 1.0e5,
    ) -> Dict[str, float]:
        """
        Edge Case 20: Space-Charge Carrier Screening in SAC2M APD Multiplication Layer.
        Mobile photocarriers reduce internal field:
          E_sc = (I_photo * w_mult) / (2 * eps_0 * eps_si * v_sat * A)
          M(P_opt) = M0 / (1 + E_sc / E_applied)
        """
        P_opt_W = P_opt_uW * 1e-6
        I_photo_A = P_opt_W * self.R * M_nominal
        w_mult_m = w_mult_nm * 1e-9
        eps_si = 11.7 * cfg.epsilon_0
        A_m2 = self.A_apd

        E_sc_V_per_m = (I_photo_A * w_mult_m) / (2.0 * eps_si * v_sat_m_per_s * A_m2)
        E_sc_V_per_cm = E_sc_V_per_m / 100.0
        E_applied_V_per_cm = self.E_field_V_per_m / 100.0

        screening_ratio = E_sc_V_per_cm / max(E_applied_V_per_cm, 1.0)
        M_compressed = M_nominal / (1.0 + screening_ratio)
        gain_compression_pct = ((M_nominal - M_compressed) / M_nominal) * 100.0

        return {
            "P_opt_uW": float(P_opt_uW),
            "I_photo_uA": float(I_photo_A * 1e6),
            "E_sc_V_per_cm": float(E_sc_V_per_cm),
            "E_applied_V_per_cm": float(E_applied_V_per_cm),
            "screening_ratio": float(screening_ratio),
            "M_nominal": float(M_nominal),
            "M_compressed": float(M_compressed),
            "gain_compression_pct": float(gain_compression_pct),
            "is_screening_tolerable": bool(gain_compression_pct < 1.5),
        }

    def evaluate_non_local_dead_space(
        self,
        E_th_eV: float = 1.80,
        w_mult_nm: float = 76.0,
    ) -> Dict[str, float]:
        """
        Edge Case 21: Non-Local Avalanche Dead-Space in SAC2M APD.
        d_dead = E_th / (q * E_field)
        Non-Markovian dead-space regularizes ionization, suppressing excess noise F(M).
        """
        E_field_V_per_m = self.E_field_V_per_m
        d_dead_m = (E_th_eV * self.q) / (self.q * E_field_V_per_m)
        d_dead_nm = d_dead_m * 1e9
        dead_space_fraction = d_dead_nm / w_mult_nm

        # Hayat & Saleh non-local excess noise factor correction
        F_nominal = self.F
        F_nonlocal = 1.0 + (F_nominal - 1.0) * (1.0 - 0.7 * dead_space_fraction)

        return {
            "E_th_eV": float(E_th_eV),
            "w_mult_nm": float(w_mult_nm),
            "d_dead_nm": float(d_dead_nm),
            "dead_space_fraction": float(dead_space_fraction),
            "F_nominal": float(F_nominal),
            "F_nonlocal_corrected": float(F_nonlocal),
            "is_dead_space_physical": bool(0.20 <= dead_space_fraction <= 0.60),
        }

    def evaluate_temperature_breakdown_drift(
        self,
        T_operating_C: float = 70.0,
        T_ref_C: float = 25.0,
        gamma_temp_V_per_K: float = 0.08,
        V_bd_ref_V: float = 28.5,
    ) -> Dict[str, float]:
        """
        Edge Case 22: Temperature Drift of APD Breakdown Voltage.
        Delta_V_bd = gamma_temp * (T - T_ref)
        """
        delta_T_K = T_operating_C - T_ref_C
        delta_V_bd = gamma_temp_V_per_K * delta_T_K
        V_bd_operating = V_bd_ref_V + delta_V_bd

        return {
            "T_operating_C": float(T_operating_C),
            "T_ref_C": float(T_ref_C),
            "delta_T_K": float(delta_T_K),
            "delta_V_bd_V": float(delta_V_bd),
            "V_bd_operating_V": float(V_bd_operating),
            "is_drift_trackable": bool(delta_V_bd <= 5.0),
        }

    def calculate_photocurrent(self, P_opt_W: float) -> float:
        assert P_opt_W >= 0, "Optical power cannot be negative"
        return P_opt_W * self.R * self.M

    def calculate_noise_variance(self, P_opt_W: float, bandwidth_Hz: float = None) -> Dict[str, float]:
        if bandwidth_Hz is None:
            bandwidth_Hz = self.f_3db
            
        assert P_opt_W >= 0, "Optical power cannot be negative"
        I_ph = self.calculate_photocurrent(P_opt_W)

        sigma_shot_sq = 2.0 * self.q * (P_opt_W * self.R) * (self.M**2) * self.F * bandwidth_Hz
        sigma_dark_sq = 2.0 * self.q * (self.I_surface + (self.I_bulk + self.I_tunnel) * (self.M**2) * self.F) * bandwidth_Hz

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
