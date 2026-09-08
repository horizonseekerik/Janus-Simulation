"""
ALGORITHM 5C: SPATIAL_ONE_HOT_ROUTER
====================================
Simulates spatial 1-hot 256-channel tensor contractions across 16 optical tiles.
Models an ACTUAL Beneš network topology and implements the exact Waksman 
looping algorithm to compute the physical switch states for a given permutation.
"""

import sys
import os
import math
import numpy as np

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from configs import mini_16t_constants as cfg
from tier5_python_rns.moduli_generator import generate_moduli_set, crt_reconstruct

class BenesNetwork:
    """Models an N-port Beneš network (N must be a power of 2) with real routing."""
    def __init__(self, N: int):
        self.N = N
        self.num_stages = 2 * int(np.log2(N)) - 1 if N > 1 else 0
        self.switches_per_stage = N // 2
        # Switch states: 0 = bar (straight), 1 = cross
        self.switch_states = np.zeros((self.num_stages, self.switches_per_stage), dtype=int)
        
    def _route_subnetwork(self, pi, stage_offset, row_offset, current_N):
        """Recursive Waksman looping algorithm for bipartite graph routing."""
        if current_N == 2:
            # Base case: single 2x2 switch
            state = 0 if pi[0] == 0 else 1
            self.switch_states[stage_offset, row_offset] = state
            return

        switches = current_N // 2
        input_stage = stage_offset
        output_stage = stage_offset + 2 * int(np.log2(current_N)) - 2

        inv_pi = {v: k for k, v in enumerate(pi)}
        adj_in = [[] for _ in range(switches)]
        for pin in range(current_N):
            adj_in[pin // 2].append(pin)

        edge_color = {}
        visited = set()
        for s in range(switches):
            for pin in adj_in[s]:
                if pin in visited:
                    continue
                curr = pin
                while curr not in visited:
                    visited.add(curr)
                    edge_color[curr] = 0
                    out_p = pi[curr]
                    part_out = out_p ^ 1
                    part_in = inv_pi[part_out]
                    visited.add(part_in)
                    edge_color[part_in] = 1
                    curr = part_in ^ 1

        for in_sw in range(switches):
            self.switch_states[input_stage, row_offset + in_sw] = edge_color[2 * in_sw]
        for out_sw in range(switches):
            self.switch_states[output_stage, row_offset + out_sw] = edge_color[inv_pi[2 * out_sw]]

        pi_upper = [0] * switches
        pi_lower = [0] * switches
        for pin, out_pin in enumerate(pi):
            in_sw = pin // 2
            out_sw = out_pin // 2
            if edge_color[pin] == 0:
                pi_upper[in_sw] = out_sw
            else:
                pi_lower[in_sw] = out_sw

        self._route_subnetwork(pi_upper, stage_offset + 1, row_offset, switches)
        self._route_subnetwork(pi_lower, stage_offset + 1, row_offset + switches // 2, switches)

    def waksman_route(self, pi):
        """Computes all physical switch settings for the permutation pi."""
        assert len(pi) == self.N, "Permutation size must match network size"
        # Reset states
        self.switch_states = np.zeros((self.num_stages, self.switches_per_stage), dtype=int)
        self._route_subnetwork(pi, 0, 0, self.N)
        
    def traverse(self, inputs):
        """
        Physically routes an array or one-hot vector of inputs through the switch matrix.
        Traverses every stage of 2x2 switches according to self.switch_states.
        Returns the output vector after passing through the full Beneš network fabric.
        """
        data = list(inputs)
        if len(data) != self.N:
            raise ValueError(f"Input size ({len(data)}) must match network size ({self.N})")
        return np.array(self._traverse_subnetwork(data, 0, 0, self.N))

    def _traverse_subnetwork(self, data, stage_offset, row_offset, current_N):
        """Hierarchical physical switch traversal matching the Waksman topology."""
        if current_N == 2:
            s = self.switch_states[stage_offset, row_offset]
            return [data[1], data[0]] if s == 1 else [data[0], data[1]]

        switches = current_N // 2
        input_stage = stage_offset
        output_stage = stage_offset + 2 * int(np.log2(current_N)) - 2

        # Input stage switches
        upper_in = [0] * switches
        lower_in = [0] * switches
        for in_sw in range(switches):
            s = self.switch_states[input_stage, row_offset + in_sw]
            in0 = data[2 * in_sw]
            in1 = data[2 * in_sw + 1]
            if s == 0:
                upper_in[in_sw] = in0
                lower_in[in_sw] = in1
            else:
                upper_in[in_sw] = in1
                lower_in[in_sw] = in0

        # Propagate through upper and lower subnetworks
        upper_out = self._traverse_subnetwork(
            upper_in, stage_offset + 1, row_offset, switches
        )
        lower_out = self._traverse_subnetwork(
            lower_in, stage_offset + 1, row_offset + switches // 2, switches
        )

        # Output stage switches
        out = [0] * current_N
        for out_sw in range(switches):
            s = self.switch_states[output_stage, row_offset + out_sw]
            in0 = upper_out[out_sw]
            in1 = lower_out[out_sw]
            if s == 0:
                out[2 * out_sw] = in0
                out[2 * out_sw + 1] = in1
            else:
                out[2 * out_sw] = in1
                out[2 * out_sw + 1] = in0

        return out


class SpatialOneHotTile:
    """
    Emulates a single optical multiplier tile using physical 1-hot waveguide encoding,
    Beneš routing network stage traversal, and optical photodetector detection.
    """

    def __init__(
        self,
        modulus: int,
        N_dim: int = cfg.N_dim,
        N_alphabet: int = cfg.N_alphabet,
    ):
        self.modulus = modulus
        self.N_dim = N_dim
        self.N_alphabet = N_alphabet
        self.benes_size = 2 ** int(np.ceil(np.log2(max(N_alphabet, modulus))))
        self.benes = BenesNetwork(self.benes_size)
        self.fanin_losses = {}

    def compute_permutation(self, weight_val: int) -> list:
        """
        Computes the permutation mapping for an invertible weight w where gcd(w, m) == 1.
        x -> (x * w) mod m for 0 <= x < m, and identity for padding channels.
        """
        pi = list(range(self.benes_size))
        w = int(weight_val) % self.modulus
        if math.gcd(w, self.modulus) == 1 and w != 0:
            for x in range(self.modulus):
                pi[x] = (x * w) % self.modulus
        return pi

    def multiply_accumulate(self, A_res: np.ndarray, B_res: np.ndarray) -> np.ndarray:
        """
        Computes optical spatial 1-hot tensor products C[i, j, k] = (A[i, k] * B[k, j]) % m
        using physical 1-hot waveguide routing and Beneš switch traversal in the active datapath.
        """
        A_mod = (A_res % self.modulus).astype(int)
        B_mod = (B_res % self.modulus).astype(int)
        unique_weights = np.unique(B_mod)

        # Build physical optical routing transfer response for all active weights
        optical_lut = {}
        for w in unique_weights:
            w_int = int(w)
            optical_lut[w_int] = np.zeros(self.modulus, dtype=int)

            if w_int == 0:
                # Optical zero-gating: redirects all light to channel 0
                optical_lut[w_int][:] = 0
            elif math.gcd(w_int, self.modulus) == 1:
                # Permutation routing through Beneš physical network
                pi = self.compute_permutation(w_int)
                self.benes.waksman_route(pi)

                # Route waveguide identity vector through physical switches
                waveguide_inputs = np.arange(self.benes_size)
                waveguide_outputs = self.benes.traverse(waveguide_inputs)

                # Physical photodetector array identifies which output port received light from input waveguide x:
                # In the Beneš fabric, output port y receives light from input pin waveguide_outputs[y].
                # Thus, input pin x arrives at output port where waveguide_outputs == x.
                for x in range(self.modulus):
                    detected_pin = int(np.where(waveguide_outputs == x)[0][0])
                    optical_lut[w_int][x] = detected_pin
            else:
                # Optical fan-in combiner for non-coprime residues (composite moduli)
                # Physical multi-mode interference (MMI) / directional combiner stage.
                # When gcd(w, m) = g > 1, exactly g distinct input waveguides map to each active output port.
                g = math.gcd(w_int, self.modulus)
                self.fanin_losses[w_int] = 10.0 * math.log10(g)
                # Optical transmission efficiency factor T = 1/g due to passive combining loss
                for x in range(self.modulus):
                    target_port = (x * w_int) % self.modulus
                    optical_lut[w_int][x] = target_port

        N_dim_i, N_dim_k = A_mod.shape
        _, N_dim_j = B_mod.shape
        C_products = np.zeros((N_dim_i, N_dim_j, N_dim_k), dtype=int)

        for j in range(N_dim_j):
            for k in range(N_dim_k):
                w_val = B_mod[k, j]
                lut = optical_lut[w_val]
                for i in range(N_dim_i):
                    a_val = A_mod[i, k]
                    C_products[i, j, k] = lut[a_val]

        return C_products


class SpatialOneHotAccelerator:
    """Master 16-Tile Monolithic Planar MVP Accelerator with Signed CMOS Accumulation."""

    def __init__(self, pure_prime: bool = False):
        self.mod_info = generate_moduli_set(pure_prime=pure_prime)
        self.moduli = self.mod_info["moduli_compute"]
        self.tiles = [SpatialOneHotTile(m) for m in self.moduli]

    def matmul(self, A_matrix: np.ndarray, B_matrix: np.ndarray) -> np.ndarray:
        """
        Executes bit-exact matrix multiplication supporting signed operands.
        1. Encodes signed inputs into residue channels modulo m_i.
        2. Routes spatial 1-hot signals through 16 optical tiles in parallel.
        3. Folds CRT reconstructed products into signed integer domain [-M/2, M/2 - 1].
        4. Accumulates signed values in 64-bit CMOS accumulator tree.
        """
        N_dim_i, N_dim_k = A_matrix.shape
        _, N_dim_j = B_matrix.shape
        C_products = []

        for t in range(cfg.N_tiles):
            m = self.moduli[t]
            A_res = A_matrix % m
            B_res = B_matrix % m
            C_products.append(self.tiles[t].multiply_accumulate(A_res, B_res))

        M_tot = self.mod_info["M_total"]
        C_out = np.zeros((N_dim_i, N_dim_j), dtype=object)

        for i in range(N_dim_i):
            for j in range(N_dim_j):
                cmos_acc = 0
                for k in range(N_dim_k):
                    elem_res = [C_products[t][i, j, k] for t in range(cfg.N_tiles)]
                    val = crt_reconstruct(
                        elem_res,
                        self.moduli,
                        self.mod_info["M_i"],
                        self.mod_info["N_i"],
                    )
                    # Signed-domain reconstruction fold
                    if val >= M_tot // 2:
                        val -= M_tot
                    cmos_acc += val
                C_out[i, j] = cmos_acc

        return C_out


if __name__ == "__main__":
    # Test a small Beneš to prove routing logic works
    b = BenesNetwork(8)
    test_pi = [7, 6, 5, 4, 3, 2, 1, 0]
    b.waksman_route(test_pi)
    routed_test = b.traverse(np.arange(8))
    print("Test routing 8x8 successfully traversed states:", b.switch_states.shape)
    for x in range(8):
        assert routed_test[test_pi[x]] == x

    acc = SpatialOneHotAccelerator()
    acc.tiles = [SpatialOneHotTile(m, 4) for m in acc.moduli]

    # Test with strictly signed operands (positive, negative, zero)
    np.random.seed(42)
    A = np.random.randint(-100, 100, size=(4, 4))
    B = np.random.randint(-100, 100, size=(4, 4))

    C_opt = acc.matmul(A, B)
    C_ref = np.matmul(A.astype(object), B.astype(object))
    diff = int(np.sum(np.abs(C_opt - C_ref)))
    print(f"Spatial One-Hot Signed Contraction Deviation: {diff} (PASS)" if diff == 0 else f"FAILED: {diff}")
    assert diff == 0, f"Signed matmul failed with deviation {diff}"

