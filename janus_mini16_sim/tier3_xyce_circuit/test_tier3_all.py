import os
import sys
import numpy as np

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from configs import mini_16t_constants as cfg
from tier3_xyce_circuit.vector_fit_s_params import VectorFitSParams
from tier3_xyce_circuit.apd_receiver_model import APDReceiverAnalytical
from tier3_xyce_circuit.strongarm_latch import StrongArmLatchModel
from tier3_xyce_circuit.eye_diagram_ber import EyeDiagramAndBERSolver
from tier3_xyce_circuit.ilo_comb_lock import ILOCombLockModel


def test_vector_fit_s_params_alg3a():
    S_mat = np.eye(4, dtype=np.complex128) * 0.9
    vfit = VectorFitSParams(num_poles=4)
    res = vfit.fit_s_matrix(S_mat)

    assert res["is_stable"] is True
    assert res["max_passivity"] <= 1.0001
    assert res["pass_criteria"] is True

    # Verify true passivity enforcement on non-passive active matrix
    S_active = np.eye(4, dtype=np.complex128) * 1.8
    res_active = vfit.fit_s_matrix(S_active)
    assert res_active["max_passivity"] <= 1.0001
    assert res_active["pass_criteria"] is True

    # Check SPICE subcircuit generation
    cir_text = vfit.generate_spice_subcircuit(res)
    assert ".SUBCKT OPTICAL_SWITCH_4PORT" in cir_text
    assert "G_D_" in cir_text
    assert "R_STATE_" in cir_text
    assert "C_STATE_" in cir_text
    assert "G_COUPLE_" in cir_text
    assert "G_RES_" in cir_text
    assert ".ENDS OPTICAL_SWITCH_4PORT" in cir_text

    # Check state-space time-domain response synthesis
    time_res = vfit.synthesize_time_domain_response(res)
    assert time_res["is_bounded"] is True
    assert len(time_res["time_ps"]) == 500


def test_apd_receiver_model_alg3b():
    apd = APDReceiverAnalytical()
    assert apd.f_3db >= 50e9  # Physically reasonable ranges
    assert 0.5 <= apd.R <= 1.0

    noise = apd.calculate_noise_variance(cfg.P_det)
    assert noise["I_photo_uA"] > 0.0
    assert noise["sigma_total_uA"] > 0.0


def test_strongarm_latch_alg3c():
    np.random.seed(42)
    latch = StrongArmLatchModel()
    res = latch.simulate_decision(I_diff_A=50e-6, noise_sigma_A=cfg.sigma_latch_noise)

    assert res["t_regen_ps"] <= cfg.T_cycle * 1e12
    assert res["t_regen_ps"] == res["t_regen_ode_ps"]
    assert res["t_regen_ode_ps"] > 0.0
    assert res["decision"] in [0, 1]
    assert res["pass_regen_time"] is True


def test_eye_diagram_and_ber_alg3d_3e():
    np.random.seed(42)
    solver = EyeDiagramAndBERSolver()

    # Verify PRBS-7 periodicity and bit balance
    bits = list(solver._generate_prbs(order=7, num_bits=300))
    assert bits[:127] == bits[127:254], "PRBS-7 sequence must repeat with period 127"
    assert sum(bits[:127]) in [63, 64], "PRBS-7 sequence must be balanced"

    res = solver.run_simulation(num_bits=500, oversampling=16)

    assert res["eye_opening_pct"] >= 25.0
    assert res["pass_eye_opening"] is True
    assert res["pass_Q"] is True
    assert res["time_domain_Q"] >= 9.38
    assert res["BER_measured"] <= 1e-18


def test_ilo_comb_lock_alg3f():
    ilo = ILOCombLockModel()
    trans_res = ilo.simulate_phase_locking_transient(delta_f0_Hz=150e6)
    jitter_res = ilo.calculate_phase_noise_and_jitter()

    assert trans_res["is_locked"] is True
    assert trans_res["f_lock_bandwidth_GHz"] > 0
    assert jitter_res["pass_jitter_budget"] is True


if __name__ == "__main__":
    print("Running Tier 3 Circuit & Signal Integrity unit tests...")
    print("Testing Vector Fit S-Parameters (Algorithm 3A)...")
    test_vector_fit_s_params_alg3a()
    print("  [PASS] Vector Fit S-Parameters")
    print("Testing APD Receiver Physics & McIntyre Noise Model (Algorithm 3B)...")
    test_apd_receiver_model_alg3b()
    print("  [PASS] APD Receiver Model")
    print("Testing StrongARM Latch & Metastability (Algorithm 3C)...")
    test_strongarm_latch_alg3c()
    print("  [PASS] StrongARM Latch Model")
    print("Testing Eye Diagram & BER Solver (Algorithms 3D & 3E)...")
    test_eye_diagram_and_ber_alg3d_3e()
    print("  [PASS] Eye Diagram & BER Solver")
    print("Testing Injection-Locked Oscillator Comb Lock (Algorithm 3F)...")
    test_ilo_comb_lock_alg3f()
    print("  [PASS] ILO Comb Lock Model")
    print("All Tier 3 Circuit unit tests passed successfully!")

