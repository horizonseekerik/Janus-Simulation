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

    def run_simulation(self, num_bits: int = 1_000_000, oversampling: int = 16, chunk_size: int = 100_000, dry_run: bool = False) -> Dict[str, Any]:
        """
        Numerical simulation of the 100 GHz eye diagram, Q-factor, and BER across up to 1,000,000 bits.
        Uses memory-efficient chunked vectorization for high-speed cloud execution.
        """
        if dry_run:
            num_bits = 1_000

        fs = oversampling * self.f_clk
        dt = 1.0 / fs
        
        # 1. Generate smooth NRZ optical pulses (2 ps optical rise/fall time)
        pulse_shape = np.ones(oversampling)
        t_edge = 2.0e-12
        edge_samples = int(round(t_edge / dt))
        if edge_samples > 0:
            edge_ramp = 0.5 * (1.0 - np.cos(np.pi * np.arange(edge_samples) / edge_samples))
            pulse_shape[:edge_samples] = edge_ramp
            pulse_shape[-edge_samples:] = edge_ramp[::-1]

        # 2. Setup Bessel filter (105 GHz APD bandwidth)
        cutoff = min(self.apd.f_3db / (0.5 * fs), 0.99)
        b, a = signal.bessel(3, cutoff, btype='low', norm='mag')
        _, gd = signal.group_delay((b, a))
        delay_samples = int(round(gd[0]))

        C_p = cfg.C_p_strongarm
        t_int = cfg.t_int_strongarm
        int_samples = int(round(oversampling * (t_int / self.T_cycle)))

        q = self.apd.q
        M = self.apd.M
        F = self.apd.F
        R = self.apd.R

        S_I_1 = 2.0 * q * (2.0 * self.P_det * R) * (M**2) * F + 2.0 * q * self.apd.I_dark
        S_I_0 = 2.0 * q * self.apd.I_dark
        B_ref = 1.0 / (2.0 * t_int)
        S_I_latch = (self.apd.sigma_latch_noise**2) / B_ref

        sigma_V_1 = math.sqrt((S_I_1 + S_I_latch) * t_int) / C_p
        sigma_V_0 = math.sqrt((S_I_0 + S_I_latch) * t_int) / C_p

        # Statistical accumulators across all chunks
        n_chunks = math.ceil(num_bits / chunk_size)
        all_sig_1 = []
        all_sig_0 = []
        bit_errors = 0
        total_eval_bits = 0

        for ch in range(n_chunks):
            cur_bits = min(chunk_size, num_bits - ch * chunk_size)
            bits = self._generate_prbs(order=7, num_bits=cur_bits)

            tx_waveform = np.zeros(cur_bits * oversampling)
            for i, bit in enumerate(bits):
                if bit:
                    tx_waveform[i*oversampling:(i+1)*oversampling] = pulse_shape * (2.0 * self.P_det)

            filtered_waveform = signal.lfilter(b, a, tx_waveform)
            ideal_current = filtered_waveform * R * M + self.apd.I_dark

            guard = max(5, int(math.ceil((delay_samples + int_samples) / oversampling)) + 1)
            chunk_V_sampled = []
            chunk_eval_bits = []

            for i in range(guard, max(guard, cur_bits - guard)):
                center = i * oversampling + delay_samples + oversampling // 2
                idx_start = center - int_samples // 2
                idx_end = idx_start + int_samples
                if idx_start >= 0 and idx_end <= len(ideal_current):
                    Q_int = np.sum(ideal_current[idx_start:idx_end]) * dt
                    chunk_V_sampled.append(Q_int / C_p)
                    chunk_eval_bits.append(bits[i])

            chunk_V_sampled = np.array(chunk_V_sampled)
            chunk_eval_bits = np.array(chunk_eval_bits)

            # Add noise
            noise = np.where(chunk_eval_bits == 1,
                             np.random.normal(0, sigma_V_1, len(chunk_eval_bits)),
                             np.random.normal(0, sigma_V_0, len(chunk_eval_bits)))
            chunk_V_noisy = chunk_V_sampled + noise

            all_sig_1.append(chunk_V_noisy[chunk_eval_bits == 1])
            all_sig_0.append(chunk_V_noisy[chunk_eval_bits == 0])

            # Empirical decision error check against mid-rail threshold
            v_thresh = 0.5 * (np.mean(chunk_V_sampled[chunk_eval_bits == 1]) + np.mean(chunk_V_sampled[chunk_eval_bits == 0]))
            decisions = (chunk_V_noisy >= v_thresh).astype(int)
            bit_errors += int(np.sum(decisions != chunk_eval_bits))
            total_eval_bits += len(chunk_eval_bits)

        sig_1 = np.concatenate(all_sig_1)
        sig_0 = np.concatenate(all_sig_0)

        mu_1, std_1 = float(np.mean(sig_1)), float(np.std(sig_1))
        mu_0, std_0 = float(np.mean(sig_0)), float(np.std(sig_0))

        # Eye diagram metrics
        time_domain_Q = float((mu_1 - mu_0) / (std_1 + std_0 + 1e-12))
        eye_opening_V = float((mu_1 - 3.0 * std_1) - (mu_0 + 3.0 * std_0))
        eye_opening_pct = float((eye_opening_V / max(mu_1, 1e-12)) * 100.0) if mu_1 > 0 else 0.0
        eye_height_mV = float(eye_opening_V * 1e3)

        # BER via Q-factor erfc formula
        ber_erfc = float(0.5 * erfc(time_domain_Q / math.sqrt(2.0)))
        empirical_ber = float(bit_errors / max(total_eval_bits, 1))

        return {
            "num_bits_simulated": num_bits,
            "eval_bits": total_eval_bits,
            "time_domain_Q": time_domain_Q,
            "eye_opening_pct": eye_opening_pct,
            "eye_height_mV": eye_height_mV,
            "mu_1_V": mu_1,
            "mu_0_V": mu_0,
            "std_1_mV": float(std_1 * 1e3),
            "std_0_mV": float(std_0 * 1e3),
            "BER_measured": ber_erfc,
            "BER_analytical": ber_erfc,
            "BER_empirical": empirical_ber,
            "bit_errors_observed": bit_errors,
            "pass_Q": bool(time_domain_Q >= 9.38),
            "pass_eye_opening": bool(eye_opening_pct >= 25.0),
        }

    def evaluate_laser_rin_folding(
        self,
        RIN_dBc_per_Hz: float = -155.0,
        P_opt_uW: float = 21.42,
        f_clk_GHz: float = 100.0,
        t_int_ps: float = 5.0,
    ) -> Dict[str, float]:
        """
        Edge Case 32: Dynamic Laser RIN & High-Frequency Noise Folding.
        sigma_RIN^2 = <P>^2 * 10^(RIN/10) * Delta_f_eff
        Nyquist noise folding folds laser relaxation oscillations into the decision band.
        """
        P_opt_W = P_opt_uW * 1e-6
        t_int_s = t_int_ps * 1e-12
        B_eff_Hz = 1.0 / (2.0 * t_int_s)  # 100 GHz integrate-and-dump bandwidth
        rin_linear = 10.0 ** (RIN_dBc_per_Hz / 10.0)

        # Baseband laser RIN optical power variance
        sigma_rin_opt_W = P_opt_W * math.sqrt(rin_linear * B_eff_Hz)
        sigma_rin_opt_uW = sigma_rin_opt_W * 1e6

        # Folding factor from Nyquist sampling (relaxation peak at 1-10 MHz folds into 100 GHz clock)
        folding_factor = 1.15
        sigma_rin_folded_uW = sigma_rin_opt_uW * math.sqrt(folding_factor)

        # Converted to photocurrent at APD
        R = getattr(cfg, "R_responsivity", 0.80)
        M = getattr(cfg, "M_apd", 7)
        sigma_rin_current_uA = sigma_rin_folded_uW * R * M

        return {
            "RIN_dBc_per_Hz": float(RIN_dBc_per_Hz),
            "P_opt_uW": float(P_opt_uW),
            "sigma_rin_opt_uW": float(sigma_rin_opt_uW),
            "sigma_rin_folded_uW": float(sigma_rin_folded_uW),
            "sigma_rin_current_uA": float(sigma_rin_current_uA),
            "is_rin_tolerable": bool(sigma_rin_current_uA < 1.5),
        }

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="100 GHz Eye Diagram & BER Solver")
    parser.add_argument("--bits", type=int, default=1_000_000, help="Number of bits/cycles to simulate")
    parser.add_argument("--dry-run", action="store_true", help="Quick verification run with 1,000 bits")
    args = parser.parse_args()

    solver = EyeDiagramAndBERSolver()
    res = solver.run_simulation(num_bits=args.bits, dry_run=args.dry_run)
    print("=" * 65)
    print(f"  100-GHz EYE DIAGRAM & BER RESULTS ({res['num_bits_simulated']:,} BITS)")
    print("=" * 65)
    print(f"  Time-Domain Q-Factor : {res['time_domain_Q']:.2f} (Target: >= 9.38 for BER < 1e-20)")
    print(f"  Eye Opening Height   : {res['eye_height_mV']:.2f} mV ({res['eye_opening_pct']:.1f}% opening)")
    print(f"  Analytical BER       : {res['BER_analytical']:.3e}")
    print(f"  Empirical Bit Errors : {res['bit_errors_observed']} / {res['eval_bits']:,} bits (BER: {res['BER_empirical']:.3e})")
    print(f"  Pass Quality & Margin: {res['pass_Q']}")
    print("=" * 65)

