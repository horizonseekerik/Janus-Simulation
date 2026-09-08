"""
ALGORITHM 5F: BIT_EXACT_GEMM_BENCHMARK
======================================
Executes standard INT4, INT8, INT16, INT32, INT64 matrix multiplication benchmarks (32x32) across the 16 residue tiles.
Compares against NumPy 128-bit integer reference ground truth.
Strict verification criterion: 0.00000000000000% numerical deviation.

The optical RNS domain only needs to bound a single element-wise multiplication product,
since CMOS accumulates the CRT-reconstructed signed products as normal binary integers.

Signed dynamic range criterion:
  For P-bit signed operands in [-2^(P-1), 2^(P-1)-1], maximum absolute product is 2^(2P-2).
  Signed CRT reconstruction requires M/2 > 2^(2P-2), i.e. M > 2^(2P-1).
"""

import sys
import os
import random
import numpy as np
from typing import Dict, Any, Tuple

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from configs import mini_16t_constants as cfg
from tier5_python_rns.moduli_generator import (
    generate_moduli_set,
    crt_reconstruct,
    get_tiles_for_precision,
)


def exact_opt_gemm(
    A: np.ndarray,
    B: np.ndarray,
    precision: str = "INT8",
    M_bits: int = None,
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Executes a bit-exact signed GEMM through the flat RNS optical pipeline.
    
    Parameters:
    -----------
    A : np.ndarray
        Left operand matrix (M x K).
    B : np.ndarray  
        Right operand matrix (K x N).
    precision : str
        Integer precision label (INT4, INT8, INT16, INT32). INT64 uses PRNS path.
    M_bits : int, optional
        Legacy parameter for backwards compatibility. If set, maps to precision.
    
    Returns:
    --------
    C_result : np.ndarray
        Bit-exact result matrix (M x N) with dtype=object.
    info : dict
        Metadata including tiles_used and deviation from reference.
    """
    if M_bits is not None and precision == "INT8":
        # Backwards compatibility: map M_bits to precision string
        precision = f"INT{M_bits}"

    p_str = precision.upper() if isinstance(precision, str) else f"INT{precision}"
    P = int(p_str.replace("INT", ""))

    mod_info = generate_moduli_set()
    full_moduli = mod_info["moduli_full"]

    if P == 64:
        k_needed = 16
    else:
        # Signed dynamic range: M > 2^(2P-1) for exact signed product reconstruction
        req_range = 2 ** (2 * P - 1)
        k_needed = 1
        prod = full_moduli[0]
        while prod <= req_range and k_needed < len(full_moduli):
            prod *= full_moduli[k_needed]
            k_needed += 1

        if k_needed > cfg.N_tiles:
            raise ValueError(
                f"{p_str} requires {k_needed} tiles, exceeding {cfg.N_tiles} physical tiles."
            )

    active_moduli = full_moduli[:k_needed]
    N_dim_i, N_dim_k = A.shape
    _, N_dim_j = B.shape

    if P != 64:
        # Flat RNS Path
        C_residues = []
        for t in range(k_needed):
            m = active_moduli[t]
            A_res = (A % m).astype(object)
            B_res = (B % m).astype(object)
            C_tile = np.zeros((N_dim_i, N_dim_j, N_dim_k), dtype=object)
            for i in range(N_dim_i):
                for j in range(N_dim_j):
                    for k in range(N_dim_k):
                        C_tile[i, j, k] = (A_res[i, k] * B_res[k, j]) % m
            C_residues.append(C_tile)

        M_tot = 1
        for m in active_moduli:
            M_tot *= m

        C_result = np.zeros((N_dim_i, N_dim_j), dtype=object)
        for i in range(N_dim_i):
            for j in range(N_dim_j):
                cmos_acc = 0
                for k in range(N_dim_k):
                    elem_res = [C_residues[t][i, j, k] for t in range(k_needed)]
                    val = crt_reconstruct(elem_res, active_moduli)
                    if val >= M_tot // 2:
                        val -= M_tot
                    cmos_acc += val
                C_result[i, j] = cmos_acc
    else:
        # PRNS INT64 Path
        from tier5_python_rns.moduli_generator import (
            generate_prns_moduli_set,
            to_prns,
            from_prns,
        )
        prns_info = generate_prns_moduli_set()

        def split64_signed(val):
            xl = val % (1 << 32)
            if xl >= (1 << 31):
                xl -= 1 << 32
            xh = (val - xl) // (1 << 32)
            return xh, xl

        C_result = np.zeros((N_dim_i, N_dim_j), dtype=object)
        for i in range(N_dim_i):
            for j in range(N_dim_j):
                cmos_acc = 0
                for k in range(N_dim_k):
                    a_val = int(A[i, k])
                    b_val = int(B[k, j])
                    a_h, a_l = split64_signed(a_val)
                    b_h, b_l = split64_signed(b_val)
                    opt_al, opt_ah = to_prns(a_l, a_h, prns_info)
                    opt_bl, opt_bh = to_prns(b_l, b_h, prns_info)
                    # Optical Cycle 0: Dual 8-tile clusters compute in parallel (all 16 physical tiles active)
                    # Cluster 0 (tiles 0..7) computes Low-Low: (a_l * b_l) mod m
                    cycle0_cluster0 = [(al * bl) % m for al, bl, m in zip(opt_al, opt_bl, prns_info["opt_moduli"])]
                    # Cluster 1 (tiles 8..15) computes High-High: (a_h * b_h) mod m
                    cycle0_cluster1 = [(ah * bh) % m for ah, bh, m in zip(opt_ah, opt_bh, prns_info["opt_moduli"])]

                    # Optical Cycle 1: Dual 8-tile clusters compute in parallel (all 16 physical tiles active)
                    # Cluster 0 (tiles 0..7) computes Low-High: (a_l * b_h) mod m
                    cycle1_cluster0 = [(al * bh) % m for al, bh, m in zip(opt_al, opt_bh, prns_info["opt_moduli"])]
                    # Cluster 1 (tiles 8..15) computes High-Low: (a_h * b_l) mod m
                    cycle1_cluster1 = [(ah * bl) % m for ah, bl, m in zip(opt_ah, opt_bl, prns_info["opt_moduli"])]

                    # Cycle 2: CMOS recombination tree (PRNS CRT decode + 64-bit shift-and-add)
                    xl_yl_rec = from_prns(cycle0_cluster0, prns_info)
                    xh_yh_rec = from_prns(cycle0_cluster1, prns_info)
                    xl_yh_rec = from_prns(cycle1_cluster0, prns_info)
                    xh_yl_rec = from_prns(cycle1_cluster1, prns_info)
                    cross_rec = xl_yh_rec + xh_yl_rec
                    product_64 = xh_yh_rec * (1 << 64) + cross_rec * (1 << 32) + xl_yl_rec
                    cmos_acc += product_64
                C_result[i, j] = cmos_acc

    C_ref = np.matmul(A.astype(object), B.astype(object))
    deviation = int(np.sum(np.abs(C_result - C_ref)))

    return C_result, {
        "tiles_used": k_needed,
        "precision": p_str,
        "deviation": deviation,
        "bit_exact": deviation == 0,
    }


def run_gemm_precision_benchmark(
    N_dim: int = cfg.N_dim, precisions: list = [4, 8, 16, 32, 64]
) -> Dict[str, Any]:
    random.seed(42)  # Deterministic reproducibility

    mod_info = generate_moduli_set()
    full_moduli = mod_info["moduli_full"]

    results = {}
    total_deviation = 0

    print("=" * 70)
    print("JANUS MINI 16-TILE: BIT-EXACT GEMM BENCHMARK SUITE (ALGORITHM 5F)")
    print("=" * 70)

    corner_cases = ["random", "max_pos", "max_neg", "mixed", "zero"]

    for P in precisions:
        for case in corner_cases:
            if P != 64:
                # Signed dynamic range: M > 2^(2P-1) for exact signed product reconstruction
                # CMOS accumulates CRT-reconstructed signed products as binary integers.
                req_range = 2 ** (2 * P - 1)
                k_needed = 1
                prod = full_moduli[0]
                while prod <= req_range and k_needed < len(full_moduli):
                    prod *= full_moduli[k_needed]
                    k_needed += 1

                # Check hardware limit
                if k_needed > cfg.N_tiles:
                    raise ValueError(
                        f"INT{P} requires {k_needed} tiles, exceeding {cfg.N_tiles} physical tiles."
                    )

                active_moduli = full_moduli[:k_needed]
            else:
                # INT64 uses dual-cluster QRNS. Exactly 16 tiles.
                # CMOS accumulates the real/cross terms separately.
                k_needed = 16

            bias = 2 ** (P - 1)
            if case == "random":
                A_signed = np.array(
                    [
                        [random.randint(-bias, bias - 1) for _ in range(N_dim)]
                        for _ in range(N_dim)
                    ],
                    dtype=object,
                )
                B_signed = np.array(
                    [
                        [random.randint(-bias, bias - 1) for _ in range(N_dim)]
                        for _ in range(N_dim)
                    ],
                    dtype=object,
                )
            elif case == "max_pos":
                A_signed = np.full((N_dim, N_dim), bias - 1, dtype=object)
                B_signed = np.full((N_dim, N_dim), bias - 1, dtype=object)
            elif case == "max_neg":
                A_signed = np.full((N_dim, N_dim), -bias, dtype=object)
                B_signed = np.full((N_dim, N_dim), -bias, dtype=object)
            elif case == "mixed":
                A_signed = np.full((N_dim, N_dim), bias - 1, dtype=object)
                B_signed = np.full((N_dim, N_dim), -bias, dtype=object)
            elif case == "zero":
                A_signed = np.zeros((N_dim, N_dim), dtype=object)
                B_signed = np.zeros((N_dim, N_dim), dtype=object)

            C_ref = np.matmul(A_signed, B_signed)

            if P != 64:
                # Flat RNS Path (Native Signed)
                C_residues = []
                for t in range(k_needed):
                    m = active_moduli[t]
                    A_res = (A_signed % m).astype(object)
                    B_res = (B_signed % m).astype(object)

                    # Optical Routing (Multiplication) without Accumulation
                    C_tile = np.zeros((N_dim, N_dim, N_dim), dtype=object)
                    for i in range(N_dim):
                        for j in range(N_dim):
                            for k in range(N_dim):
                                C_tile[i, j, k] = (A_res[i, k] * B_res[k, j]) % m
                    C_residues.append(C_tile)

                # Precompute M_tot for signed reconstruction
                M_tot = 1
                for m in active_moduli:
                    M_tot *= m

                C_janus = np.zeros((N_dim, N_dim), dtype=object)
                for i in range(N_dim):
                    for j in range(N_dim):
                        cmos_accumulator = 0
                        for k in range(N_dim):
                            elem_res = [C_residues[t][i, j, k] for t in range(k_needed)]
                            val = crt_reconstruct(elem_res, active_moduli)
                            if val >= M_tot // 2:
                                val -= M_tot
                            cmos_accumulator += val
                        C_janus[i, j] = cmos_accumulator
            else:
                # PRNS INT64 Path (16 Tiles = 2 Optical Clusters + 1 CMOS SRAM Cluster)
                from tier5_python_rns.moduli_generator import (
                    generate_prns_moduli_set,
                    to_prns,
                    from_prns,
                )

                prns_info = generate_prns_moduli_set()

                # Split 64-bit into two signed 32-bit halves.
                def split64_signed(val):
                    xl = val % (1 << 32)
                    if xl >= (1 << 31):
                        xl -= 1 << 32
                    xh = (val - xl) // (1 << 32)
                    return xh, xl

                C_janus_unsigned = np.zeros((N_dim, N_dim), dtype=object)

                for i in range(N_dim):
                    for j in range(N_dim):
                        # High precision CMOS accumulator for 64-bit products
                        cmos_accumulator = 0

                        for k in range(N_dim):
                            a_val = int(A_signed[i, k])
                            b_val = int(B_signed[k, j])

                            a_h, a_l = split64_signed(a_val)
                            b_h, b_l = split64_signed(b_val)

                            # Forward PRNS projection
                            opt_al, opt_ah = to_prns(a_l, a_h, prns_info)
                            opt_bl, opt_bh = to_prns(b_l, b_h, prns_info)

                            # Multiplexing 16 optical tiles over 2 clock cycles to compute all 4 products
                            C_xl_yl = [
                                (al * bl) % m
                                for al, bl, m in zip(
                                    opt_al, opt_bl, prns_info["opt_moduli"]
                                )
                            ]
                            C_xh_yh = [
                                (ah * bh) % m
                                for ah, bh, m in zip(
                                    opt_ah, opt_bh, prns_info["opt_moduli"]
                                )
                            ]
                            C_xl_yh = [
                                (al * bh) % m
                                for al, bh, m in zip(
                                    opt_al, opt_bh, prns_info["opt_moduli"]
                                )
                            ]
                            C_xh_yl = [
                                (ah * bl) % m
                                for ah, bl, m in zip(
                                    opt_ah, opt_bl, prns_info["opt_moduli"]
                                )
                            ]

                            # CRT Reconstruction
                            xl_yl_rec = from_prns(C_xl_yl, prns_info)
                            xh_yh_rec = from_prns(C_xh_yh, prns_info)
                            xl_yh_rec = from_prns(C_xl_yh, prns_info)
                            xh_yl_rec = from_prns(C_xh_yl, prns_info)

                            # Reconstruct the 64-bit product from 32-bit parts in CMOS (Addition strictly in CMOS)
                            cross_rec = xl_yh_rec + xh_yl_rec
                            product_64 = (
                                xh_yh_rec * (1 << 64)
                                + cross_rec * (1 << 32)
                                + xl_yl_rec
                            )

                            # CMOS Accumulation
                            cmos_accumulator += product_64

                        # Store accumulated result directly since we used A_signed
                        C_janus_unsigned[i, j] = cmos_accumulator

                C_janus = np.zeros((N_dim, N_dim), dtype=object)
                for i in range(N_dim):
                    for j in range(N_dim):
                        C_janus[i, j] = C_janus_unsigned[i, j]

            deviation = int(np.sum(np.abs(C_janus - C_ref)))
            max_err = int(np.max(np.abs(C_janus - C_ref)))
            total_deviation += deviation

            print(
                f"[*] INT{P:<2} | {case:<8} | {k_needed:>2} Channels | Max Element Error: {max_err} | Total Deviation: {deviation} | Status: {'PASS' if deviation == 0 else 'FAIL'}"
            )

        results[f"INT{P}"] = {
            "tiles_used": k_needed,
            "deviation": total_deviation,
            "max_element_error": max_err,
            "status": "PASS" if total_deviation == 0 else "FAIL",
        }

    print("-" * 70)
    print(
        f"CUMULATIVE NUMERICAL DEVIATION: {total_deviation} (0.00000000000000% Error)"
    )
    print("=" * 70)

    if total_deviation != 0:
        raise ValueError(f"GEMM arithmetic deviation non-zero: {total_deviation}")
    return results


if __name__ == "__main__":
    res = run_gemm_precision_benchmark()
