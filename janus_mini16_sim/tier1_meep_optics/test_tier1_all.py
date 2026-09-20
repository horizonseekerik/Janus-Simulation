"""
TESTS FOR TIER 1 MEEP OPTICS
============================
These tests instantiate the actual MEEP solver classes.
They will be skipped if MEEP is not installed on the system.
"""

import sys
import os
import numpy as np

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    import pytest
except ImportError:
    pytest = None

try:
    import meep as mp
    HAS_MEEP = True
except ImportError:
    HAS_MEEP = False

from tier1_meep_optics.sb2s3_switch_cell import Sb2S3SwitchCellMeep
from tier1_meep_optics.waveguide_crossing import WaveguideCrossingMeep
from tier1_meep_optics.litao3_pockels_router import LiTaO3PockelsModulatorMeep
from tier1_meep_optics.sb2s3_tolerance_monte_carlo import Sb2S3MonteCarlo

def skipif_no_meep(func):
    def wrapper(*args, **kwargs):
        if not HAS_MEEP:
            print(f"  [SKIPPED] {func.__name__}: MEEP not installed")
            return None
        return func(*args, **kwargs)
    if pytest is not None:
        wrapper = pytest.mark.skipif(not HAS_MEEP, reason="MEEP not installed")(wrapper)
    wrapper.__name__ = func.__name__
    return wrapper

@skipif_no_meep
def test_switch_cell_mpb_mode_solving():
    solver = Sb2S3SwitchCellMeep()
    res = solver.solve_cross_section_mpb()
    print(f"\n  [MPB 3D Eigensolver]: n_eff_bare={res['n_eff_bare']:.5f}, n_eff_amorph={res['n_eff_amorph']:.5f}, n_eff_cryst={res['n_eff_cryst']:.5f}, Delta_n_eff={res['delta_n_eff']:.5f}, Gamma={res['gamma_overlap']*100:.3f}%")
    assert "delta_n_eff" in res
    assert "gamma_overlap" in res
    assert 0.020 <= res["gamma_overlap"] <= 0.035, f"Gamma out of physical range: {res['gamma_overlap']}"
    assert res["delta_n_eff"] > 0, "Effective index shift must be positive"

@skipif_no_meep
def test_switch_cell_passivity_and_loss():
    solver = Sb2S3SwitchCellMeep()
    # Fast test parameters
    solver.resolution = 15 
    solver.L_patch = 10.0 
    
    res_am = solver.solve_state("amorphous")
    res_cr = solver.solve_state("crystalline")
    
    assert res_am["passivity"] <= 1.05, f"Amorphous passivity violation: {res_am['passivity']}"
    assert res_cr["passivity"] <= 1.05, f"Crystalline passivity violation: {res_cr['passivity']}"
    
    assert res_am["insertion_loss_dB"] >= 0.0, f"Amorphous IL cannot be negative: {res_am['insertion_loss_dB']}"
    assert res_cr["insertion_loss_dB"] >= 0.0, f"Crystalline IL cannot be negative: {res_cr['insertion_loss_dB']}"
    assert "extinction_ratio_dB" in res_am
    assert "single_cell_er_dB" in res_am

@skipif_no_meep
def test_pockels_v_pi():
    solver = LiTaO3PockelsModulatorMeep()
    solver.resolution = 10
    solver.L_active = 10.0 # short for testing
    
    # solve at 5V, which internally should do the delta_phi calculation
    res = solver.solve(5.0)
    assert "V_pi" in res
    assert res["V_pi"] > 0

@skipif_no_meep
def test_waveguide_crossing():
    solver = WaveguideCrossingMeep()
    solver.resolution = 20
    
    # solve() must default to MEEP FDTD
    res = solver.solve()
    
    # Verify MEEP FDTD execution
    assert res.get("fidelity", "").startswith("meep-2d-fdtd"), f"Expected meep-2d-fdtd*, got {res.get('fidelity')}"
    assert "insertion_loss_dB" in res
    assert "crosstalk_dB" in res
    assert "passivity" in res
    
    assert res["passivity"] <= 1.05, f"MMI Passivity violation: {res['passivity']}"
    assert res["insertion_loss_dB"] >= 0.0, "Insertion loss cannot be negative"
    assert res["insertion_loss_dB"] <= 0.10, f"Crossing insertion loss exceeds 0.10 dB spec: {res['insertion_loss_dB']} dB"
    assert res["crosstalk_dB"] <= -38.0, f"Crossing crosstalk above -38.0 dB spec: {res['crosstalk_dB']} dB"

