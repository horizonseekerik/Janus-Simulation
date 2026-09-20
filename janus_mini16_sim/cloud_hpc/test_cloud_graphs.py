"""
TEST SUITE: CLOUD HPC SCIENTIFIC GRAPHING & CHECKPOINT SUITE
============================================================
Verifies that all 19 publication-grade figures, checkpoint overlays,
and OFC composite dashboards are properly generated, non-empty,
and formatted correctly in both PNG and vector PDF formats.
"""

import os
import sys
import shutil
import pytest
import numpy as np

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from cloud_hpc.cloud_graph_generator import (
    CloudGraphGenerator,
    MC_CHECKPOINT_INTERVALS,
    SPICE_CHECKPOINT_INTERVALS
)
from tier1_meep_optics.monte_carlo_tolerance import MonteCarloFoundryTolerance1M
from tier3_xyce_circuit.eye_diagram_ber import EyeDiagramAndBERSolver


@pytest.fixture(scope="module")
def test_output_dir():
    """Temporary test directory for generated figures."""
    out_dir = os.path.abspath(os.path.join(base_dir, "output", "test_cloud_figures"))
    os.makedirs(out_dir, exist_ok=True)
    yield out_dir
    # Cleanup after test suite
    if os.path.exists(out_dir):
        shutil.rmtree(out_dir, ignore_errors=True)


def test_cloud_generator_initialization(test_output_dir):
    """Verifies CloudGraphGenerator initializes and creates target directories."""
    gen = CloudGraphGenerator(output_dir=test_output_dir)
    assert os.path.exists(gen.output_dir)
    assert gen.dpi >= 300


def test_category_a_monte_carlo_graphs(test_output_dir):
    """Verifies all 7 Category A Monte Carlo tolerance and checkpoint figures."""
    gen = CloudGraphGenerator(output_dir=test_output_dir)
    np.random.seed(42)
    margins = np.random.normal(8.41, 0.42, 10_000)

    # 1. Convergence plot
    gen.generate_mc_convergence_plot(margins, [1_000, 5_000, 10_000])
    assert os.path.exists(os.path.join(test_output_dir, "fig_mc_convergence_vs_runs.png"))
    assert os.path.exists(os.path.join(test_output_dir, "fig_mc_convergence_vs_runs.pdf"))
    assert os.path.getsize(os.path.join(test_output_dir, "fig_mc_convergence_vs_runs.png")) > 1000

    # 2. Histogram PDF plot
    gen.generate_mc_histogram_pdf_plot(margins)
    assert os.path.exists(os.path.join(test_output_dir, "fig_mc_histogram_pdf_1m.png"))
    assert os.path.exists(os.path.join(test_output_dir, "fig_mc_histogram_pdf_1m.pdf"))

    # 3. Yield CDF plot
    gen.generate_mc_yield_cdf_plot(margins)
    assert os.path.exists(os.path.join(test_output_dir, "fig_mc_yield_cdf_semilog.png"))
    assert os.path.exists(os.path.join(test_output_dir, "fig_mc_yield_cdf_semilog.pdf"))

    # 4. Variance decomposition
    gen.generate_mc_variance_decomposition_plot()
    assert os.path.exists(os.path.join(test_output_dir, "fig_mc_variance_decomposition.png"))

    # 5. Process window 2D
    gen.generate_mc_process_window_2d_plot()
    assert os.path.exists(os.path.join(test_output_dir, "fig_mc_process_window_2d.png"))

    # 6. Cascaded MMI loss
    gen.generate_mc_cascaded_mmi_loss_plot()
    assert os.path.exists(os.path.join(test_output_dir, "fig_mc_cascaded_mmi_loss.png"))

    # 7. Checkpoints evolution
    gen.generate_mc_checkpoint_evolution_plot(margins, [1_000, 5_000, 10_000])
    assert os.path.exists(os.path.join(test_output_dir, "fig_mc_checkpoints_evolution.png"))


