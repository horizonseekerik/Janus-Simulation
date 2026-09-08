"""
Automated Pytest Suite for RTL Synthesis and Standard-Cell Area Analyzer.
Directly addresses Red-Team Findings #11, #12, #14, #22, #32, #33, #54.
Verifies exact ROM bit counts, register depths, pipeline stages, and physical constraints.
"""

import os
import sys
import pytest

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from tier4_rtl_digital.rtl_synthesis_analyzer import RTLSynthesisAnalyzer


def test_crt_adder_tree_synthesis_report():
    analyzer = RTLSynthesisAnalyzer()
    res = analyzer.analyze_crt_adder_tree()

    assert res.module_name == "crt_adder_tree.v"
    assert res.pipeline_stages == 8
    # Exact ROM bit count: 16 channels x 256 entries x 136 bits = 557,056 bits (~68 KiB)
    assert res.num_rom_bits == 557056
    # DFF bits across 8 stages must exceed 4,000 bits
    assert res.num_dff_bits >= 4000
    assert res.total_logic_ge >= 25000
    assert res.area_7nm_um2 > 40000.0
    # Power at 1.0 GHz in expected range (100 - 500 mW)
    assert 50.0 <= res.total_power_1ghz_mw <= 500.0


def test_rns_encoder_synthesis_report():
    analyzer = RTLSynthesisAnalyzer()
    res = analyzer.analyze_rns_encoder()

    assert res.module_name == "rns_encoder.v"
    assert res.pipeline_stages == 4
    # Exact ROM bit count: 16 channels x 8 bytes x 256 entries x 8 bits = 262,144 bits (~32 KiB)
    assert res.num_rom_bits == 262144
    assert res.num_dff_bits >= 2000
    assert res.total_logic_ge >= 35000
    assert 50.0 <= res.total_power_1ghz_mw <= 500.0


def test_jir_fault_monitor_synthesis_report():
    analyzer = RTLSynthesisAnalyzer()
    res = analyzer.analyze_jir_fault_monitor()

    assert res.module_name == "jir_fault_monitor.v"
    # Pipeline stages: 4-stage encoder + 1 registered output = 5 stages
    assert res.pipeline_stages == 5
    # Exact ROM bit count: 2 channels x 8 bytes x 256 entries x 8 bits = 32,768 bits (~4 KiB)
    assert res.num_rom_bits == 32768
    assert res.num_dff_bits >= 300
    assert res.total_logic_ge >= 4000


def test_full_chip_synthesis_summary():
    analyzer = RTLSynthesisAnalyzer()
    summary = analyzer.get_full_chip_digital_synthesis_summary()

    # Total ROM storage must equal exactly 851,968 bits (~104.0 KiB)
    assert summary["total_rom_storage_bits"] == 851968
    assert abs(summary["total_rom_storage_kib"] - 104.0) < 0.1

    # Total logic GE must be ~90,000 GE
    assert 70000 <= summary["total_digital_ge"] <= 120000

    # Area occupancy percentages across 7nm, 12nm, and 28nm
    assert 0.05 < summary["area_occupancy_7nm_pct"] < 1.0
    assert 0.10 < summary["area_occupancy_12nm_pct"] < 2.0
    assert 0.50 < summary["area_occupancy_28nm_pct"] < 5.0

    # Frequency sweep power results
    sweep = summary["power_frequency_sweep_mw"]
    assert "1_0_GHz" in sweep and "2_0_GHz" in sweep and "3_0_GHz" in sweep
    assert sweep["1_0_GHz"] < sweep["2_0_GHz"] < sweep["3_0_GHz"]

    # synth.ys exists
    synth_ys_path = os.path.join(BASE_DIR, "tier4_rtl_digital", "synth.ys")
    assert os.path.exists(synth_ys_path)


def test_sta_timing_and_sdc():
    """Verifies SDC constraint file existence and analytical STA results."""
    sdc_path = os.path.join(BASE_DIR, "tier4_rtl_digital", "janus_tier4_top.sdc")
    assert os.path.exists(sdc_path), "janus_tier4_top.sdc must exist"

    analyzer = RTLSynthesisAnalyzer()
    sta = analyzer.compute_static_timing_analysis()

    assert "7nm_FinFET" in sta and "12nm_FinFET" in sta and "28nm_FDSOI" in sta

    # TSMC 7nm must achieve >= 3.0 GHz F_max with positive slack at 1GHz, 2GHz, 3GHz
    tsmc7 = sta["7nm_FinFET"]
    assert tsmc7.f_max_ghz >= 3.5
    assert tsmc7.setup_slack_1ghz_ps > 500.0
    assert tsmc7.setup_slack_2ghz_ps > 100.0
    assert tsmc7.setup_slack_3ghz_ps > 0.0

    # GF 12nm must meet timing at 1.0 GHz and 2.0 GHz
    gf12 = sta["12nm_FinFET"]
    assert gf12.f_max_ghz >= 2.0
    assert gf12.setup_slack_1ghz_ps > 400.0
    assert gf12.setup_slack_2ghz_ps > 0.0

    # 28nm FD-SOI meets timing at 1.0 GHz
    fdsoi28 = sta["28nm_FDSOI"]
    assert fdsoi28.f_max_ghz >= 1.0
    assert fdsoi28.setup_slack_1ghz_ps > 0.0


def test_missing_file_raises_filenotfound():
    """Verifies that missing files raise FileNotFoundError rather than inventing fake cells."""
    analyzer = RTLSynthesisAnalyzer()
    with pytest.raises(FileNotFoundError):
        analyzer._parse_rtl_structural_metrics("non_existent_module.v")

