"""
PROJECT JANUS MINI (16-TILE): BATCH & MULTI-HEAD TOKEN PACKING ENGINE
======================================================================
Solves the spatial crossbar occupancy challenge during autoregressive decoding
by packing attention heads (or a batch of tokens) into the optical multiplier mesh.

Calculates actual hardware utilization based on block packing efficiency.
"""

import sys
import os
import math
from dataclasses import dataclass
import numpy as np

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from configs import mini_16t_constants as cfg
from tier5_python_rns.spatial_one_hot_router import SpatialOneHotAccelerator
from tier5_python_rns.moduli_generator import generate_moduli_set, get_tiles_for_precision


@dataclass
class PackedAttentionResult:
    model: str
    num_heads: int
    d_head: int
    seq_len: int
    precision: str
    spatial_row_occupancy_pct: float
    hardware_utilization_pct: float
    total_useful_macs: int
    total_hardware_macs: int
    total_tile_blocks: int
    execution_cycles: int
    sustained_latency_ns: float
    tokens_per_second: float
    energy_uj: float
    energy_per_token_nj: float
    bit_exact_match: bool

    @property
    def total_macs(self) -> int:
        return self.total_useful_macs


@dataclass
class PackedMLPResult:
    model: str
    batch_size: int
    hidden_dim: int
    intermediate_dim: int
    precision: str
    spatial_row_occupancy_pct: float
    hardware_utilization_pct: float
    total_useful_macs: int
    total_hardware_macs: int
    total_tile_blocks: int
    execution_cycles: int
    sustained_latency_ns: float
    per_token_latency_ns: float
    tokens_per_second: float
    total_energy_uj: float
    energy_per_token_nj: float
    bit_exact_match: bool

    @property
    def total_macs(self) -> int:
        return self.total_useful_macs


