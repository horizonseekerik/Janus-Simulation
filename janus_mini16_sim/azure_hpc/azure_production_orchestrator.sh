#!/usr/bin/env bash
# ==============================================================================
# PROJECT JANUS: AZURE PRODUCTION CLOUD HPC ORCHESTRATOR
# Budget: < $10.00 (from your $200 Azure Credit)
# Workload: 1,000,000 Monte Carlo Runs + 1,000,000 SPICE Cycles + 5M Elmer FEM
# Generates: 19 High-Resolution Publication Figures & OFC 3-Page Dashboard
# ==============================================================================
set -euo pipefail

RESOURCE_GROUP="janus-hpc-rg"
LOCATION="eastus"
CONTAINER_NAME="results"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

echo "========================================================================"
echo "  PROJECT JANUS: AZURE HPC 1,000,000-RUN PRODUCTION CAMPAIGN"
echo "  Target Budget  : < \$10.00 (from \$200 credit)"
echo "  Strategy       : Auto-fallback across high-speed SKUs & regions"
echo "  Timestamp      : ${TIMESTAMP}"
echo "========================================================================"

# 1. Create Resource Group
echo "[*] Step 1: Creating Azure Resource Group..."
az group create --name "${RESOURCE_GROUP}" --location "${LOCATION}" --output table

# 2. Re-use or Create Storage Account for Artifacts & Figures
echo "[*] Step 2: Preparing Azure Storage Account for results..."
EXISTING_STORAGE=$(az storage account list --resource-group "${RESOURCE_GROUP}" --query "[0].name" --output tsv 2>/dev/null || true)
if [ -n "${EXISTING_STORAGE}" ] && [ "${EXISTING_STORAGE}" != "None" ]; then
    STORAGE_ACCOUNT="${EXISTING_STORAGE}"
    echo "[*] Reusing existing Storage Account: ${STORAGE_ACCOUNT}"
else
    STORAGE_ACCOUNT="janushpc$(date +%s | tail -c 8)"
    echo "[*] Creating new Storage Account: ${STORAGE_ACCOUNT}..."
    az storage account create \
        --name "${STORAGE_ACCOUNT}" \
        --resource-group "${RESOURCE_GROUP}" \
        --location "${LOCATION}" \
        --sku Standard_LRS \
        --output table
fi

STORAGE_KEY=$(az storage account keys list --resource-group "${RESOURCE_GROUP}" --account-name "${STORAGE_ACCOUNT}" --query "[0].value" --output tsv)
az storage container create --name "${CONTAINER_NAME}" --account-name "${STORAGE_ACCOUNT}" --account-key "${STORAGE_KEY}" --output table

# Generate 7-day write SAS token for hands-free background upload
SAS_EXPIRY=$(date -u -d "7 days" '+%Y-%m-%dT%H:%MZ' 2>/dev/null || date -u -v+7d '+%Y-%m-%dT%H:%MZ')
SAS_TOKEN=$(az storage container generate-sas --account-name "${STORAGE_ACCOUNT}" --name "${CONTAINER_NAME}" --account-key "${STORAGE_KEY}" --permissions rwl --expiry "${SAS_EXPIRY}" --output tsv)
BLOB_UPLOAD_URL="https://${STORAGE_ACCOUNT}.blob.core.windows.net/${CONTAINER_NAME}/janus_1m_results.tar.gz?${SAS_TOKEN}"

# 3. Create Cloud Startup Script (Runs 100% in Background inside the VM)
cat <<EOF > /tmp/azure_janus_startup.sh
#!/usr/bin/env bash
set -e
export DEBIAN_FRONTEND=noninteractive

echo "[*] Updating system packages & installing dependencies..."
apt-get update -y
apt-get install -y git python3 python3-pip python3-venv libopenmpi-dev openmpi-bin gmsh curl

cd /opt
git clone https://github.com/horizonseekerik/janus-photonic-hardware.git janus
cd /opt/janus

python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install numpy scipy matplotlib sympy pytest

mkdir -p /opt/janus/output/cloud_figures /opt/janus/janus_mini16_sim/output /opt/janus/janus_mini16_sim/orchestrator/artifacts

echo "[*] Step 1: Running 1,000,000-Sample Monte Carlo Tolerance with 7 Figures..."
python3 janus_mini16_sim/tier1_meep_optics/monte_carlo_tolerance.py --samples 1000000 --batch-size 250000 --export-graphs --graph-dir /opt/janus/output/cloud_figures > /opt/janus/output/mc_1m.log 2>&1

