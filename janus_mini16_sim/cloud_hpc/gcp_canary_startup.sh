#!/usr/bin/env bash
# ==============================================================================
# PROJECT JANUS: GCP CANARY STARTUP & PRE-FLIGHT VALIDATION SCRIPT
# Budget: <$2.00 (Single Spot VM: g2-standard-24 or c2-standard-30)
# ==============================================================================
set -euo pipefail

echo "========================================================================"
echo "  PROJECT JANUS: STAGE 2 CLOUD CANARY PRE-FLIGHT VERIFICATION"
echo "  Timestamp: $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
echo "========================================================================"

WORKSPACE="/workspace/janus"
mkdir -p "${WORKSPACE}/logs"
cd "${WORKSPACE}"

# 1. System Environment & GPU/CPU Check
echo "[1/5] Auditing compute hardware & environment..."
nproc || true
nvidia-smi || echo "[INFO] Non-GPU node detected; proceeding in CPU mode."

# 2. Python Dependencies Verification
echo "[2/5] Checking Python scientific packages..."
python3 -c "import numpy, scipy, matplotlib, z3; print(f'NumPy: {numpy.__version__}, SciPy: {scipy.__version__}, Z3: {z3.__version__}')"
python3 -c "import meep; print(f'MEEP: {meep.__version__}')" || echo "[INFO] MEEP not detected in host python; using compact mode."

# 3. Canary Test: 3D Waveguide Crossing & LiTaO3 Router Dry-Run
echo "[3/5] Running Tier 1 3D Optics Canary Test..."
python3 janus_mini16_sim/tier1_meep_optics/waveguide_crossing.py --use-3d --dry-run
python3 janus_mini16_sim/tier1_meep_optics/litao3_pockels_router.py --use-3d --dry-run
python3 janus_mini16_sim/tier1_meep_optics/monte_carlo_tolerance.py --dry-run

# 4. Canary Test: 3D Elmer FEM Thermal Mesh & 1M-Cycle SPICE Generator
echo "[4/5] Running Tier 2 & 3 Multi-Physics Canary Tests..."
python3 janus_mini16_sim/tier2_elmer_thermal/gmsh_mesh_generator.py --dry-run
python3 janus_mini16_sim/tier2_elmer_thermal/elmer_thermal_solver.py --dry-run
python3 janus_mini16_sim/tier3_xyce_circuit/strongarm_latch.py --dry-run
python3 janus_mini16_sim/tier3_xyce_circuit/eye_diagram_ber.py --dry-run

# 5. Canary Test: Monolithic Dynamic Multi-Physics Co-Simulation
echo "[5/5] Running Monolithic Dynamic Co-Simulation Canary..."
python3 janus_mini16_sim/run_mini16_full_cosim.py --monolithic --sim-time-ps 200.0

# 6. Emit Canary Pass Signal
echo "All Canary unit checks completed successfully!"
echo "CANARY_PASSED"

# Auto-shutdown to prevent credit leakage
echo "Shutting down canary instance..."
sudo shutdown -h now
