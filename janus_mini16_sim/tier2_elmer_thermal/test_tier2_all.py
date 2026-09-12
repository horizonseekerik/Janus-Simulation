import os
import sys
import numpy as np

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from configs import mini_16t_constants as cfg
from tier2_elmer_thermal.gmsh_mesh_generator import Gmsh3DMeshGenerator
from tier2_elmer_thermal.elmer_thermal_solver import (
    TransientThermal1D,
    Elmer3DThermalPipeline,
    NanoscaleCellThermalSubmodel,
)
from tier2_elmer_thermal.extract_thermal_rom import ThermalROMExtractor

def test_gmsh_mesh_generator_alg2a(tmp_path):
    generator = Gmsh3DMeshGenerator(domain_scale="tile")
    geo_path = str(tmp_path / "test_mesh.msh")
    generator.generate_mesh(geo_path)
    
    if os.path.exists(geo_path):
        vols = generator.calculate_mesh_volumes()
        assert vols["Active_Total_m3"] > 0.0
        assert vols["thermal_capacitances_J_K"]["Total"] > 0.0
        stats = vols.get("mesh_stats", {})
        if "num_3d_elements" in stats:
            assert stats["num_3d_elements"] > 0
            assert stats["min_quality_sicn"] > 0.0, "Mesh elements must be valid and non-inverted"

def test_1d_stack_analytical_and_mesh_convergence():
    solver = TransientThermal1D()
    
    # 1. Closed-form analytical reference comparison
    R_exact = solver.calculate_analytical_thermal_resistance(source_location="bulk")
    dT_exact = solver.P_total * R_exact
    
    res = solver.evaluate_steady_state()
    rel_error_pct = abs(res["delta_T_steady_K"] - dT_exact) / dT_exact * 100.0
    assert rel_error_pct < 0.10, f"Numerical steady-state deviates from analytical reference: {rel_error_pct:.4f}%"
    assert abs(res["R_th_stack_K_W"] - R_exact) / R_exact * 100.0 < 0.10
    
    # Also verify interface source analytical benchmark
    R_if = solver.calculate_analytical_thermal_resistance(source_location="interface")
    assert R_if < R_exact
    assert abs(R_if - 0.17367) / 0.17367 < 0.01
    
    # 2. Spatial grid convergence test (dz = 10 um, 5 um, 2.5 um)
    conv_res = solver.run_mesh_convergence_study()
    assert bool(conv_res["pass_mesh_convergence"]) is True
    assert conv_res["max_relative_error_pct"] < 0.50, f"Mesh convergence error too high: {conv_res['max_relative_error_pct']}%"
    
    # Verify monotonic asymptotic convergence
    errs = conv_res["relative_errors_pct"]
    assert errs[1] < errs[0], f"Convergence not monotonic: {errs}"
    assert errs[2] < errs[1], f"Convergence not monotonic: {errs}"

def test_transient_thermal_1d_alg2b_2c():
    """Validates the 1D multi-stratum finite-volume stack solver."""
    solver = TransientThermal1D()
    res = solver.evaluate_steady_state()
    
    # Physically authentic bounds with copper heat sink at z=z_max (delta_T ~ 1.08 K for 6.18W)
    R_exact = solver.calculate_analytical_thermal_resistance(source_location="bulk")
    dT_exact = solver.P_total * R_exact
    assert abs(res["delta_T_steady_K"] - dT_exact) / dT_exact < 0.01  # Within 1% of analytical
    assert res["T_peak_operating_C"] <= cfg.T_max_operating
    assert bool(res["pass_steady_state_limit"]) is True
    assert bool(res["pass_operating_temp_limit"]) is True
    assert bool(res["pass_crystallization_guard"]) is True

    pulse_res = solver.verify_pulse_energy_conservation()
    assert pulse_res["energy_conservation_error_frac"] < 1e-6
    assert bool(pulse_res["pass_pulse_energy_conservation"]) is True

    pcm_energy_res = solver.verify_pcm_switching_energy()
    assert pcm_energy_res["E_crystallize_J"] > 0.0
    assert pcm_energy_res["E_amorphize_J"] > 0.0
    assert bool(pcm_energy_res["pass_crystallize_energy"]) is True
    assert bool(pcm_energy_res["pass_amorphize_energy"]) is True
    assert bool(pcm_energy_res["within_order_of_magnitude_of_cfg_band"]) is True

    xtal_res = solver.evaluate_crystallization_kinetics()
    assert xtal_res["crystallized_fraction"] < 1.0e-6, "Amorphous retention must have negligible crystallized fraction"
    assert bool(xtal_res["pass_crystallization_kinetics"]) is True

