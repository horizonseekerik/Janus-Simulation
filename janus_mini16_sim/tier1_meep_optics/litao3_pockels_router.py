"""
ALGORITHM 1C: LITAO3 POCKELS MODULATOR MEEP
===========================================
Simulates LiTaO3 Pockels MZ modulator using MEEP.
Extracts actual phase shifts to compute V_pi.
"""

import sys
import os
import math
import numpy as np

try:
    import meep as mp
    HAS_MEEP = True
except ImportError:
    HAS_MEEP = False

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from configs import mini_16t_constants as cfg

class LiTaO3PockelsModulatorMeep:
    def __init__(self):
        self.has_meep = HAS_MEEP
        self.L_active = cfg.L_active_um
        self.gap = cfg.gap_eo_nm / 1000.0
        self.resolution = 30
        
    def _run_sim_and_get_phase(self, voltage: float) -> float:
        d_n = 0.5 * (cfg.n_litao3**3) * cfg.r33_litao3 * (voltage / (self.gap * 1e-6))
        n_active = cfg.n_litao3 + d_n
        
        sx = 10.0
        sy = 3.0
        cell = mp.Vector3(sx, sy, 0)
        pml_layers = [mp.PML(1.0)]
        
        litao3_mat = mp.Medium(index=n_active)
        sio2 = mp.Medium(index=cfg.n_sio2)
        
        wg = mp.Block(mp.Vector3(mp.inf, 0.5, mp.inf), material=litao3_mat)
        
        lambda_0 = cfg.lambda_0_nm / 1000.0
        fcen = 1.0 / lambda_0
        
        src = mp.EigenModeSource(
            src=mp.GaussianSource(fcen, fwidth=0.1*fcen),
            center=mp.Vector3(-sx/2 + 1.5, 0, 0),
            size=mp.Vector3(0, 1.5, 0),
            eig_band=1,
            direction=mp.X
        )
        
        sim = mp.Simulation(
            cell_size=cell,
            boundary_layers=pml_layers,
            geometry=[wg],
            sources=[src],
            resolution=self.resolution,
            default_material=sio2
        )
        
        # Measure complex amplitude at the output
        mon = sim.add_mode_monitor(fcen, 0, 1, mp.FluxRegion(center=mp.Vector3(sx/2 - 1.5, 0, 0), size=mp.Vector3(0, 1.5, 0)))
        
        sim.run(until=60.0)
        
        res = sim.get_eigenmode_coefficients(mon, [1])
        alpha_forward = res.alpha[0, 0, 0] # forward mode amplitude
        phase = np.angle(alpha_forward)
        
        return phase

    def solve(self, voltage: float):
        if not HAS_MEEP:
            d_n = 0.5 * (cfg.n_litao3**3) * cfg.r33_litao3 * (voltage / (self.gap * 1e-6))
            lambda_0 = cfg.lambda_0_nm * 1e-9
            delta_phi = (2.0 * math.pi / lambda_0) * d_n * (self.L_active * 1e-6)
            v_pi = abs(voltage * (math.pi / max(delta_phi, 1e-18)))
            A = self.L_active * 1e-6 * 0.5e-6
            C_junction = cfg.epsilon_0 * (cfg.n_litao3**2) * A / (self.gap * 1e-6)
            bw = 1.0 / (2.0 * math.pi * cfg.R_eff * C_junction)
            return {
                "V_pi": float(v_pi),
                "C_junction": float(C_junction),
                "bandwidth": float(bw),
                "phase_shift_rad": float(delta_phi),
            }

        # Run at 0V and at `voltage` to get delta_phi
        phase_0 = self._run_sim_and_get_phase(0.0)
        phase_v = self._run_sim_and_get_phase(voltage)
        
        delta_phi = phase_v - phase_0
        
        # Unroll phase wrapping if necessary, though for 5V it shouldn't wrap in this short test length
        if delta_phi == 0:
            v_pi = float('inf')
        else:
            # The phase shift scales linearly with voltage and length. 
            # We ran a short length (sx=10, active region ~7um). We must scale delta_phi to the full L_active.
            sim_L = 10.0 - 3.0 # Exact propagation distance between source and monitor in the simulation
            
            # Sanity check: Ensure we haven't wrapped the phase in this short length
            assert abs(delta_phi) < math.pi * 0.9, f"Phase wrapped! (delta_phi={delta_phi:.3f} rad). V_pi extrapolation will be corrupted."
            
            scaled_delta_phi = delta_phi * (self.L_active / sim_L)
            
            # V_pi is the voltage required for a Pi phase shift
            v_pi = abs(voltage * (math.pi / scaled_delta_phi))
            
        A = self.L_active * 1e-6 * 0.5e-6
        C_junction = cfg.epsilon_0 * cfg.n_litao3**2 * A / (self.gap * 1e-6)
        bw = 1.0 / (2 * math.pi * cfg.R_eff * C_junction)
        
        return {
            "V_pi": v_pi,
            "C_junction": C_junction,
            "bandwidth": bw,
            "phase_shift_rad": delta_phi
        }

if __name__ == "__main__":
    solver = LiTaO3PockelsModulatorMeep()
    res = solver.solve(5.0)
    print(res)
