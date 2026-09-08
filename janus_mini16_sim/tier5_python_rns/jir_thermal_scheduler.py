"""
ALGORITHM 5D: JIR_THERMAL_SCHEDULER
===================================
Thermal-priority scheduler with basic JIR residue channel remapping and
nearest-neighbor cross-tile thermal diffusion across a 4x4 planar tile grid.
Simulates closed-loop thermal tracking and rotational tile cooling.
"""

import sys
import os
import math
import numpy as np
from typing import Dict, List, Any

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from configs import mini_16t_constants as cfg

MODULI_LIST = [256, 251, 243, 241, 239, 233, 229, 227, 223, 211, 199, 197, 193, 191, 181, 179]


class JIRThermalScheduler:
    """Thermal-priority scheduler with basic JIR residue channel remapping
    and nearest-neighbor cross-tile thermal diffusion across a 4x4 planar tile grid.
    """

    def __init__(
        self,
        N_tiles: int = cfg.N_tiles,
        tau_jir: float = cfg.tau_jir,
        P_per_tile: float = cfg.P_per_tile,
        T_ambient: float = cfg.T_ambient_C,
        T_max_operating: float = cfg.T_max_operating,
        T_crystallization_guard: float = cfg.T_crystallization_guard,
        G_cross: float = 0.005,
    ):
        self.N_tiles = N_tiles
        self.tau_jir = tau_jir
        self.P_per_tile = P_per_tile
        self.T_ambient = T_ambient
        self.T_max_operating = T_max_operating
        self.T_guard = T_crystallization_guard
        self.G_cross = G_cross
        self.moduli_list = list(MODULI_LIST)

        # 5-pole Foster RC model for SiO2/SiPh stack
        self.R_poles = [0.12, 0.08, 0.05, 0.03, 0.02]  # K/W
        self.tau_poles = [69.06e-3, 15.0e-3, 3.0e-3, 0.5e-3, 0.05e-3]  # s
        self.R_total = sum(self.R_poles)

        self.delta_T_poles = np.zeros((self.N_tiles, len(self.R_poles)), dtype=np.float64)
        self.temperatures = np.full(self.N_tiles, self.T_ambient, dtype=np.float64)
        self.violations = 0
        self.residue_map = {i: MODULI_LIST[i] for i in range(min(self.N_tiles, len(MODULI_LIST)))}

    def step_epoch(self, active_mask: List[bool], dt: float = None):
        """Advances thermal dynamics by one epoch using exact exponential integration.
        Conductive heat flux between adjacent planar tiles is coupled into each tile's
        dynamic power state so cross-tile diffusion accumulates and persists across epochs.
        """
        if dt is None:
            dt = self.tau_jir

        # 1. Compute net conductive heat flux from adjacent tiles (4-neighbor grid)
        q_diff = np.zeros(self.N_tiles, dtype=np.float64)
        for t in range(self.N_tiles):
            row, col = t // 4, t % 4
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = row + dr, col + dc
                if 0 <= nr < 4 and 0 <= nc < 4:
                    neighbor = nr * 4 + nc
                    q_diff[t] += self.G_cross * (self.temperatures[neighbor] - self.temperatures[t])

        # 2. Integrate multi-pole RC thermal response with persistent cross-tile flux
        for t in range(self.N_tiles):
            # Effective input power = active compute heat + conductive flux from neighbors
            p_in = (self.P_per_tile if active_mask[t] else 0.0) + q_diff[t]
            p_in = max(0.0, p_in)

            for n, (R_n, tau_n) in enumerate(zip(self.R_poles, self.tau_poles)):
                decay = math.exp(-dt / tau_n)
                self.delta_T_poles[t, n] = self.delta_T_poles[t, n] * decay + p_in * R_n * (1.0 - decay)

            self.temperatures[t] = self.T_ambient + np.sum(self.delta_T_poles[t])

        for t in range(self.N_tiles):
            if self.temperatures[t] > self.T_max_operating:
                self.violations += 1

    def run_workload_simulation(
        self,
        total_epochs: int = 5000,
        active_count: int = 8,
        dwell_epochs: int = 250,
        T_trigger_delta: float = 15.0,
    ) -> Dict[str, Any]:
        """Runs a closed-loop JIR thermal-priority scheduler with active residue channel remapping.
        
        Parameters:
        -----------
        total_epochs : int
            Total simulation epochs.
        active_count : int
            Number of compute residue channels required by the workload (e.g. 8 for INT32).
        dwell_epochs : int
            Maximum epochs a tile computes before JIR thermal rotation swaps it with an idle reserve tile.
        T_trigger_delta : float
            Temperature rise above ambient at which emergency JIR rotation triggers.
        """
        self.temperatures.fill(self.T_ambient)
        self.delta_T_poles.fill(0.0)
        self.violations = 0
        jir_remaps = 0

        # Physical tile to assigned residue channel mapping
        # First active_count tiles initially host the active compute channels
        self.residue_map = {i: MODULI_LIST[i] if i < active_count else None for i in range(self.N_tiles)}
        active_tiles = set(range(active_count))
        tile_active_duration = np.zeros(self.N_tiles, dtype=int)

        max_T_recorded = self.T_ambient
        history = []
        T_rot_trigger = min(self.T_max_operating - 2.0, self.T_ambient + T_trigger_delta)

        for epoch in range(total_epochs):
            # Check for active tiles requiring JIR thermal rotation
            # A tile rotates if:
            # 1. Its temperature crosses T_rot_trigger, OR
            # 2. It has computed continuously for dwell_epochs (preventive wear-leveling)
            candidates_to_rotate = []
            for t in active_tiles:
                if self.temperatures[t] >= T_rot_trigger or tile_active_duration[t] >= dwell_epochs:
                    candidates_to_rotate.append(t)

            # Rotate hottest active tiles first
            candidates_to_rotate.sort(key=lambda t: self.temperatures[t], reverse=True)

            # Identify cool idle reserve tiles (coldest first)
            idle_tiles = [t for t in range(self.N_tiles) if t not in active_tiles]
            idle_tiles.sort(key=lambda t: self.temperatures[t])

            for hot_tile in candidates_to_rotate:
                if idle_tiles:
                    cool_tile = idle_tiles.pop(0)
                    # Remap residue channel from hot_tile to cool_tile
                    channel = self.residue_map[hot_tile]
                    self.residue_map[hot_tile] = None
                    self.residue_map[cool_tile] = channel
                    active_tiles.remove(hot_tile)
                    active_tiles.add(cool_tile)
                    tile_active_duration[hot_tile] = 0
                    tile_active_duration[cool_tile] = 0
                    jir_remaps += 1

            # Update active duration counters
            for t in active_tiles:
                tile_active_duration[t] += 1
            for t in range(self.N_tiles):
                if t not in active_tiles:
                    tile_active_duration[t] = 0

            active_mask = [t in active_tiles for t in range(self.N_tiles)]
            self.step_epoch(active_mask)

            current_max = np.max(self.temperatures)
            max_T_recorded = max(max_T_recorded, current_max)
            history.append(current_max)

        return {
            "total_epochs": total_epochs,
            "simulated_time_ms": total_epochs * self.tau_jir * 1e3,
            "max_temperature_C": float(max_T_recorded),
            "min_temperature_C": float(np.min(self.temperatures)),
            "steady_state_avg_C": float(np.mean(history[-min(len(history), 1000):])),
            "thermal_violations": self.violations,
            "jir_remaps": jir_remaps,
            "active_tile_count": len(active_tiles),
            "pass_operating_limit": bool(max_T_recorded <= self.T_max_operating),
            "pass_crystallization_guard": bool(max_T_recorded < self.T_guard),
        }


if __name__ == "__main__":
    scheduler = JIRThermalScheduler()
    res = scheduler.run_workload_simulation(total_epochs=2000, active_count=8)
    print("=" * 60)
    print("JANUS MINI 16-TILE: JIR THERMAL SCHEDULER SIMULATION")
    print("=" * 60)
    for k, v in res.items():
        print(f"  {k:28s}: {v}")
    print("=" * 60)
    print("Simulation status: PASS" if res["pass_operating_limit"] and res["thermal_violations"] == 0 else "Simulation status: FAIL")
