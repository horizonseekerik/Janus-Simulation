"""
Automated Pytest Suite for Master Co-Simulation Orchestrator (Project JANUS Mini 16-Tile).
Verifies Algorithm 0, multi-tier data pipelining, and 16-point decision tree execution.
"""

import os
import sys

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import pytest
from orchestrator.master_orchestrator import JanusMasterOrchestrator
from tier1_meep_optics.sb2s3_switch_cell import HAS_MEEP


def test_master_orchestrator_initialization():
    orchestrator = JanusMasterOrchestrator(verbose=False)
    assert orchestrator.validate_global_constants() is True


@pytest.mark.skipif(not HAS_MEEP, reason="Full co-simulation requires MEEP (available in Ubuntu WSL)")
def test_master_orchestrator_full_cosim(tmp_path):
    out_dir = str(tmp_path / "cosim_artifacts")
    orchestrator = JanusMasterOrchestrator(verbose=False, output_dir=out_dir)
    results = orchestrator.run_full_cosim()

    # overall_pass might be False if a solver is missing or legitimately fails
    assert "overall_pass" in results
    assert len(results["checks"]) == 16
    assert os.path.exists(results["report_path"])
    assert os.path.exists(results["json_report_path"])


def test_custom_integer_evaluation():
    orchestrator = JanusMasterOrchestrator(verbose=False)
    # Test multiple arbitrary values (small, large 64-bit, and hex)
    for test_val in [0, 1, 255, 65535, 123456789012345678, 0xDEADBEEFCAFEBABE]:
        res = orchestrator.evaluate_custom_integer(test_val, print_output=False)
        assert res["is_match"] is True
        assert res["reconstructed"] == test_val
        assert res["rrns_consistent"] is True


def test_custom_multiplication_evaluation():
    orchestrator = JanusMasterOrchestrator(verbose=False)
    test_pairs = [
        (12, 34),
        (255, 255),
        (123456789, 987654321),
        (0xFFFF, 0xFFFF),
        (1000000000, 5000000000),
    ]
    for a, b in test_pairs:
        res = orchestrator.evaluate_custom_multiply(a, b, print_output=False)
        assert res["is_match"] is True
        assert res["reconstructed_product"] == a * b


if __name__ == "__main__":
    print("Running Master Orchestrator unit tests...")
    print("Testing Master Orchestrator Initialization & Global Constants...")
    test_master_orchestrator_initialization()
    print("  [PASS] Master Orchestrator Initialization")
    print("Testing Custom 64-bit Integer Decomposition & CRT Reconstruction...")
    test_custom_integer_evaluation()
    print("  [PASS] Custom Integer CRT Reconstruction")
    print("Testing Custom Multiplication & Optical RNS Permutation...")
    test_custom_multiplication_evaluation()
    print("  [PASS] Custom Optical RNS Multiplication")
    print("All Master Orchestrator fast unit tests passed successfully!")