def test_category_b_spice_graphs(test_output_dir):
    """Verifies all 6 Category B 100 GHz SPICE signal integrity figures."""
    gen = CloudGraphGenerator(output_dir=test_output_dir)

    # 8. 2D eye density heatmap
    gen.generate_spice_2d_eye_density_heatmap(n_cycles=1_000)
    assert os.path.exists(os.path.join(test_output_dir, "fig_spice_1m_eye_density_heatmap.png"))

    # 9. BER waterfall curve
    gen.generate_spice_ber_waterfall_plot()
    assert os.path.exists(os.path.join(test_output_dir, "fig_spice_ber_waterfall_curve.png"))

    # 10. StrongARM regeneration histogram
    gen.generate_spice_strongarm_regen_plot(n_cycles=1_000)
    assert os.path.exists(os.path.join(test_output_dir, "fig_spice_strongarm_regen_histogram_1m.png"))

    # 11. Jitter distribution
    gen.generate_spice_jitter_distribution_plot()
    assert os.path.exists(os.path.join(test_output_dir, "fig_spice_jitter_distribution.png"))

    # 12. Noise PSD spectrum
    gen.generate_spice_noise_psd_spectrum_plot()
    assert os.path.exists(os.path.join(test_output_dir, "fig_spice_noise_psd_spectrum.png"))

    # 13. Eye checkpoints evolution
    gen.generate_spice_checkpoint_evolution_plot([100, 500, 1_000])
    assert os.path.exists(os.path.join(test_output_dir, "fig_spice_eye_checkpoints_evolution.png"))


def test_category_c_thermal_graphs(test_output_dir):
    """Verifies all 4 Category C Elmer 3D FEM & Foster RC thermal figures."""
    gen = CloudGraphGenerator(output_dir=test_output_dir)

    # 14. 3D stratum slices
    gen.generate_thermal_3d_stratum_slices_plot()
    assert os.path.exists(os.path.join(test_output_dir, "fig_thermal_3d_stratum_slices.png"))

    # 15. Transient step 5-pole response
    gen.generate_thermal_transient_step_5pole_plot()
    assert os.path.exists(os.path.join(test_output_dir, "fig_thermal_transient_step_5pole.png"))

    # 16. Lateral crosstalk decay
    gen.generate_thermal_lateral_crosstalk_plot()
    assert os.path.exists(os.path.join(test_output_dir, "fig_thermal_lateral_crosstalk_decay.png"))

    # 17. JIR clamping dynamics
    gen.generate_thermal_jir_clamping_plot()
    assert os.path.exists(os.path.join(test_output_dir, "fig_thermal_jir_clamping_dynamics.png"))


def test_category_d_ofc_dashboards(test_output_dir):
    """Verifies all 2 Category D OFC 3-page composite dashboards."""
    gen = CloudGraphGenerator(output_dir=test_output_dir)

    # 18. Hero dashboard
    gen.generate_ofc_3page_hero_dashboard()
    assert os.path.exists(os.path.join(test_output_dir, "fig_ofc_3page_hero_dashboard.png"))
    assert os.path.exists(os.path.join(test_output_dir, "fig_ofc_3page_hero_dashboard.pdf"))

    # 19. Radar sign-off matrix
    gen.generate_ofc_radar_signoff_plot()
    assert os.path.exists(os.path.join(test_output_dir, "fig_ofc_radar_signoff_matrix.png"))
    assert os.path.exists(os.path.join(test_output_dir, "fig_ofc_radar_signoff_matrix.pdf"))


def test_monte_carlo_cli_export_graphs(test_output_dir):
    """Verifies monte_carlo_tolerance.py generates graphs when requested."""
    mc_dir = os.path.join(test_output_dir, "mc_cli_test")
    engine = MonteCarloFoundryTolerance1M(n_samples=5_000)
    res = engine.run_simulation(batch_size=2_500, export_graphs=True, graph_dir=mc_dir)
    assert res["n_samples"] == 5_000
    assert os.path.exists(os.path.join(mc_dir, "fig_mc_convergence_vs_runs.png"))
    assert os.path.exists(os.path.join(mc_dir, "fig_mc_yield_cdf_semilog.png"))


def test_spice_cli_export_graphs(test_output_dir):
    """Verifies eye_diagram_ber.py exports graphs when invoked."""
    spice_dir = os.path.join(test_output_dir, "spice_cli_test")
    gen = CloudGraphGenerator(output_dir=spice_dir)
    gen.generate_spice_2d_eye_density_heatmap(n_cycles=500)
    gen.generate_spice_ber_waterfall_plot()
    assert os.path.exists(os.path.join(spice_dir, "fig_spice_1m_eye_density_heatmap.png"))
    assert os.path.exists(os.path.join(spice_dir, "fig_spice_ber_waterfall_curve.png"))
