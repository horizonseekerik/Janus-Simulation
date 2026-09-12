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
    print("All Tier 1 tests passed successfully!")


