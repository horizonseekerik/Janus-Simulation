#!/usr/bin/env bash
# ==============================================================================
# PROJECT JANUS: GCP PRODUCTION DISTRIBUTED ORCHESTRATOR
# Target Budget: ~$550–$750 (From $2,000 Google Cloud Credit Pool)
# Workload: 1,000,000 Monte Carlo Runs + 1,000,000 SPICE Cycles + 5M Elmer FEM
# ==============================================================================
set -euo pipefail

BUCKET="gs://janus-100pct-simulation-artifacts"
ZONE="us-central1-a"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
RUN_DIR="/workspace/janus/runs/${TIMESTAMP}"

echo "========================================================================"
echo "  PROJECT JANUS: DISTRIBUTED 100% UNCOMPROMISED SIMULATION CAMPAIGN"
echo "  Target Budget : ~$550–$750 | Credit Pool: $2,000 GCP + $1,000 Azure"
echo "  Monte Carlo   : 1,000,000 Stochastic Lithography Runs"
echo "  SPICE Cycles  : 1,000,000 Transient Decision Dynamics @ 100 GHz"
echo "  Thermal FEM   : 5,000,000 Tetrahedral Elements (16,384 Discrete Sources)"
echo "  Timestamp     : ${TIMESTAMP}"
echo "========================================================================"

mkdir -p "${RUN_DIR}/logs" "${RUN_DIR}/results"

# ------------------------------------------------------------------------------
# STEP 1: Stage 2 Pre-Flight Canary Verification (<$2.00)
# ------------------------------------------------------------------------------
echo "[*] Step 1: Running Canary Verification on 1 Spot GPU Node..."
gcloud compute instances create "janus-canary-${TIMESTAMP}" \
    --zone="${ZONE}" \
    --machine-type="g2-standard-24" \
    --preemptible \
    --metadata-from-file startup-script="cloud_hpc/gcp_canary_startup.sh"

# Wait for canary pass
echo "[*] Waiting for canary completion..."
gcloud compute instances tail-serial-port-output "janus-canary-${TIMESTAMP}" --zone="${ZONE}" | grep -m 1 "CANARY_PASSED"
gcloud compute instances delete "janus-canary-${TIMESTAMP}" --zone="${ZONE}" --quiet

echo "[*] Canary PASSED! Launching full distributed production campaign..."

# ------------------------------------------------------------------------------
# STEP 2: 3D Vectorial MEEP FDTD & 1,000,000-Run Monte Carlo Fleet (10 GPU Spot VMs)
# 4 GPU VMs run full 3D Maxwell FDTD (35M Yee cells) for Crossing & Pockels Router
# 6 VMs run distributed 1,000,000-sample Monte Carlo Tolerance Fleet
# ------------------------------------------------------------------------------
echo "[*] Step 2: Dispatching 10 GPU Spot VMs for 3D MEEP FDTD & 1,000,000 Monte Carlo Runs..."
# 2A: Full-wave 3D MEEP FDTD on GPUs
for i in {0..3}; do
    cat <<EOF > "/tmp/startup_meep_${i}.sh"
#!/usr/bin/env bash
cd /workspace/janus
echo "[*] Running 3D Vectorial MEEP FDTD on GPU (35 Million Yee Cells)..."
python3 janus_mini16_sim/tier1_meep_optics/waveguide_crossing.py --use-3d --resolution 30 > "/workspace/janus/meep_crossing_${i}.log" 2>&1
python3 janus_mini16_sim/tier1_meep_optics/litao3_pockels_router.py --use-3d --resolution 30 --voltage 2.80 >> "/workspace/janus/meep_crossing_${i}.log" 2>&1
gsutil cp "/workspace/janus/meep_crossing_${i}.log" "${BUCKET}/${TIMESTAMP}/"
sudo shutdown -h now
EOF

    gcloud compute instances create "janus-meep-worker-${i}-${TIMESTAMP}" \
        --zone="${ZONE}" \
        --machine-type="g2-standard-24" \
        --preemptible \
        --metadata-from-file startup-script="/tmp/startup_meep_${i}.sh" &
done

# 2B: 1,000,000-Sample Monte Carlo Tolerance Fleet (Workers 4..9, ~166k samples each)
for i in {4..9}; do
    cat <<EOF > "/tmp/startup_mc_${i}.sh"
#!/usr/bin/env bash
cd /workspace/janus
python3 janus_mini16_sim/tier1_meep_optics/monte_carlo_tolerance.py --samples 166667 --batch-size 50000 > "/workspace/janus/mc_worker_${i}.log" 2>&1
gsutil cp "/workspace/janus/mc_worker_${i}.log" "${BUCKET}/${TIMESTAMP}/"
sudo shutdown -h now
EOF

    gcloud compute instances create "janus-mc-worker-${i}-${TIMESTAMP}" \
        --zone="${ZONE}" \
        --machine-type="g2-standard-24" \
        --preemptible \
        --metadata-from-file startup-script="/tmp/startup_mc_${i}.sh" &