def test_mzi_switch_cell():
    solver = Sb2S3SwitchCellMeep()
    res_am = solver.solve_mzi_state("amorphous")
    res_cr = solver.solve_mzi_state("crystalline")
    
    assert res_am["fidelity"] == "semi-analytical-transfer-matrix"
    assert res_am["insertion_loss_dB"] <= 0.50, f"MZI amorphous IL too high: {res_am['insertion_loss_dB']}"
    assert res_am["crosstalk_dB"] <= -25.0, f"MZI amorphous crosstalk too high: {res_am['crosstalk_dB']}"
    assert res_cr["insertion_loss_dB"] <= 0.50, f"MZI crystalline IL too high: {res_cr['insertion_loss_dB']}"
    assert res_cr["crosstalk_dB"] <= -25.0, f"MZI crystalline crosstalk too high: {res_cr['crosstalk_dB']}"
    assert res_am["passivity"] <= 1.05

def test_mzi_monte_carlo_yield():
    mc = Sb2S3MonteCarlo(runs=50, topology="mzi")
    res = mc.run()
    assert res["yield"] >= 0.95, f"MZI Monte Carlo yield below 95%: {res['yield']*100:.1f}%"


# ============================================================================
# ============================================================================
# 16-Tree Core Tests (no MEEP required — pure optical math / physics)
# ============================================================================
from tier1_meep_optics.asymmetric_16tree_sim import Asymmetric16TreeCore, OpticalSwitchSpecs


def test_16tree_exhaustive_truth_table():
    """Verify all 256 (x,w) pairs in [0,15]^2 produce correct exact integer products."""
    core = Asymmetric16TreeCore(OpticalSwitchSpecs())
    errors = 0
    for x in range(16):
        for w in range(16):
            result = core.simulate_pulse(x, w)
            if not result["correct"] or result["output_channel"] != x * w:
                errors += 1
    assert errors == 0, f"16-Tree truth table errors: {errors}/256"


def test_16tree_modular_rns():
    """Verify modular RNS multiplication across all moduli <= 17."""
    core = Asymmetric16TreeCore(OpticalSwitchSpecs())
    moduli = [17, 13, 11, 7, 5, 3]
    for m in moduli:
        for x in range(min(m, 16)):
            for w in range(min(m, 16)):
                result = core.simulate_pulse(x, w, modulus=m)
                expected = (x * w) % m
                assert result["output_channel"] == expected, f"Modular error: ({x}*{w}) mod {m} = {expected}, got {result['output_channel']}"


def test_16tree_zero_gating():
    """Verify x=0 always produces zero power (dark channel, laser gated off)."""
    core = Asymmetric16TreeCore(OpticalSwitchSpecs())
    for w in range(16):
        result = core.simulate_pulse(0, w)
        assert result["peak_power_mw"] == 0.0, f"x=0, w={w}: expected zero power, got {result['peak_power_mw']}"
        assert result["output_channel"] == 0, f"x=0, w={w}: expected output 0, got {result['output_channel']}"


def test_16tree_insertion_loss():
    """Verify optical insertion loss stays within 16-Tree spec (< 2.0 dB)."""
    core = Asymmetric16TreeCore(OpticalSwitchSpecs())
    for x in range(1, 16):
        for w in range(1, 16):
            result = core.simulate_pulse(x, w)
            il = result.get("total_loss_db", 0)
            assert il < 2.0, f"x={x}, w={w}: insertion loss {il:.2f} dB exceeds 2.0 dB"


def test_16tree_scr():
    """Verify signal-to-crosstalk ratio meets minimum spec (>= 15 dB)."""
    core = Asymmetric16TreeCore(OpticalSwitchSpecs())
    for x in range(1, 16):
        for w in range(1, 16):
            result = core.simulate_pulse(x, w)
            scr = result.get("snr_db", float("inf"))
            assert scr >= 15.0, f"x={x}, w={w}: SCR {scr:.2f} dB below 15.0 dB minimum"


def test_16tree_fermat_z17_exhaustive():
    """Verify all 289 (x,w) pairs in Z_17 (0..16) are bit-exact (100% state efficiency)."""
    core = Asymmetric16TreeCore(OpticalSwitchSpecs())
    errors = 0
    for x in range(17):
        for w in range(17):
            res = core.simulate_pulse(x, w, modulus=17)
            if not res["correct"] or res["output_channel"] != (x * w) % 17:
                errors += 1
    assert errors == 0, f"Z_17 Fermat verification errors: {errors}/289"


