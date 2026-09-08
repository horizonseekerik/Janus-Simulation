import sys
import os
import math
import numpy as np
from typing import Dict, Any

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from configs import mini_16t_constants as cfg

class StrongArmLatchModel:
    """StrongARM latch physical model."""

    def __init__(self,
                 V_dd: float = 0.8,
                 I_bias: float = 400e-6):
        self.V_dd = V_dd
        self.C_p = cfg.C_p_strongarm
        self.C_L = 31.25e-18 # Derived effective load capacitance
        self.g_m = cfg.g_m_latch
        self.I_bias = I_bias
        self.f_clk = cfg.f_clk

    def simulate_decision(self, I_diff_A: float, noise_sigma_A: float) -> Dict[str, Any]:
        """
        Simulates physical model of StrongARM latch with numerical non-linear ODE integration
        governing the cross-coupled regenerative amplification phase:
          C_L * d(Delta_V)/dt = g_m * Delta_V * (1 - (Delta_V / V_dd)^2)
        """
        from scipy.integrate import solve_ivp
        net_diff_current = I_diff_A + np.random.normal(0, noise_sigma_A)
        
        # 1. Integration phase: accumulates differential voltage across sensing capacitance C_p
        t_int_window = cfg.t_int_strongarm
        V_offset_init = (net_diff_current * t_int_window) / self.C_p
        # Ensure finite non-zero initial offset for numerical stability
        sign = 1.0 if V_offset_init >= 0 else -1.0
        V_offset = sign * max(abs(V_offset_init), 1e-6)
        V_offset = sign * min(abs(V_offset), self.V_dd * 0.5)
        
        # 2. Regeneration phase: Numerical ODE integration of non-linear cross-coupled pair
        tau_regen = self.C_L / self.g_m
        
        def regen_ode(t, y):
            v_diff = y[0]
            # Non-linear transconductance saturation as outputs approach supply rails
            sat_factor = max(0.0, 1.0 - (abs(v_diff) / self.V_dd)**2)
            return [(self.g_m / self.C_L) * v_diff * sat_factor]
            
        t_max_regen = 10.0 * tau_regen
        sol = solve_ivp(regen_ode, [0, t_max_regen], [V_offset], method='RK45', max_step=0.1*tau_regen)
        
        # Detect time to reach 90% rail-to-rail decision threshold
        v_traj = sol.y[0]
        t_traj = sol.t
        v_thresh = 0.90 * self.V_dd
        idx_decision = np.where(np.abs(v_traj) >= v_thresh)[0]
        if len(idx_decision) > 0:
            t_regeneration = float(t_traj[idx_decision[0]])
        else:
            # Analytical asymptotic fallback if threshold not crossed in window
            t_regeneration = float(tau_regen * math.log(self.V_dd / max(abs(V_offset), 1e-9)))
            
        t_setup = getattr(cfg, "t_setup", 1.0e-12)
        t_total = t_int_window + t_regeneration + t_setup  # Slew & setup time
        
        # Metastability probability: P_meta = f_clk * t_window * exp(-t_avail / tau_regen)
        t_avail = max(0.0, cfg.T_cycle - t_int_window - t_setup)
        P_meta = float(self.f_clk * t_setup * math.exp(-t_avail / tau_regen))
        
        # Energy = C_L * V_dd^2 (dynamic) + I_bias * V_dd * t_cycle (static)
        E_dyn = self.C_L * (self.V_dd**2)
        E_stat = self.I_bias * self.V_dd * cfg.T_cycle
        E_total = E_dyn + E_stat
        
        decision = 1 if net_diff_current > 0 else 0
        if t_total > cfg.T_cycle:
            decision = int(np.random.randint(0, 2))
            
        return {
            "decision": decision,
            "t_total_ps": float(t_total * 1e12),
            "t_regen_ps": float(t_regeneration * 1e12),
            "t_regen_ode_ps": float(t_regeneration * 1e12),
            "E_decision_aJ": float(E_total * 1e18),
            "P_meta": P_meta,
            "pass_regen_time": bool(t_regeneration <= 4.0e-12),
            "pass_cycle_budget": bool(t_total <= cfg.T_cycle),
        }

if __name__ == "__main__":
    latch = StrongArmLatchModel()
    print(latch.simulate_decision(50e-6, cfg.sigma_latch_noise))
