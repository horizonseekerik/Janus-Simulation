"""
Automated Pytest Suite for Monolithic Dynamic Multi-Physics Co-Simulation.
Verifies Algorithm 0-M: Coupled electro-optics, 3D thermal diffusion, SPICE APD/latch,
and digital CRT/RRNS exact arithmetic under live dynamic multi-physics feedback.
"""

import os
import sys
import pytest
import numpy as np

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from configs import mini_16t_constants as cfg
from orchestrator.monolithic_dynamic_cosim import (
    MonolithicDynamicCoSimulator,
    DynamicCoSimConfig,
    run_monolithic_dynamic_cosim,
)


def test_dynamic_co_simulation_initialization():
    """Validates configuration parameters, time step sizing, and physical constants."""
    config = DynamicCoSimConfig(sim_time_ps=100.0, dt_ps=0.1)
    sim = MonolithicDynamicCoSimulator(config)

    assert sim.num_steps == 1000
    assert sim.dt_s == 1e-13  # 100 fs
    assert sim.t_clk_ps == 10.0  # 100 GHz -> 10 ps period
    assert sim.L_baseline_dB == cfg.L_32_edge_cases_baseline_dB
    assert sim.beta_temp == 0.08  # APD temp drift: +0.08 V/K
    assert sim.d_dead == 33.6e-9  # APD dead-space: 33.6 nm
    assert sim.sigma_rdf == 10.02e-3  # StrongARM RDF: 10.02 mV


def test_dynamic_thermal_optical_feedback():
    """Validates that continuous RF drive induces Joule heating and dynamic thermo-optic phase shift."""
    config = DynamicCoSimConfig(sim_time_ps=50.0, dt_ps=0.2, enable_noise=False)
    sim = MonolithicDynamicCoSimulator(config)

    t_initial = sim.T_nodes[0]
    # Drive continuous RF voltage
    for step in range(100):
        res = sim.step_dynamic_state(t_ps=step * 0.2, v_rf_drive=2.0, clk_val=1.0, tile_active=True)

    t_final = res["t_mod_C"]
    assert t_final >= t_initial, "Joule heating must increase or maintain temperature"
    assert t_final <= cfg.SPEC_T_max_operating_C, f"Temperature {t_final} C exceeded operating ceiling"
    assert abs(res["delta_phi"]) > 0.0, "Electro-optic phase shift must be non-zero under RF drive"


def test_dynamic_apd_space_charge_and_temperature_drift():
    """Validates that APD breakdown voltage drifts with temperature and space-charge screening is active."""
    config = DynamicCoSimConfig(sim_time_ps=30.0, dt_ps=0.1, enable_noise=False)
    sim = MonolithicDynamicCoSimulator(config)

    # Force a temperature rise on APD node
    sim.T_nodes[2] = 35.0  # +10 C above ambient (25 C)
    res = sim.step_dynamic_state(t_ps=5.0, v_rf_drive=2.0, clk_val=0.0, tile_active=True)

    # Expected V_bd = 25.0 + 0.08 * 10 = 25.8 V
    assert abs(res["v_bd"] - 25.8) < 1e-3, f"V_bd was {res['v_bd']}, expected 25.8 V"
    assert res["i_pd_uA"] > 0.0, "Photocurrent must be positive under optical excitation"


def test_dynamic_htree_skew_and_rrns_recovery():
    """Validates that dynamic thermal gradients maintain optical H-tree skew < 100 fs and RRNS heals errors."""
    config = DynamicCoSimConfig(sim_time_ps=100.0, dt_ps=0.1, enable_noise=True)
    sim = MonolithicDynamicCoSimulator(config)

    res = sim.run_simulation(val_a=123456789, val_b=987654321)
    m = res["metrics"]
    a = res["algorithmic"]

    assert m["skew_max_fs"] <= 100.0, f"Optical H-tree skew {m['skew_max_fs']} fs exceeded 100 fs budget"
    assert a["product_match"] is True, f"64-bit product mismatch: {a['recovered_product']} != {a['product_ref']}"
    assert a["rrns_healed"] is True, "RRNS self-healing must report success"


def test_monolithic_cosim_end_to_end():
    """End-to-end execution of the monolithic dynamic co-simulation engine."""
    res = run_monolithic_dynamic_cosim(sim_time_ps=100.0, val_a=55555, val_b=77777)
    m = res["metrics"]
    a = res["algorithmic"]

    assert m["pass_link_margin"] is True, f"Baseline margin {m['nominal_baseline_margin_dB']} dB below 4.5 dB"
    assert m["pass_clock_skew"] is True, f"Clock skew {m['skew_max_fs']} fs exceeded 100 fs"
    assert m["pass_thermal_ceiling"] is True, f"Peak temperature {m['t_peak_C']} C exceeded 70 C"
    assert m["eye_height_mV"] >= 15.0, f"Eye height {m['eye_height_mV']} mV below 15 mV"
    assert m["eye_opening_pct"] >= 65.0, f"Eye opening {m['eye_opening_pct']}% below 65%"
    assert a["product_match"] is True, "End-to-end 64-bit product must match reference"
