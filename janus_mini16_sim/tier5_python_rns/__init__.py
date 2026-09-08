"""
PROJECT JANUS MINI (16-TILE): TIER 5 PYTHON RNS ENGINE
======================================================
This package provides mathematical and architectural simulation for the 
JANUS Mini 16-Tile Planar MVP, calculating performance and thermal bounds
from physical parameters.

Exported Public API:
-------------------
- Algorithm 5A: generate_moduli_set, to_rns, crt_reconstruct
- Algorithm 5B: run_formal_verification
- Algorithm 5C: SpatialOneHotAccelerator, SpatialOneHotTile
- Algorithm 5D: JIRThermalScheduler
- Algorithm 5E: RRNSSelfHealingEngine
- Algorithm 5F: run_gemm_precision_benchmark
"""

from .moduli_generator import (
    generate_moduli_set,
    to_rns,
    crt_reconstruct,
    mod_inverse,
    extended_gcd,
)

from .formal_verifier import (
    run_formal_verification,
)

from .spatial_one_hot_router import SpatialOneHotAccelerator, SpatialOneHotTile

from .jir_thermal_scheduler import JIRThermalScheduler

from .rrns_self_healing import RRNSSelfHealingEngine

from .gemm_exact_benchmark import run_gemm_precision_benchmark, exact_opt_gemm

from .ai_workload_benchmarks import AIWorkloadProfiler

from .gpu_comparator import GPUComparator

from .batch_token_packer import BatchTokenPacker

from .moduli_generator import get_tiles_for_precision

__all__ = [
    # Algorithm 5A
    "generate_moduli_set",
    "to_rns",
    "crt_reconstruct",
    "mod_inverse",
    "extended_gcd",
    "get_tiles_for_precision",
    # Algorithm 5B
    "run_formal_verification",
    # Algorithm 5C
    "SpatialOneHotAccelerator",
    "SpatialOneHotTile",
    # Algorithm 5D
    "JIRThermalScheduler",
    # Algorithm 5E
    "RRNSSelfHealingEngine",
    # Algorithm 5F
    "run_gemm_precision_benchmark",
    "exact_opt_gemm",
    # Workload Profiling & Benchmarks
    "AIWorkloadProfiler",
    "GPUComparator",
    "BatchTokenPacker",
]

__version__ = "1.0.0"
__tier__ = "Tier 5: Architecture, JIR & RNS Arithmetic"