def test_elmer_3d_thermal_pipeline():
    """Validates the 3D Gmsh mesh generation, multiscale coupling, and PCM hotspot model."""
    pipeline = Elmer3DThermalPipeline(domain_scale="tile")
    
    # 1. 3D Mesh Generation & Physical Groups
    mesh_info = pipeline.run_mesh_pipeline()
    assert "mesh_path" in mesh_info
    stats = mesh_info.get("mesh_stats", {})
    if "num_3d_elements" in stats:
        assert stats["num_3d_elements"] > 0
        assert stats["min_quality_sicn"] > 0.0, "All 3D tetrahedral elements must be strictly valid/non-inverted"
        assert stats["avg_quality_sicn"] > 0.60, "Mean tetrahedral quality must exceed 0.60"
        
    vols = mesh_info.get("volumes_m3", {})
    if vols:
        assert "VOL_CMOS_SUBSTRATE" in vols
        assert "VOL_SIO2_BUFFER" in vols
        assert "VOL_SIPH_STRATUM" in vols
        assert "VOL_HEAT_SPREADER2" in vols
        
    # 2. Steady-State & Multiscale Hotspot Evaluation
    steady_res = pipeline.evaluate_steady_state()
    assert steady_res["T_die_max_C"] <= cfg.T_max_operating
    assert steady_res["T_pcm_hotspot_C"] <= cfg.T_max_operating
    assert steady_res["delta_T_nano_K"] > 0.0
    assert steady_res["R_th_nano_cell_K_W"] > 100.0  # Nanoscale spreading resistance
    assert bool(steady_res["pass_pcm_hotspot_limit"]) is True
    
    # 3. 3D Elmer Results Verification (executed when Elmer binaries are available)
    if steady_res.get("elmer_solver_executed", False):
        elmer_details = steady_res["elmer_details"]
        assert os.path.isfile(elmer_details["vtu_file"]), "VTU file must exist"
        assert elmer_details["vtu_size_bytes"] > 10000, "VTU file must have non-zero size"
        
        # Verify through-thickness Z profile parsed from line.dat
        assert len(elmer_details["z_profile_m"]) >= 20, "Through-thickness profile must contain line points"
        assert len(elmer_details["T_profile_K"]) == len(elmer_details["z_profile_m"])
        # Cold plate boundary check: T(z_max) must equal ambient
        assert abs(elmer_details["T_profile_K"][-1] - pipeline.T_ambient) < 1e-3, "Top boundary must equal ambient"
        
        # Power density reconciliation (61.76 kW/m^2 across 3D tile and 1D stack)
        q_3d = elmer_details["P_tile_W"] / pipeline.A_tile
        q_1d = pipeline.P_total / pipeline.A_die
        assert abs(q_3d - q_1d) < 1e-2, f"Power density mismatch: {q_3d} vs {q_1d}"
        
        # Thermal resistance reconciliation between 3D Elmer and analytical 1D stack
        R_th_analytical = pipeline.calculate_analytical_thermal_resistance("bulk")
        assert abs(steady_res["R_th_stack_K_W"] - R_th_analytical) / R_th_analytical < 0.05, "3D and 1D thermal resistance must agree within 5%"
    else:
        assert "1D Multi-Stratum" in steady_res.get("solver_type", "")

    # 4. Multiscale Step Response
    t, dT_pcm = pipeline.solve_step_response(np.array([1e-6, 1e-3, 10.0]))
    assert len(t) == 3
    assert dT_pcm[-1] > dT_pcm[0]
    assert dT_pcm[-1] > steady_res["delta_T_steady_K"]  # Includes nanoscale hotspot rise

def test_extract_thermal_rom_alg2d():
    extractor = ThermalROMExtractor()
    res = extractor.extract_and_fit_rom()
    
    # Check that R^2 >= 0.999 on genuine computed transient response
    assert res["r_squared"] >= 0.999, f"R^2 fit ({res['r_squared']}) below 0.999 target"
    assert bool(res["pass_r_squared"]) is True
    assert bool(res["pass_max_abs_error"]) is True, f"Max absolute error {res['max_abs_error_K']} K exceeds 0.05 K"
    assert bool(res["pass_normalized_error"]) is True, f"Max normalized error {res['max_normalized_error_pct']}% exceeds 2.0%"
    assert bool(res["pass_steady_state_error"]) is True, f"Steady-state error {res['steady_state_error_pct']}% exceeds 0.5%"
    assert bool(res["pass_rom_comprehensive"]) is True
    assert bool(res["pass_tau1"]) is True
    
    # Verify deterministic ascending time constant ordering (tau_1 < tau_2 < ... < tau_5)
    tau_poles = np.array(res["tau_poles_s"])
    assert np.all(np.diff(tau_poles) > 0.0), f"Poles not strictly sorted: {tau_poles}"
    
    assert all(r > 0.0 for r in res["R_poles_K_W"]), "Fitted thermal resistances must be positive"
    assert all(np.isfinite(res["R_poles_K_W"])), "Fitted resistances must be finite"
    assert all(t > 0.0 for t in res["tau_poles_s"]), "Fitted time constants must be positive"
    assert all(np.isfinite(res["tau_poles_s"])), "Fitted time constants must be finite"

if __name__ == "__main__":
    print("Running Tier 2 Thermal unit tests...")
    print("Testing 1D Stack Analytical Benchmark & Spatial Mesh Convergence...")
    test_1d_stack_analytical_and_mesh_convergence()
    print("  [PASS] Analytical Benchmark & Mesh Convergence")
    print("Testing 1D Multi-Stratum Finite-Volume Stack Solver (Algorithms 2B & 2C)...")
    test_transient_thermal_1d_alg2b_2c()
    print("  [PASS] 1D Stack Solver")
    print("Testing 3D Multiscale Elmer Pipeline & Hotspot Model...")
    test_elmer_3d_thermal_pipeline()
    print("  [PASS] 3D Multiscale Thermal Pipeline")
    print("Testing Thermal ROM Extractor (Algorithm 2D)...")
    test_extract_thermal_rom_alg2d()
    print("  [PASS] Thermal ROM Extractor")
    print("All Tier 2 Thermal unit tests passed successfully!")
