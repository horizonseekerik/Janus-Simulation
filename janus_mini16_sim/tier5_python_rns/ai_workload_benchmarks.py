"""
PROJECT JANUS MINI (16-TILE): AI WORKLOAD BENCHMARKING ENGINE
==============================================================
Profiles real-world Deep Learning layers computing actual architectural performance
and runs sample bit-exact GEMM verification.
"""

import sys
import os
import math
from dataclasses import dataclass, asdict
from typing import Dict, Any
import numpy as np

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from configs import mini_16t_constants as cfg
from tier5_python_rns.gemm_exact_benchmark import exact_opt_gemm
from tier5_python_rns.moduli_generator import get_tiles_for_precision


@dataclass
class LayerBenchmarkResult:
    model_name: str
    layer_name: str
    precision: str
    M: int
    K: int
    N: int
    total_macs: int
    execution_cycles: int
    sustained_latency_ns: float
    throughput_tmacs: float
    energy_uj: float
    energy_efficiency_tmacs_w: float
    bit_exact_verified: bool


class AIWorkloadProfiler:
    def __init__(self):
        self.N_mult_total = cfg.N_mult_total
        self.f_clk = cfg.f_clk
        # Enforce exact clock period definition T_cycle = 1 / f_clk
        self.T_cycle = 1.0 / self.f_clk
        self.eta = cfg.eta_sustained
        self.P_total = cfg.P_total_system

    def profile_layer(
        self,
        model_name: str,
        layer_name: str,
        M: int,
        K: int,
        N: int,
        precision: str = "INT8",
        verify_sample: bool = True,
    ) -> LayerBenchmarkResult:
        total_macs = M * K * N

        # Canonical tile assignment per precision
        tiles_per_op = get_tiles_for_precision(precision)
        mults_per_cycle = self.N_mult_total // tiles_per_op

        # Pipeline latency breakdown from first principles:
        # 1. RNS input encoding depth: 2 cycles
        # 2. Optical time-of-flight through 15-stage Beneš mesh: 1 cycle (10 ps at 100 GHz)
        # 3. Photodetector StrongARM sensing & CMOS accumulator tree: 3 cycles
        # 4. CRT output reconstruction & signed domain folding: 4 cycles
        pipeline_fill_cycles = 10

        # Calculate performance from first principles
        compute_cycles = math.ceil(total_macs / mults_per_cycle)
        execution_cycles = compute_cycles + pipeline_fill_cycles
        raw_latency_s = execution_cycles * self.T_cycle
        sustained_latency_s = raw_latency_s / self.eta

        sustained_latency_ns = sustained_latency_s * 1e9

        throughput_tmacs = (total_macs / sustained_latency_s) / 1e12
        energy_j = self.P_total * sustained_latency_s
        energy_uj = energy_j * 1e6
        efficiency_tmacs_w = throughput_tmacs / self.P_total

        bit_exact = True
        if verify_sample:
            # Full signed dynamic range verification
            prec_str = precision.upper() if isinstance(precision, str) else f"INT{precision}"
            prec_bits = int(prec_str.replace("INT", ""))
            bias = 2 ** (prec_bits - 1)

            test_M = min(M, 16)
            test_K = min(K, 16)
            test_N = min(N, 16)
            A_test = np.random.randint(-bias, bias - 1, size=(test_M, test_K))
            B_test = np.random.randint(-bias, bias - 1, size=(test_K, test_N))
            C_opt, _ = exact_opt_gemm(A_test, B_test, precision=precision)
            C_ref = np.matmul(A_test.astype(object), B_test.astype(object))
            diff = int(np.sum(np.abs(C_opt - C_ref)))
            bit_exact = (diff == 0)

        return LayerBenchmarkResult(
            model_name=model_name,
            layer_name=layer_name,
            precision=precision.upper(),
            M=M,
            K=K,
            N=N,
            total_macs=total_macs,
            execution_cycles=execution_cycles,
            sustained_latency_ns=sustained_latency_ns,
            throughput_tmacs=throughput_tmacs,
            energy_uj=energy_uj,
            energy_efficiency_tmacs_w=efficiency_tmacs_w,
            bit_exact_verified=bit_exact,
        )

    def benchmark_llama3_8b(
        self, batch_size: int = 1, seq_len: int = 1, precision: str = "INT8"
    ) -> Dict[str, Any]:
        hidden_dim = 4096
        intermediate_dim = 14336
        M = batch_size * seq_len

        layers = [
            ("Q_Projection", M, hidden_dim, hidden_dim),
            ("K_Projection", M, hidden_dim, hidden_dim // 4),
            ("V_Projection", M, hidden_dim, hidden_dim // 4),
            ("Attention_Out", M, hidden_dim, hidden_dim),
            ("SwiGLU_Gate_Up", M, hidden_dim, intermediate_dim * 2),
            ("SwiGLU_Down", M, intermediate_dim, hidden_dim),
        ]

        results = []
        for name, m, k, n in layers:
            res = self.profile_layer("LLaMA-3-8B", name, m, k, n, precision=precision)
            results.append(res)

        total_macs = sum(r.total_macs for r in results)
        total_latency_ns = sum(r.sustained_latency_ns for r in results)
        total_energy_uj = sum(r.energy_uj for r in results)
        avg_throughput = (total_macs / (total_latency_ns * 1e-9)) / 1e12

        return {
            "model": "LLaMA-3-8B",
            "precision": precision,
            "batch_size": batch_size,
            "seq_len": seq_len,
            "layers": [asdict(r) for r in results],
            "total_layer_macs": total_macs,
            "total_layer_latency_ns": total_latency_ns,
            "total_layer_energy_uj": total_energy_uj,
            "average_throughput_tmacs": avg_throughput,
            "energy_efficiency_tmacs_w": avg_throughput / self.P_total,
        }

    def benchmark_gpt2_base(
        self, batch_size: int = 1, seq_len: int = 1, precision: str = "INT8"
    ) -> Dict[str, Any]:
        """Profiles the 4 core projection layers of a GPT-2 Base Transformer layer."""
        hidden_dim = 768
        intermediate_dim = 3072
        M = batch_size * seq_len

        layers = [
            ("QKV_Projection", M, hidden_dim, 3 * hidden_dim),
            ("Attention_Out", M, hidden_dim, hidden_dim),
            ("MLP_FC1", M, hidden_dim, intermediate_dim),
            ("MLP_FC2", M, intermediate_dim, hidden_dim),
        ]

        results = []
        for name, m, k, n in layers:
            res = self.profile_layer("GPT-2-Base", name, m, k, n, precision=precision)
            results.append(res)

        total_macs = sum(r.total_macs for r in results)
        total_latency_ns = sum(r.sustained_latency_ns for r in results)
        total_energy_uj = sum(r.energy_uj for r in results)
        avg_throughput = (total_macs / (total_latency_ns * 1e-9)) / 1e12

        return {
            "model": "GPT-2-Base",
            "precision": precision,
            "batch_size": batch_size,
            "seq_len": seq_len,
            "layers": [asdict(r) for r in results],
            "total_layer_macs": total_macs,
            "total_layer_latency_ns": total_latency_ns,
            "total_layer_energy_uj": total_energy_uj,
            "average_throughput_tmacs": avg_throughput,
            "energy_efficiency_tmacs_w": avg_throughput / self.P_total,
        }

    def benchmark_vit_huge(
        self, batch_size: int = 1, precision: str = "INT8"
    ) -> Dict[str, Any]:
        """Profiles the 4 core projection layers of a ViT-Huge (ViT-H/14) Transformer layer."""
        hidden_dim = 1280
        intermediate_dim = 5120
        # 14x14 patch grid on 224x224 image = 196 patches + 1 cls token = 197 tokens per image
        seq_len = 197
        M = batch_size * seq_len

        layers = [
            ("QKV_Projection", M, hidden_dim, 3 * hidden_dim),
            ("Attention_Out", M, hidden_dim, hidden_dim),
            ("MLP_FC1", M, hidden_dim, intermediate_dim),
            ("MLP_FC2", M, intermediate_dim, hidden_dim),
        ]

        results = []
        for name, m, k, n in layers:
            res = self.profile_layer("ViT-Huge", name, m, k, n, precision=precision)
            results.append(res)

        total_macs = sum(r.total_macs for r in results)
        total_latency_ns = sum(r.sustained_latency_ns for r in results)
        total_energy_uj = sum(r.energy_uj for r in results)
        avg_throughput = (total_macs / (total_latency_ns * 1e-9)) / 1e12

        return {
            "model": "ViT-Huge",
            "precision": precision,
            "batch_size": batch_size,
            "seq_len": seq_len,
            "layers": [asdict(r) for r in results],
            "total_layer_macs": total_macs,
            "total_layer_latency_ns": total_latency_ns,
            "total_layer_energy_uj": total_energy_uj,
            "average_throughput_tmacs": avg_throughput,
            "energy_efficiency_tmacs_w": avg_throughput / self.P_total,
        }


if __name__ == "__main__":
    profiler = AIWorkloadProfiler()
    llama = profiler.benchmark_llama3_8b()
    print(f"LLaMA-3-8B Total MACs: {llama['total_layer_macs']:,}")
    gpt2 = profiler.benchmark_gpt2_base()
    print(f"GPT-2-Base Total MACs: {gpt2['total_layer_macs']:,}")
    vit = profiler.benchmark_vit_huge()
    print(f"ViT-Huge Total MACs: {vit['total_layer_macs']:,}")