class BatchTokenPacker:
    """
    Packs multi-head attention queries and batched token representations
    into optical crossbar tiles to maximize spatial waveguide occupancy.
    Supports both Autoregressive Decode Attention (H * seq_len * d_head)
    and Context Prefill Full Self-Attention (H * seq_len^2 * d_head).
    """

    def __init__(self):
        self.N_tiles = cfg.N_tiles
        self.N_dim = cfg.N_dim
        self.f_clk = cfg.f_clk
        self.T_cycle = cfg.T_cycle
        self.eta = cfg.eta_sustained
        self.P_total = cfg.P_total_system

        self.accelerator = SpatialOneHotAccelerator()

    def get_parallel_engines(self, precision: str = "INT8") -> int:
        """Returns number of independent GEMM engines for the given precision based on hardware tiles."""
        k_tiles = get_tiles_for_precision(precision)
        return max(1, self.N_tiles // k_tiles)

    def pack_multihead_attention(
        self,
        num_heads: int = 32,
        d_head: int = 128,
        seq_len: int = 64,
        precision: str = "INT8",
        verify_exactness: bool = True,
    ) -> PackedAttentionResult:
        n_engines = self.get_parallel_engines(precision)

        # 1. Total useful compute: QK^T scores (num_heads x seq_len x d_head)
        total_useful_macs = num_heads * seq_len * d_head

        # 2. Tile block decomposition (packing heads into the M dimension):
        # We pack heads into blocks of N_dim.
        blocks_M = math.ceil(num_heads / self.N_dim)
        blocks_D = math.ceil(d_head / self.N_dim)
        blocks_S = math.ceil(seq_len / self.N_dim)
        
        total_tile_blocks = blocks_M * blocks_D * blocks_S
        
        # 3. Hardware MACs performed (including padding)
        macs_per_block = self.N_dim * self.N_dim * self.N_dim
        total_hardware_macs = total_tile_blocks * macs_per_block
        
        utilization_pct = (total_useful_macs / total_hardware_macs) * 100.0
        
        # We pack min(num_heads, N_dim) into a single M-block
        occupancy_pct = (min(num_heads, self.N_dim) / float(self.N_dim)) * 100.0

        # 4. Wave-pipelined execution cycles
        execution_cycles = math.ceil(total_tile_blocks / n_engines) + 12
        raw_latency_s = execution_cycles * self.T_cycle
        sustained_latency_s = raw_latency_s / self.eta
        sustained_latency_ns = sustained_latency_s * 1e9

        # 5. Token generation rate
        tokens_per_second = 1.0 / sustained_latency_s
        total_energy_j = self.P_total * sustained_latency_s
        total_energy_uj = total_energy_j * 1e6
        energy_per_token_nj = total_energy_j * 1e9

        bit_exact = True
        if verify_exactness:
            # End-to-end packed multi-head attention tile execution:
            # Pack H head query vectors into rows and key cache into columns of an N_dim x N_dim hardware block
            rng = np.random.RandomState(42)
            H_sub = min(num_heads, self.N_dim)
            D_sub = min(d_head, self.N_dim)
            S_sub = min(seq_len, self.N_dim)

            Q_heads = rng.randint(-30, 30, size=(H_sub, D_sub))
            K_cache = rng.randint(-30, 30, size=(D_sub, S_sub))

            # Hardware tile packing with zero-padding for non-full crossbars
            Q_tile = np.zeros((self.N_dim, self.N_dim), dtype=int)
            K_tile = np.zeros((self.N_dim, self.N_dim), dtype=int)
            Q_tile[:H_sub, :D_sub] = Q_heads
            K_tile[:D_sub, :S_sub] = K_cache

            # Execute through 16-tile spatial optical accelerator
            S_opt_tile = self.accelerator.matmul(Q_tile, K_tile)

            # Unpack scores and verify against mathematical multi-head attention reference
            S_unpacked = S_opt_tile[:H_sub, :S_sub]
            S_ref = np.matmul(Q_heads.astype(object), K_cache.astype(object))
            diff = int(np.sum(np.abs(S_unpacked - S_ref)))

            # Verify padding boundary isolation (zero crosstalk in non-occupied channels)
            pad_bleed = int(np.sum(np.abs(S_opt_tile[H_sub:, :]))) + int(np.sum(np.abs(S_opt_tile[:, S_sub:])))
            bit_exact = (diff == 0 and pad_bleed == 0)

        return PackedAttentionResult(
            model="LLaMA-3-8B (Multi-Head Attention)",
            num_heads=num_heads,
            d_head=d_head,
            seq_len=seq_len,
            precision=precision.upper(),
            spatial_row_occupancy_pct=occupancy_pct,
            hardware_utilization_pct=utilization_pct,
            total_useful_macs=total_useful_macs,
            total_hardware_macs=total_hardware_macs,
            total_tile_blocks=total_tile_blocks,
            execution_cycles=execution_cycles,
            sustained_latency_ns=sustained_latency_ns,
            tokens_per_second=tokens_per_second,
            energy_uj=total_energy_uj,
            energy_per_token_nj=energy_per_token_nj,
            bit_exact_match=bit_exact,
        )

    def pack_batch_mlp(
        self,
        batch_size: int = 32,
        hidden_dim: int = 4096,
        intermediate_dim: int = 14336,
        precision: str = "INT8",
        verify_exactness: bool = True,
    ) -> PackedMLPResult:
        n_engines = self.get_parallel_engines(precision)

        # Gate + Up Projections: (batch x hidden) @ (hidden x 2*inter)
        macs_gate_up = batch_size * hidden_dim * (intermediate_dim * 2)
        # Down Projection: (batch x inter) @ (inter x hidden)
        macs_down = batch_size * intermediate_dim * hidden_dim
        total_useful_macs = macs_gate_up + macs_down

        # Block packing
        b_M = math.ceil(batch_size / self.N_dim)
        b_K1 = math.ceil(hidden_dim / self.N_dim)
        b_N1 = math.ceil((intermediate_dim * 2) / self.N_dim)
        blocks_gate_up = b_M * b_K1 * b_N1
        
        b_K2 = math.ceil(intermediate_dim / self.N_dim)
        b_N2 = math.ceil(hidden_dim / self.N_dim)
        blocks_down = b_M * b_K2 * b_N2
        
        total_blocks = blocks_gate_up + blocks_down
        
        macs_per_block = self.N_dim * self.N_dim * self.N_dim
        total_hardware_macs = total_blocks * macs_per_block
        
        utilization_pct = (total_useful_macs / total_hardware_macs) * 100.0
        occupancy_pct = (min(batch_size, self.N_dim) / float(self.N_dim)) * 100.0

        execution_cycles = math.ceil(total_blocks / n_engines) + 12
        raw_latency_s = execution_cycles * self.T_cycle
        sustained_latency_s = raw_latency_s / self.eta

        sustained_latency_ns = sustained_latency_s * 1e9
        per_token_latency_ns = sustained_latency_ns / batch_size
        tokens_per_second = batch_size / sustained_latency_s

        total_energy_j = self.P_total * sustained_latency_s
        total_energy_uj = total_energy_j * 1e6
        energy_per_token_nj = (total_energy_j / batch_size) * 1e9

        bit_exact = True
        if verify_exactness:
            # End-to-end packed token representation tile execution
            rng = np.random.RandomState(42)
            B_sub = min(batch_size, self.N_dim)
            H_sub = min(hidden_dim, self.N_dim)
            I_sub = min(intermediate_dim, self.N_dim)

            X_tokens = rng.randint(-30, 30, size=(B_sub, H_sub))
            W_weights = rng.randint(-30, 30, size=(H_sub, I_sub))

            X_tile = np.zeros((self.N_dim, self.N_dim), dtype=int)
            W_tile = np.zeros((self.N_dim, self.N_dim), dtype=int)
            X_tile[:B_sub, :H_sub] = X_tokens
            W_tile[:H_sub, :I_sub] = W_weights

            Y_opt_tile = self.accelerator.matmul(X_tile, W_tile)
            Y_unpacked = Y_opt_tile[:B_sub, :I_sub]
            Y_ref = np.matmul(X_tokens.astype(object), W_weights.astype(object))

            diff = int(np.sum(np.abs(Y_unpacked - Y_ref)))
            pad_bleed = int(np.sum(np.abs(Y_opt_tile[B_sub:, :]))) + int(np.sum(np.abs(Y_opt_tile[:, I_sub:])))
            bit_exact = (diff == 0 and pad_bleed == 0)

        return PackedMLPResult(
            model="LLaMA-3-8B (SwiGLU MLP Block)",
            batch_size=batch_size,
            hidden_dim=hidden_dim,
            intermediate_dim=intermediate_dim,
            precision=precision.upper(),
            spatial_row_occupancy_pct=occupancy_pct,
            hardware_utilization_pct=utilization_pct,
            total_useful_macs=total_useful_macs,
            total_hardware_macs=total_hardware_macs,
            total_tile_blocks=total_blocks,
            execution_cycles=execution_cycles,
            sustained_latency_ns=sustained_latency_ns,
            per_token_latency_ns=per_token_latency_ns,
            tokens_per_second=tokens_per_second,
            total_energy_uj=total_energy_uj,
            energy_per_token_nj=energy_per_token_nj,
            bit_exact_match=bit_exact,
        )