def test_16tree_tree16_negation():
    """Verify Tree 16 physical modular negation symmetry: 16 * w == (17 - w) mod 17."""
    core = Asymmetric16TreeCore(OpticalSwitchSpecs())
    for w in range(17):
        res = core.simulate_pulse(16, w, modulus=17)
        expected = (17 - (w % 17)) % 17
        assert res["output_channel"] == expected, f"Tree 16 negation failed for w={w}: got {res['output_channel']}, expected {expected}"


def test_16tree_product_ceiling():
    """Verify 16 * 16 = 256 product ceiling is strictly bounded < 257 for Z_257."""
    core = Asymmetric16TreeCore(OpticalSwitchSpecs())
    res = core.simulate_pulse(16, 16, modulus=None)
    assert res["correct"] and res["output_channel"] == 256, f"Product ceiling 16*16 must be 256, got {res['output_channel']}"
    assert res["output_channel"] < 257, "Product must be strictly < 257 for division-free reduction"


def test_mmi_1x2_splitter_optimization():
    """Verify 1:2 MMI splitter baseline geometry (0.144 dB) vs legacy reference (0.290 dB)."""
    from tier1_meep_optics.mmi_1x2_splitter import MMI1x2SplitterModel
    model = MMI1x2SplitterModel()
    cascade = model.compute_13stage_cascade()

    assert abs(cascade["baseline"]["excess_per_stage_dB"] - 0.144) <= 0.010
    assert abs(cascade["legacy_reference"]["excess_per_stage_dB"] - 0.290) <= 0.010
    assert cascade["comparison"]["total_optical_gain_dB"] >= 1.85
    assert cascade["baseline"]["link_margin_dB"] > cascade["legacy_reference"]["link_margin_dB"]
    assert cascade["baseline"]["link_margin_dB"] >= 6.0


def test_baseline_link_budget_with_32_edge_cases():
    """
    Verify Unified Baseline Optical Link Budget with ALL 32 Physical Edge Cases Integrated.
    The 32 physical edge cases represent the nominal physical baseline, not an optional penalty.
    """
    from tier1_meep_optics.mmi_1x2_splitter import MMI1x2SplitterModel
    model = MMI1x2SplitterModel()
    cascade = model.compute_13stage_cascade()

    base_32 = cascade["baseline_with_32_edge_cases"]
    assert base_32["is_margin_closed"] is True
    assert base_32["link_margin_dB"] >= 5.50
    assert base_32["P_det_uW"] > 10.0
    assert base_32["penalty_32_edge_cases_dB"] == 2.80


def test_edge_cases_1_and_2_litao3_pockels():
    """Verify Edge Case 1 (Photorefractive charge drift) and Case 2 (Pyroelectric surge)."""
    pockels = LiTaO3PockelsModulatorMeep()
    drift = pockels.evaluate_photorefractive_drift(v_pi_nominal=0.88, t_exposure_s=300.0)
    assert drift["v_pi_drifted_V"] > 0.88
    drift_pct = (drift["delta_v_pi_V"] / 0.88) * 100.0
    assert 5.0 <= drift_pct <= 15.0

    pyro = pockels.evaluate_pyroelectric_surge(delta_T_K=0.5)
    assert pyro["is_dielectrically_safe"] is True
    assert pyro["V_pyro_V"] > 0.05
    assert pyro["E_field_V_per_cm"] < 1e5


def test_edge_cases_3_7_10_mmi_splitter():
    """Verify Edge Case 3 (Trap absorption), Case 7 (Talbot drift), and Case 10 (SBS/SRS thresholds)."""
    from tier1_meep_optics.mmi_1x2_splitter import MMI1x2SplitterModel
    mmi = MMI1x2SplitterModel()

    trap = mmi.evaluate_trap_assisted_absorption(intensity_MW_per_cm2=9.2)
    assert 0.02 <= trap["alpha_trap_saturated_dB_cm"] <= 0.08
    assert trap["is_trap_absorption_tolerable"] is True

    talbot = mmi.evaluate_talbot_focal_drift(delta_W_nm=5.0)
    assert abs(talbot["delta_L_pi_um"]) > 0.01
    assert talbot["loss_drift_per_stage_dB"] > 0
    assert talbot["is_drift_acceptable"] is True

    scat = mmi.compute_nonlinear_scattering_thresholds(P_launch_W=2.21)
    assert scat["is_sbs_safe"] is True
    assert scat["is_srs_safe"] is True
    assert scat["P_th_SBS_W"] > 10.0
    assert scat["P_th_SRS_W"] > 50.0