echo "[*] Step 2: Running 1,000,000-Cycle 100 GHz SPICE Eye & BER with 6 Figures..."
python3 janus_mini16_sim/tier3_xyce_circuit/eye_diagram_ber.py --bits 1000000 --export-graphs --graph-dir /opt/janus/output/cloud_figures > /opt/janus/output/spice_1m.log 2>&1

echo "[*] Step 3: Running Full 5-Tier Co-Simulation & Decision Tree..."
python3 janus_mini16_sim/run_mini16_full_cosim.py --all > /opt/janus/output/full_cosim.log 2>&1

echo "[*] Step 4: Generating All 19 Publication-Grade Scientific Figures & OFC Dashboards..."
python3 janus_mini16_sim/cloud_hpc/cloud_graph_generator.py --output-dir /opt/janus/output/cloud_figures --samples 1000000 --cycles 1000000 > /opt/janus/output/cloud_graphs.log 2>&1

echo "[*] Compressing all figures, logs, and artifacts..."
cd /opt/janus
tar -czvf /opt/janus_1m_results.tar.gz output/ janus_mini16_sim/output/ janus_mini16_sim/orchestrator/artifacts/

echo "[*] Uploading completed archive directly to Azure Storage Container..."
curl -X PUT -T /opt/janus_1m_results.tar.gz -H "x-ms-blob-type: BlockBlob" "${BLOB_UPLOAD_URL}"

echo "[*] All simulations finished and uploaded to Azure Storage! Shutting down VM to save credit..."
sudo shutdown -h now
EOF

# 4. Launch Azure VM with intelligent multi-SKU and multi-region fallback
echo "[*] Step 3: Launching Azure VM with automatic SKU & region fallback..."

CANDIDATE_SIZES=(
    "Standard_F4s_v2"
    "Standard_D4s_v4"
    "Standard_D4s_v3"
    "Standard_B4as_v2"
    "Standard_D4as_v5"
    "Standard_B2ms"
    "Standard_F2s_v2"
)

REGIONS=("eastus" "eastus2" "centralus")

VM_LAUNCHED=false
FINAL_VM_NAME=""
FINAL_REGION=""
FINAL_SIZE=""

for REG in "${REGIONS[@]}"; do
    for SIZE in "${CANDIDATE_SIZES[@]}"; do
        CURRENT_VM_NAME="janus-hpc-$(echo "${SIZE}" | tr '_' '-' | tr '[:upper:]' '[:lower:]')"
        echo "[*] Attempting deployment: ${SIZE} in ${REG} (VM: ${CURRENT_VM_NAME})..."
        
        if az vm create \
            --resource-group "${RESOURCE_GROUP}" \
            --name "${CURRENT_VM_NAME}" \
            --image Ubuntu2204 \
            --size "${SIZE}" \
            --location "${REG}" \
            --admin-username azureuser \
            --generate-ssh-keys \
            --custom-data /tmp/azure_janus_startup.sh \
            --output table; then
            
            echo "[+] SUCCESS: VM '${CURRENT_VM_NAME}' (${SIZE}) launched in ${REG}!"
            VM_LAUNCHED=true
            FINAL_VM_NAME="${CURRENT_VM_NAME}"
            FINAL_REGION="${REG}"
            FINAL_SIZE="${SIZE}"
            break 2
        else
            echo "[-] SKU ${SIZE} unavailable in ${REG}. Trying next candidate..."
            az vm delete --resource-group "${RESOURCE_GROUP}" --name "${CURRENT_VM_NAME}" --yes --no-wait >/dev/null 2>&1 || true
        fi
    done
done

if [ "${VM_LAUNCHED}" = false ]; then
    echo "[!] ERROR: All candidate VM sizes and regions exhausted. Please check subscription quotas."
    exit 1
fi

echo "========================================================================"
echo "  [LAUNCHED] Azure HPC VM (${FINAL_SIZE} in ${FINAL_REGION}) is running!"
echo "  VM Name        : ${FINAL_VM_NAME}"
echo "  Storage URL    : https://${STORAGE_ACCOUNT}.blob.core.windows.net/${CONTAINER_NAME}/"
echo "  Monitor with   : az vm get-instance-view --name ${FINAL_VM_NAME} --resource-group ${RESOURCE_GROUP} --output table"
echo "  To delete when done: az group delete --name ${RESOURCE_GROUP} --yes --no-wait"
echo "========================================================================"
