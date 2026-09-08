import sys
import os
import math
import numpy as np
from scipy import signal
from scipy.special import erfc
from typing import Dict, Any

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from configs import mini_16t_constants as cfg
from tier3_xyce_circuit.apd_receiver_model import APDReceiverAnalytical

class EyeDiagramAndBERSolver:
    """100 GHz Eye Diagram and Bit Error Rate Solver based on physical numerical simulation."""

    def __init__(self):
        self.apd = APDReceiverAnalytical()
        self.P_det = cfg.P_det
        self.f_clk = cfg.f_clk
        self.T_cycle = cfg.T_cycle
        self.BER_target = cfg.BER_target

    def _generate_prbs(self, order: int = 7, num_bits: int = 1000) -> np.ndarray:
        """Generate a standard PRBS sequence using LFSR with ITU-T O.150 polynomial."""
        state = (1 << order) - 1
        bits = []
        for _ in range(num_bits):
            bit = state & 1
            bits.append(bit)
            # PRBS-7 polynomial: x^7 + x^6 + 1. For a right-shifting register, taps are bit 0 and bit 1.
            new_bit = (state ^ (state >> 1)) & 1
            state = (state >> 1) | (new_bit << (order - 1))
        return np.array(bits)

    def run_simulation(self, num_bits: int = 1000, oversampling: int = 32) -> Dict[str, Any]:
        """Numerical simulation of the 100 GHz eye diagram, Q-factor, and BER."""
        # 1. Generate PRBS sequence
        bits = self._generate_prbs(order=7, num_bits=num_bits)
        
        fs = oversampling * self.f_clk
        dt = 1.0 / fs
        
        # 2. Generate smooth NRZ optical pulses (2 ps optical rise/fall time)
        pulse_shape = np.ones(oversampling)
        t_edge = 2.0e-12
        edge_samples = int(round(t_edge / dt))
        if edge_samples > 0:
            edge_ramp = 0.5 * (1.0 - np.cos(np.pi * np.arange(edge_samples) / edge_samples))
            pulse_shape[:edge_samples] = edge_ramp
            pulse_shape[-edge_samples:] = edge_ramp[::-1]
            
        tx_waveform = np.zeros(num_bits * oversampling)
        for i, bit in enumerate(bits):
            if bit:
                tx_waveform[i*oversampling:(i+1)*oversampling] = pulse_shape * (2.0 * self.P_det)
                
        # 3. Apply bandwidth limiting via Bessel filter (linear phase, 105 GHz APD bandwidth)
        cutoff = min(self.apd.f_3db / (0.5 * fs), 0.99)
        b, a = signal.bessel(3, cutoff, btype='low', norm='mag')
        _, gd = signal.group_delay((b, a))
        delay_samples = int(round(gd[0]))
        
        filtered_waveform = signal.lfilter(b, a, tx_waveform)
        
        # Photocurrent
        ideal_current = filtered_waveform * self.apd.R * self.apd.M + self.apd.I_dark
        
        # 4. Integrate onto sensing node parasitic capacitance C_p over StrongARM integration window
        C_p = cfg.C_p_strongarm
        t_int = cfg.t_int_strongarm
        int_samples = int(round(oversampling * (t_int / self.T_cycle)))
        
        # Determine guard window dynamically to cover filter transient and delay
        min_guard_samples = delay_samples + int_samples
        guard = max(5, int(math.ceil(min_guard_samples / oversampling)) + 1)
        
        V_sampled = []
        eval_bits = []
        
        for i in range(guard, max(guard, num_bits - guard)):
            center = i * oversampling + delay_samples + oversampling // 2
            idx_start = center - int_samples // 2
            idx_end = idx_start + int_samples
            # Bounds check to guarantee full integration window without silent truncation
            if idx_start >= 0 and idx_end <= len(ideal_current):
                Q_int = np.sum(ideal_current[idx_start:idx_end]) * dt
                V_sampled.append(Q_int / C_p)
                eval_bits.append(bits[i])
            
        V_sampled = np.array(V_sampled)
        eval_bits = np.array(eval_bits)
        
        # 5. Add physical noise (shot noise, dark current, and StrongARM latch thermal noise)
        q = self.apd.q
        M = self.apd.M
        F = self.apd.F
        R = self.apd.R
        
        S_I_1 = 2.0 * q * (2.0 * self.P_det * R) * (M**2) * F + 2.0 * q * self.apd.I_dark
        S_I_0 = 2.0 * q * self.apd.I_dark
        
        # Consistent latch white noise spectral density: S_I_latch = sigma_latch_noise^2 / B_ref
        # Integrate-and-dump charge variance scales physically as sigma_Q^2 = (S_I + S_I_latch) * t_int
        B_ref = 1.0 / (2.0 * t_int)
        S_I_latch = (self.apd.sigma_latch_noise**2) / B_ref
        
        sigma_V_1 = math.sqrt((S_I_1 + S_I_latch) * t_int) / C_p
        sigma_V_0 = math.sqrt((S_I_0 + S_I_latch) * t_int) / C_p
        
        V_noisy = np.copy(V_sampled)
        for idx, b_val in enumerate(eval_bits):
            s_v = sigma_V_1 if b_val == 1 else sigma_V_0
            V_noisy[idx] += np.random.normal(0, s_v)
            
        sig_1 = V_noisy[eval_bits == 1]
        sig_0 = V_noisy[eval_bits == 0]
        
        mu_1, std_1 = np.mean(sig_1), np.std(sig_1)
        mu_0, std_0 = np.mean(sig_0), np.std(sig_0)
        
        # 6. Compute eye diagram metrics
        time_domain_Q = float((mu_1 - mu_0) / (std_1 + std_0 + 1e-12))
        eye_opening = (mu_1 - 3*std_1) - (mu_0 + 3*std_0)
        eye_opening_pct = float((eye_opening / max(mu_1, 1e-12)) * 100.0) if mu_1 > 0 else 0.0
        
        # 7. Compute BER via Q-factor erfc formula
        ber_erfc = float(0.5 * erfc(time_domain_Q / math.sqrt(2.0)))
        
        return {
            "time_domain_Q": time_domain_Q,
            "eye_opening_pct": eye_opening_pct,
            "BER_measured": ber_erfc,
            "pass_Q": bool(time_domain_Q >= 9.38),
            "pass_eye_opening": bool(eye_opening_pct >= 25.0),
        }

if __name__ == "__main__":
    solver = EyeDiagramAndBERSolver()
    res = solver.run_simulation()
    print(res)