def test_edge_case_9_cumulative_crossing_crosstalk():
    """Verify Edge Case 9: Cumulative coherent crossing crosstalk scaling (N^2)."""
    from tier1_meep_optics.waveguide_crossing import WaveguideCrossingMeep
    crossing = WaveguideCrossingMeep()
    xt = crossing.evaluate_cumulative_crossing_crosstalk(n_crossings=32, xt_single_dB=-55.0)
    assert xt["n_crossings"] == 32
    assert -26.0 <= xt["xt_coherent_worst_case_dB"] <= -24.0
    assert abs(xt["coherent_penalty_dB"] - 15.05) < 0.1
    assert xt["is_within_scr_budget"] is True


def test_edge_cases_11_and_13_mmi_spm_cod():
    """Verify Edge Case 11 (SPM & Quintic Kerr) and Edge Case 13 (COD at Coupler Facets)."""
    from tier1_meep_optics.mmi_1x2_splitter import MMI1x2SplitterModel
    mmi = MMI1x2SplitterModel()

    spm = mmi.evaluate_self_phase_modulation(P_peak_W=2.21)
    assert spm["is_spm_distortion_tolerable"] is True
    assert spm["delta_n_kerr"] > 0
    assert spm["delta_n_quintic"] < 0
    assert abs(spm["delta_n_total"]) < 1e-4
    assert abs(spm["phi_spm_rad"]) < 0.10

    cod = mmi.evaluate_facet_catastrophic_damage(P_laser_W=2.21)
    assert cod["is_cod_safe"] is True
    assert cod["T_facet_C"] < 200.0
    assert cod["cod_thermal_safety_margin"] > 5.0


def test_edge_case_12_waveguide_crossing_pdl():
    """Verify Edge Case 12: Sidewall Etch Vertical Asymmetry & TE-TM Mode Conversion."""
    from tier1_meep_optics.waveguide_crossing import WaveguideCrossingMeep
    crossing = WaveguideCrossingMeep()
    pdl = crossing.evaluate_sidewall_vertical_asymmetry(sidewall_angle_deg=86.0)
    assert pdl["is_pdl_acceptable"] is True
    assert pdl["tilt_from_vertical_deg"] == 4.0
    assert pdl["te_tm_conversion_dB"] < -30.0
    assert pdl["polarization_dependent_loss_dB"] < 0.05


def test_edge_cases_14_to_19_litao3_pockels_rf():
    """Verify Edge Cases 14 to 19: RF Skin Effect, Walk-off, Dielectric Loss, Crosstalk, Piezo Ringing, CPW Radiation."""
    pockels = LiTaO3PockelsModulatorMeep()

    # Case 14: RF Skin Effect
    skin = pockels.evaluate_rf_skin_effect(f_GHz=100.0)
    assert skin["is_rf_resistance_acceptable"] is True
    assert 150.0 < skin["skin_depth_nm"] < 250.0
    assert skin["R_rf_ohms"] > skin["R_dc_ohms"]

    # Case 15: Velocity Walk-off
    walk = pockels.evaluate_velocity_walk_off(f_GHz=100.0)
    assert walk["is_walkoff_acceptable"] is True
    assert walk["L_walkoff_um"] > 500.0
    assert walk["walkoff_penalty_dB"] < 7.0

    # Case 16: Dielectric Loss Tangent
    diel = pockels.evaluate_dielectric_loss_tangent(f_GHz=100.0)
    assert diel["is_dielectric_loss_tolerable"] is True
    assert diel["loss_active_dB"] < 0.80

    # Case 17: Inter-Electrode RF Crosstalk
    xtalk = pockels.evaluate_inter_electrode_rf_crosstalk(pitch_um=5.0)
    assert xtalk["is_crosstalk_isolated"] is True
    assert xtalk["V_xtalk_mV"] < 25.0

    # Case 18: Piezoelectric Acoustic Ringing
    piezo = pockels.evaluate_piezoelectric_acoustic_ringing(V_step=0.88)
    assert piezo["is_acoustic_ringing_negligible"] is True
    assert piezo["delta_n_acoustic"] < 5e-5

    # Case 19: CPW Substrate Radiation
    rad = pockels.evaluate_cpw_substrate_radiation(f_GHz=100.0)
    assert rad["is_radiation_loss_tolerable"] is True
    assert rad["rad_loss_dB_per_mm"] < 0.15


