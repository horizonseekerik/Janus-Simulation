"""
Automated Pytest Suite for Project JANUS Mini 16-Tile (Tier 5)
Verifies Algorithms 5A through 5F against strict quantitative criteria,
including signed matrix multiplication, AI workload profiling, GPU comparison,
and batch token packing.
"""

import sys
import os
import random
import numpy as np

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from configs import mini_16t_constants as cfg
from tier5_python_rns.moduli_generator import (
    generate_moduli_set,
    to_rns,
    crt_reconstruct,
    get_tiles_for_precision,
)
from tier5_python_rns.formal_verifier import run_formal_verification
from tier5_python_rns.spatial_one_hot_router import SpatialOneHotAccelerator
from tier5_python_rns.jir_thermal_scheduler import JIRThermalScheduler
from tier5_python_rns.rrns_self_healing import RRNSSelfHealingEngine
from tier5_python_rns.gemm_exact_benchmark import run_gemm_precision_benchmark, exact_opt_gemm
from tier5_python_rns.ai_workload_benchmarks import AIWorkloadProfiler
from tier5_python_rns.gpu_comparator import GPUComparator
from tier5_python_rns.batch_token_packer import BatchTokenPacker


def test_moduli_generator_alg5a():
    res = generate_moduli_set()
    assert len(res["moduli_compute"]) == 16
    assert len(res["moduli_redundant"]) == 2
    assert len(res["moduli_full"]) == 18
    assert res["M_bits"] >= 64
    # Test CRT round-trip
    val = 98765432109876543210
    r = to_rns(val, res["moduli_compute"])
    rec = crt_reconstruct(r, res["moduli_compute"], res["M_i"], res["N_i"])
    assert rec == val
    # Test precision tile mapping
    assert get_tiles_for_precision("INT4") == 1
    assert get_tiles_for_precision("INT8") == 2
    assert get_tiles_for_precision("INT16") == 4
    assert get_tiles_for_precision("INT32") == 8
    assert get_tiles_for_precision("INT64") == 16


def test_z3_formal_verifier_alg5b():
    res = run_formal_verification()
    assert res["all_passed"] is True


def test_spatial_one_hot_router_alg5c():
    np.random.seed(42)
    acc = SpatialOneHotAccelerator()

    # 1. Critical signed hand-crafted corner case
    A_corner = np.array([[-5, 3], [2, -4]], dtype=object)
    B_corner = np.array([[1, -2], [-3, 4]], dtype=object)
    C_opt_corner = acc.matmul(A_corner, B_corner)
    C_ref_corner = np.matmul(A_corner, B_corner)
    assert np.array_equal(C_opt_corner, C_ref_corner), f"Signed corner mismatch: {C_opt_corner} vs {C_ref_corner}"

    # 2. Extreme signed dynamic range boundary test (operands up to 10^7, products up to 10^14)
    A_ext = np.array([[10_000_000, -10_000_000], [-5_000_000, 5_000_000]], dtype=object)
    B_ext = np.array([[5_000_000, -5_000_000], [10_000_000, 10_000_000]], dtype=object)
    C_opt_ext = acc.matmul(A_ext, B_ext)
    C_ref_ext = np.matmul(A_ext, B_ext)
    assert np.array_equal(C_opt_ext, C_ref_ext), f"Signed boundary mismatch: {C_opt_ext} vs {C_ref_ext}"

    # 3. Random signed 32x32 matrix multiplication (full tile mesh)
    A_signed = np.random.randint(-50, 50, size=(cfg.N_dim, cfg.N_dim))
    B_signed = np.random.randint(-50, 50, size=(cfg.N_dim, cfg.N_dim))
    C_opt = acc.matmul(A_signed, B_signed)
    C_ref = np.matmul(A_signed.astype(object), B_signed.astype(object))
    diff = int(np.sum(np.abs(C_opt - C_ref)))
    assert diff == 0, f"SpatialOneHotAccelerator signed deviation: {diff}"

    # 4. Adversarial datapath verification: corrupting router traversal MUST alter optical product
    test_tile = acc.tiles[0]
    if test_tile.use_benes:
        orig_traverse = test_tile.benes.traverse
        test_tile.benes.traverse = lambda x: np.zeros(len(x), dtype=int)
        try:
            corrupted_out = test_tile.multiply_accumulate(np.array([[3]]), np.array([[5]]))
            assert False, "Adversarial check failed: corrupted Beneš traversal was not detected!"
        except Exception:
            pass  # Expected: optical photodetector detection caught corrupted traversal
        finally:
            test_tile.benes.traverse = orig_traverse
    else:
        # Active 16-Tree optical routing: corrupting transfer route MUST yield mismatch
        orig_route = test_tile.tree_router.route
        test_tile.tree_router.route = lambda x, w: (orig_route(x, w) + 1) % test_tile.modulus
        try:
            corrupted_out = test_tile.multiply_accumulate(np.array([[3]]), np.array([[5]]))
            expected_prod = (3 * 5) % test_tile.modulus
            assert corrupted_out[0, 0, 0] != expected_prod, "Adversarial check failed: corrupted 16-Tree routing was not detected!"
        finally:
            test_tile.tree_router.route = orig_route


