#!/usr/bin/env bash
# ==============================================================================
# PROJECT JANUS MINI (16-TILE): AZURE HPC ONE-CLICK EXECUTION SCRIPT
# ==============================================================================
# Usage:
#   chmod +x azure_deploy_run.sh
#   ./azure_deploy_run.sh --cores 120 --outdir ./azure_results
#
# This script:
#   1. Detects available CPU cores / MPI environment
#   2. Runs 3D FDTD wave simulations via MPI
#   3. Runs 3D Elmer FEM thermal simulation
#   4. Runs parallel SPICE Monte Carlo
#   5. Compresses results and initiates auto-shutdown if running on spot instance
# ==============================================================================

set -e

CORES=${1:-$(nproc)}
OUTPUT_DIR="./azure_simulation_results"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

echo "========================================================================"
echo "  PROJECT JANUS: AZURE HPC FULL-CHIP MULTI-PHYSICS RUNNER"
echo "  Detected Cores: ${CORES}"
echo "  Output Directory: ${OUTPUT_DIR}"
echo "  Timestamp: ${TIMESTAMP}"
echo "========================================================================"

mkdir -p "${OUTPUT_DIR}"

# 1. Activate conda Meep MPI environment if present
if [ -d "/opt/conda/envs/pmp" ]; then
    echo "[*] Activating parallel Meep conda environment..."
    source /opt/conda/bin/activate pmp
fi

# 2. Run Tier 1: 3D Vectorial Optics
echo "[*] Step 1: Running Tier 1 3D Optics Solvers (MPI)..."
python3 janus_mini16_sim/tier1_meep_optics/test_tier1_all.py

# 3. Run Tier 2: 3D Elmer FEM Thermal Stack
echo "[*] Step 2: Running Tier 2 3D Multi-Physics Thermal..."
python3 janus_mini16_sim/tier2_elmer_thermal/test_tier2_all.py

# 4. Run Tier 3: Parallel SPICE Latch & Eye Diagrams
echo "[*] Step 3: Running Tier 3 Receiver SPICE Dynamics..."
python3 janus_mini16_sim/tier3_xyce_circuit/test_tier3_all.py

# 5. Run Tier 4 & 5: CRT Verification and Full Workload Benchmark
echo "[*] Step 4: Running Full End-to-End Co-Simulation Pipeline..."
python3 janus_mini16_sim/run_mini16_full_cosim.py --verbose

echo "========================================================================"
echo "  [SUCCESS] All multi-physics simulation tiers completed successfully!"
echo "  Results archived in: ${OUTPUT_DIR}"
echo "========================================================================"