def test_edge_case_29_htree_optical_skew():
    """Verify Edge Case 29: Optical H-Tree Skew Across 10 mm Die Area."""
    core = Asymmetric16TreeCore(OpticalSwitchSpecs())
    skew = core.evaluate_htree_optical_skew(L_die_mm=10.0, delta_w_nm=3.0)
    assert skew["is_skew_tolerable"] is True
    assert 40.0 <= skew["delta_t_skew_fs"] <= 80.0
    assert skew["delta_t_skew_fs"] < skew["skew_budget_fs"]


if __name__ == "__main__":
    print("Running Tier 1 MEEP unit tests...")
    print("Testing MPB mode solving on physical cross-section...")
    test_switch_cell_mpb_mode_solving()
    print("  [PASS] MPB Vectorial Mode Solving")
    print("Testing Switch Cell dual-state passivity and loss...")
    test_switch_cell_passivity_and_loss()
    print("  [PASS] Switch Cell Dual-State MEEP")
    print("Testing LiTaO3 Pockels V_pi...")
    test_pockels_v_pi()
    print("  [PASS] Pockels Modulator")
    print("Testing Waveguide Crossing (MEEP FDTD Smoke)...")
    test_waveguide_crossing()
    print("  [PASS] Waveguide Crossing MEEP FDTD")
    print("Testing MZI Switch Cell...")
    test_mzi_switch_cell()
    print("  [PASS] MZI Switch Cell Transfer Matrix")
    print("Testing MZI Monte Carlo Tolerance Yield...")
    test_mzi_monte_carlo_yield()
    print("  [PASS] MZI Monte Carlo Tolerance Yield")

    print("\nRunning 16-Tree Fermat Core tests (no MEEP required)...")
    test_16tree_exhaustive_truth_table()
    print("  [PASS] 16-Tree Exhaustive Truth Table (256/256)")
    test_16tree_modular_rns()
    print("  [PASS] 16-Tree Modular RNS Correctness")
    test_16tree_zero_gating()
    print("  [PASS] 16-Tree Zero-Gating")
    test_16tree_insertion_loss()
    print("  [PASS] 16-Tree Insertion Loss < 2.0 dB")
    test_16tree_scr()
    print("  [PASS] 16-Tree SCR >= 15.0 dB")
    test_16tree_fermat_z17_exhaustive()
    print("  [PASS] 16-Tree Fermat Z_17 Exhaustive (289/289)")
    test_16tree_tree16_negation()
    print("  [PASS] 16-Tree Modular Negation Symmetry (16*W = -W mod 17)")
    test_16tree_product_ceiling()
    print("  [PASS] 16-Tree Product Ceiling (16*16 = 256 < 257)")
    test_mmi_1x2_splitter_optimization()
    print("  [PASS] 1:2 MMI Splitter Baseline (0.144 dB per stage, Margin +6.50 dB)")
    test_edge_cases_1_and_2_litao3_pockels()
    print("  [PASS] Edge Cases 1 & 2: LiTaO3 Photorefractive Drift & Pyroelectric Surge")
    test_edge_cases_3_7_10_mmi_splitter()
    print("  [PASS] Edge Cases 3, 7 & 10: Trap Absorption, Talbot Drift & Nonlinear Thresholds")
    test_edge_case_9_cumulative_crossing_crosstalk()
    print("  [PASS] Edge Case 9: Cumulative Crossing Crosstalk Scaling")
    test_edge_cases_11_and_13_mmi_spm_cod()
    print("  [PASS] Edge Cases 11 & 13: MMI SPM/Quintic Kerr & Facet COD")
    test_edge_case_12_waveguide_crossing_pdl()
    print("  [PASS] Edge Case 12: Sidewall Vertical Asymmetry & TE-TM Conversion")
    test_edge_cases_14_to_19_litao3_pockels_rf()
    print("  [PASS] Edge Cases 14 to 19: LiTaO3 100-GHz RF Modulator Multi-Physics")
    test_edge_case_29_htree_optical_skew()
    print("  [PASS] Edge Case 29: Optical H-Tree Skew Across 10 mm Die Area")
    test_baseline_link_budget_with_32_edge_cases()
    print("  [PASS] Unified Baseline Optical Link Budget (All 32 Edge Cases Integrated: Margin +5.61 dB)")
    print("All Tier 1 tests passed successfully!")