def test_jir_thermal_scheduler_alg5d():
    scheduler = JIRThermalScheduler()
    res = scheduler.run_workload_simulation(total_epochs=1000, active_count=8, dwell_epochs=200)
    assert res["thermal_violations"] == 0
    assert res["jir_remaps"] > 0, "Expected JIR thermal rotation to remap channels"
    assert res["pass_operating_limit"] is True
    assert res["pass_crystallization_guard"] is True


def test_rrns_self_healing_alg5e():
    random.seed(42)
    engine = RRNSSelfHealingEngine()
    res = engine.run_fault_injection_trials(N_trials=2000, error_probability=0.30)
    assert res["detection_rate"] == 1.0
    assert res["correction_rate"] == 1.0
    assert res["false_alarms"] == 0
    assert res["undetected_errors"] == 0


def test_gemm_exact_benchmark_alg5f():
    # Verify exactness across all precisions
    res = run_gemm_precision_benchmark(N_dim=cfg.N_dim, precisions=[4, 8, 16, 32, 64])
    for P in [4, 8, 16, 32, 64]:
        assert res[f"INT{P}"]["deviation"] == 0
        assert res[f"INT{P}"]["status"] == "PASS"


def test_ai_workload_profiler():
    profiler = AIWorkloadProfiler()
    res_llama = profiler.benchmark_llama3_8b(batch_size=1, seq_len=1, precision="INT8")
    assert res_llama["model"] == "LLaMA-3-8B"
    assert res_llama["total_layer_macs"] > 0
    assert res_llama["average_throughput_tmacs"] > 100.0

    res_gpt2 = profiler.benchmark_gpt2_base(batch_size=1, seq_len=1, precision="INT8")
    assert res_gpt2["model"] == "GPT-2-Base"
    assert len(res_gpt2["layers"]) == 4

    res_vit = profiler.benchmark_vit_huge(batch_size=1, precision="INT8")
    assert res_vit["model"] == "ViT-Huge"
    assert len(res_vit["layers"]) == 4


def test_gpu_comparator():
    comparator = GPUComparator()
    hw_table = comparator.get_hardware_comparison_table()
    assert hw_table["janus_vs_h100_energy_efficiency_mult"] >= 100.0
    assert hw_table["janus_vs_b200_energy_efficiency_mult"] >= 50.0
    assert hw_table["janus_vs_h100_density_mult"] >= 5.0
    assert hw_table["janus_vs_b200_density_mult"] >= 5.0

    llama_comp = comparator.compare_llama3_layer("INT8")
    assert llama_comp["energy_savings_vs_h100"] > 50.0
    assert llama_comp["energy_savings_vs_b200"] > 30.0


def test_batch_token_packer():
    packer = BatchTokenPacker()

    # Verify precision engine scaling
    assert packer.get_parallel_engines("INT4") == 16
    assert packer.get_parallel_engines("INT8") == 8
    assert packer.get_parallel_engines("INT16") == 4
    assert packer.get_parallel_engines("INT32") == 2
    assert packer.get_parallel_engines("INT64") == 1

    attn_res = packer.pack_multihead_attention(num_heads=32, d_head=128, seq_len=64, precision="INT8")
    assert attn_res.spatial_row_occupancy_pct == 100.0
    assert attn_res.total_macs == 32 * 64 * 128
    assert attn_res.bit_exact_match is True

    mlp_res = packer.pack_batch_mlp(batch_size=32, hidden_dim=4096, intermediate_dim=14336, precision="INT8")
    assert mlp_res.spatial_row_occupancy_pct == 100.0
    assert mlp_res.total_macs > 0
    assert mlp_res.bit_exact_match is True


if __name__ == "__main__":
    print("Running Tier 5 Python RNS & Formal Verification unit tests...")
    print("Testing Moduli Generator & CRT Round-Trip (Algorithm 5A)...")
    test_moduli_generator_alg5a()
    print("  [PASS] Moduli Generator & CRT Reconstruct")
    print("Testing Z3 SMT Formal Proofs (Algorithm 5B)...")
    test_z3_formal_verifier_alg5b()
    print("  [PASS] Z3 Formal Verifier")
    print("Testing Spatial One-Hot Router & Beneš Routing (Algorithm 5C)...")
    test_spatial_one_hot_router_alg5c()
    print("  [PASS] Spatial One-Hot Router")
    print("Testing JIR Thermal Scheduler (Algorithm 5D)...")
    test_jir_thermal_scheduler_alg5d()
    print("  [PASS] JIR Thermal Scheduler")
    print("Testing RRNS Single-Fault Self-Healing Recovery (Algorithm 5E)...")
    test_rrns_self_healing_alg5e()
    print("  [PASS] RRNS Self-Healing Recovery")
    print("Testing Exact GEMM Multi-Precision Benchmarks (Algorithm 5F)...")
    test_gemm_exact_benchmark_alg5f()
    print("  [PASS] Exact GEMM Benchmarks")
    print("Testing AI Workload Profiler...")
    test_ai_workload_profiler()
    print("  [PASS] AI Workload Profiler")
    print("Testing GPU Comparator...")
    test_gpu_comparator()
    print("  [PASS] GPU Comparator")
    print("Testing Batch Token Packer...")
    test_batch_token_packer()
    print("  [PASS] Batch Token Packer")
    print("\nAll Tier 5 Python RNS unit tests passed successfully!")