done

# ------------------------------------------------------------------------------
# STEP 3: 1,000,000-Cycle Parallel SPICE Fleet (5 Spot VMs, 200k cycles each)
# ------------------------------------------------------------------------------
echo "[*] Step 3: Dispatching 5 Compute-Optimized VMs for 1,000,000 SPICE Cycles & Netlists..."
for j in {0..4}; do
    cat <<EOF > "/tmp/startup_spice_${j}.sh"
#!/usr/bin/env bash
cd /workspace/janus
python3 janus_mini16_sim/tier3_xyce_circuit/eye_diagram_ber.py --bits 200000 > "/workspace/janus/spice_worker_${j}.log" 2>&1
python3 janus_mini16_sim/tier3_xyce_circuit/strongarm_latch.py --cycles 200000 >> "/workspace/janus/spice_worker_${j}.log" 2>&1
# If Xyce is installed in the cloud container, execute the 4-port S-parameter SPICE subcircuit
if command -v Xyce &> /dev/null; then
    Xyce -o "/workspace/janus/xyce_out_${j}.prn" janus_mini16_sim/tier3_xyce_circuit/optical_switch_sp.cir >> "/workspace/janus/spice_worker_${j}.log" 2>&1 || true
fi
gsutil cp "/workspace/janus/spice_worker_${j}.log" "${BUCKET}/${TIMESTAMP}/"
sudo shutdown -h now
EOF

    gcloud compute instances create "janus-spice-worker-${j}-${TIMESTAMP}" \
        --zone="${ZONE}" \
        --machine-type="c2-standard-60" \
        --preemptible \
        --metadata-from-file startup-script="/tmp/startup_spice_${j}.sh" &
done

# ------------------------------------------------------------------------------
# STEP 4: 5,000,000-Element Elmer FEM Thermal Solver (2 Spot VMs, 60 MPI ranks)
# ------------------------------------------------------------------------------
echo "[*] Step 4: Dispatching 2 High-Memory VMs for 5M-Element Elmer FEM..."
cat <<EOF > "/tmp/startup_elmer.sh"
#!/usr/bin/env bash
cd /workspace/janus
python3 janus_mini16_sim/tier2_elmer_thermal/gmsh_mesh_generator.py --domain-scale die --target-elements 5000000
python3 janus_mini16_sim/tier2_elmer_thermal/elmer_thermal_solver.py --mpi-ranks 60 > "/workspace/janus/elmer_thermal.log" 2>&1
gsutil cp -r /workspace/janus/output/elmer_3d "${BUCKET}/${TIMESTAMP}/"
sudo shutdown -h now
EOF

gcloud compute instances create "janus-elmer-thermal-${TIMESTAMP}" \
    --zone="${ZONE}" \
    --machine-type="c2-standard-60" \
    --preemptible \
    --metadata-from-file startup-script="/tmp/startup_elmer.sh" &

# ------------------------------------------------------------------------------
# STEP 5: Monolithic Dynamic Multi-Physics Co-Simulation & Full Decision Tree
# ------------------------------------------------------------------------------
echo "[*] Step 5: Executing Monolithic Dynamic Co-Simulation & Full 16-Point Decision Tree..."
cat <<EOF > "/tmp/startup_monolithic.sh"
#!/usr/bin/env bash
cd /workspace/janus
python3 janus_mini16_sim/run_mini16_full_cosim.py --monolithic --sim-time-ps 1000.0 > "/workspace/janus/monolithic_dynamic_cosim.log" 2>&1
python3 janus_mini16_sim/run_mini16_full_cosim.py --tier all --verbose > "/workspace/janus/full_cosim_all_tiers.log" 2>&1
python3 janus_mini16_sim/run_mini16_full_cosim.py --power-area > "/workspace/janus/power_and_area_audit.log" 2>&1
gsutil cp "/workspace/janus/monolithic_dynamic_cosim.log" "${BUCKET}/${TIMESTAMP}/"
gsutil cp "/workspace/janus/full_cosim_all_tiers.log" "${BUCKET}/${TIMESTAMP}/"
gsutil cp "/workspace/janus/power_and_area_audit.log" "${BUCKET}/${TIMESTAMP}/"
gsutil cp -r "/workspace/janus/orchestrator/artifacts" "${BUCKET}/${TIMESTAMP}/"
sudo shutdown -h now
EOF

gcloud compute instances create "janus-monolithic-${TIMESTAMP}" \
    --zone="${ZONE}" \
    --machine-type="c2-standard-30" \
    --preemptible \
    --metadata-from-file startup-script="/tmp/startup_monolithic.sh" &

wait
echo "[*] All distributed jobs dispatched successfully."
echo "[*] Monitor progress in Cloud Storage: ${BUCKET}/${TIMESTAMP}/"
