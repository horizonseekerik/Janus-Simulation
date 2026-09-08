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
    if pytest is not None:
        return pytest.mark.skipif(not HAS_MEEP, reason="MEEP not installed")(func)
    def wrapper(*args, **kwargs):
        if not HAS_MEEP:
            print("Skipping test: MEEP not installed")
            return
        return func(*args, **kwargs)
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

@skipif_no_meep
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

@skipif_no_meep
def test_mzi_monte_carlo_yield():
    mc = Sb2S3MonteCarlo(runs=50, topology="mzi")
    res = mc.run()
    assert res["yield"] >= 0.95, f"MZI Monte Carlo yield below 95%: {res['yield']*100:.1f}%"

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
    print("All Tier 1 MEEP unit tests passed successfully!")
