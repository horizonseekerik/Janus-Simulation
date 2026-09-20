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


def test_edge_cases_4_and_5_apd_receiver():
    """Verify Edge Case 4 (Kane BBT tunneling dark current floor) and Case 5 (Franz-Keldysh responsivity)."""
    apd = APDReceiverAnalytical()
    # Case 4: Kane BBT + TAT tunneling current floor
    assert 2.0e-9 <= apd.I_tunnel <= 15.0e-9
    assert apd.I_dark > apd.I_surface + apd.I_bulk * apd.M

    # Case 5: Franz-Keldysh electro-absorption perturbation
    fk = apd.calculate_franz_keldysh_responsivity(apd.E_field_V_per_m)
    assert fk["R_field_perturbed"] > fk["R_base"]
    assert 0.5 <= fk["delta_R_fraction_pct"] <= 5.0


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


def test_edge_case_20_apd_space_charge_screening():
    """Verify Edge Case 20: Space-Charge Carrier Screening in SAC2M APD."""
    apd = APDReceiverAnalytical()
    screening = apd.evaluate_space_charge_screening(P_opt_uW=21.42, M_nominal=7.0)
    assert screening["is_screening_tolerable"] is True
    assert screening["gain_compression_pct"] < 1.5
    assert screening["E_sc_V_per_cm"] < 5000.0
    assert screening["screening_ratio"] < 0.01


def test_edge_cases_21_and_22_apd_receiver():
    """Verify Edge Cases 21 & 22: Non-Local Dead-Space & Temperature Breakdown Drift."""
    apd = APDReceiverAnalytical()

    # Case 21: Non-local dead-space & history-dependent avalanche
    dead = apd.evaluate_non_local_dead_space(E_th_eV=1.80, w_mult_nm=76.0)
    assert dead["is_dead_space_physical"] is True
    assert 0.0 < dead["d_dead_nm"] < 50.0
    assert 0.20 <= dead["dead_space_fraction"] <= 0.60
    assert dead["F_nonlocal_corrected"] <= dead["F_nominal"]

    # Case 22: Breakdown voltage temperature drift
    drift = apd.evaluate_temperature_breakdown_drift(T_operating_C=70.0, T_ref_C=25.0, gamma_temp_V_per_K=0.08)
    assert drift["is_drift_trackable"] is True
    assert 0.5 < drift["delta_V_bd_V"] < 5.0
    assert drift["V_bd_operating_V"] > 28.5


def test_edge_cases_23_to_25_strongarm_latch():
    """Verify Edge Cases 23, 24 & 25: Metastability Tail, RDF & Capacitive Kickback."""
    latch = StrongArmLatchModel()

    # Case 23: Metastability tail & dynamic sampling jitter
    meta = latch.evaluate_metastability_tail(delta_V_in_mV=5.0, T_cycle_ps=10.0)
    assert meta["is_metastability_safe"] is True
    assert meta["P_meta"] < 1e-15
    assert meta["t_decision_ps"] < 10.0

    # Case 24: Random dopant fluctuation (RDF) & threshold mismatch
    rdf = latch.evaluate_random_dopant_fluctuation(W_nm=1200.0, L_nm=85.0, A_vt_mV_um=3.2)
    assert rdf["is_rdf_compensable"] is True
    assert rdf["sigma_vth_mV"] < 20.0
    assert rdf["three_sigma_mV"] <= 35.0

    # Case 25: Capacitive kickback noise
    kick = latch.evaluate_capacitive_kickback(C_gd_fF=0.80, C_sensing_fF=5.0, V_dd_V=0.80)
    assert kick["is_kickback_tolerable"] is True
    assert kick["delta_V_kick_neutralized_mV"] < 20.0


def test_edge_case_32_laser_rin_folding():
    """Verify Edge Case 32: Dynamic Laser RIN & Noise Folding into StrongARM Latch."""
    eye = EyeDiagramAndBERSolver()
    rin = eye.evaluate_laser_rin_folding(RIN_dBc_per_Hz=-155.0, P_opt_uW=21.42, f_clk_GHz=100.0)
    assert rin["is_rin_tolerable"] is True
    assert rin["sigma_rin_current_uA"] < 1.5


if __name__ == "__main__":
    print("Running Tier 3 Circuit & Signal Integrity unit tests...")
    print("Testing Vector Fit S-Parameters (Algorithm 3A)...")
    test_vector_fit_s_params_alg3a()
    print("  [PASS] Vector Fit S-Parameters")
    print("Testing APD Receiver Physics & McIntyre Noise Model (Algorithm 3B)...")
    test_apd_receiver_model_alg3b()
    print("  [PASS] APD Receiver Model")
    print("Testing Edge Cases 4 & 5 (Kane BBT & Franz-Keldysh)...")
    test_edge_cases_4_and_5_apd_receiver()
    print("  [PASS] Edge Cases 4 & 5")
    print("Testing Edge Case 20 (Space-Charge Carrier Screening)...")
    test_edge_case_20_apd_space_charge_screening()
    print("  [PASS] Edge Case 20: Space-Charge Screening")
    print("Testing Edge Cases 21 & 22 (Non-Local Dead-Space & Temperature Breakdown Drift)...")
    test_edge_cases_21_and_22_apd_receiver()
    print("  [PASS] Edge Cases 21 & 22: Dead-Space & Temperature Breakdown Drift")
    print("Testing StrongARM Latch & Metastability (Algorithm 3C)...")
    test_strongarm_latch_alg3c()
    print("  [PASS] StrongARM Latch Model")
    print("Testing Edge Cases 23 to 25 (Metastability Tail, RDF & Capacitive Kickback)...")
    test_edge_cases_23_to_25_strongarm_latch()
    print("  [PASS] Edge Cases 23 to 25: Metastability Tail, RDF & Capacitive Kickback")
    print("Testing Eye Diagram & BER Solver (Algorithms 3D & 3E)...")
    test_eye_diagram_and_ber_alg3d_3e()
    print("  [PASS] Eye Diagram & BER Solver")
    print("Testing Edge Case 32 (Laser RIN & Noise Folding)...")
    test_edge_case_32_laser_rin_folding()
    print("  [PASS] Edge Case 32: Laser RIN & Noise Folding")
    print("Testing Injection-Locked Oscillator Comb Lock (Algorithm 3F)...")
    test_ilo_comb_lock_alg3f()
    print("  [PASS] ILO Comb Lock Model")
    print("All Tier 3 Circuit unit tests passed successfully!")


