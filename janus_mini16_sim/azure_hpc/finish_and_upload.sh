#!/usr/bin/env bash
# ==============================================================================
# PROJECT JANUS: FINISH & UPLOAD 1,000,000-RUN CAMPAIGN RESULTS
# ==============================================================================
set -euo pipefail

RESOURCE_GROUP="janus-hpc-rg"
VM_NAME="janus-hpc-standard-d4s-v5"
STORAGE_ACCOUNT="janushpc9919794"
CONTAINER_NAME="results"

echo "========================================================================"
echo "  PROJECT JANUS: FINISH & UPLOAD 1,000,000-RUN CAMPAIGN RESULTS"
echo "========================================================================"

echo "[*] Step 1: Querying storage credentials & checking for existing results..."
STORAGE_KEY=$(az storage account keys list --resource-group "${RESOURCE_GROUP}" --account-name "${STORAGE_ACCOUNT}" --query "[0].value" -o tsv)

BLOB_EXISTS=$(az storage blob exists --container-name "${CONTAINER_NAME}" --account-name "${STORAGE_ACCOUNT}" --name janus_1m_results.tar.gz --account-key "${STORAGE_KEY}" --query "exists" -o tsv 2>/dev/null || echo "false")

if [ "${BLOB_EXISTS}" = "true" ]; then
    echo "[+] SUCCESS: 'janus_1m_results.tar.gz' is already uploaded in Azure Storage!"
    echo "[*] Downloading results archive locally..."
    az storage blob download \
      --container-name "${CONTAINER_NAME}" \
      --account-name "${STORAGE_ACCOUNT}" \
      --name janus_1m_results.tar.gz \
      --file janus_1m_results.tar.gz \
      --account-key "${STORAGE_KEY}"
    echo "[+] Done! Results package downloaded successfully:"
    ls -lh janus_1m_results.tar.gz
    exit 0
fi

echo "[*] Step 2: Checking VM Power State..."
VM_STATE=$(az vm get-instance-view --name "${VM_NAME}" --resource-group "${RESOURCE_GROUP}" --query "instanceView.statuses[?starts_with(code, 'PowerState/')].displayStatus" -o tsv 2>/dev/null || echo "unknown")
echo "[*] Current VM State: ${VM_STATE}"

if [ "${VM_STATE}" != "VM running" ]; then
    echo "[*] Starting VM '${VM_NAME}' to execute upload..."
    az vm start --resource-group "${RESOURCE_GROUP}" --name "${VM_NAME}" --output table
fi

echo "[*] Step 3: Generating 7-day write SAS URL..."
SAS_EXPIRY=$(date -u -d "7 days" '+%Y-%m-%dT%H:%MZ' 2>/dev/null || date -u -v+7d '+%Y-%m-%dT%H:%MZ')
SAS_TOKEN=$(az storage container generate-sas --account-name "${STORAGE_ACCOUNT}" --name "${CONTAINER_NAME}" --account-key "${STORAGE_KEY}" --permissions rwl --expiry "${SAS_EXPIRY}" -o tsv)
BLOB_URL="https://${STORAGE_ACCOUNT}.blob.core.windows.net/${CONTAINER_NAME}/janus_1m_results.tar.gz?${SAS_TOKEN}"

echo "[*] Step 4: Executing figure generation and upload inside VM..."
cat << 'INNER_EOF' > /tmp/vm_finish_task.sh
source /opt/janus/venv/bin/activate
echo "[*] Generating Category C (Thermal FEM) & Category D (OFC Dashboards)..."
python3 /opt/janus/janus_mini16_sim/cloud_hpc/cloud_graph_generator.py --output-dir /opt/janus/output/cloud_figures --samples 1000000 --cycles 1000000

echo "[*] Packaging all 19 figures, logs, and artifacts..."
cd /opt/janus
tar -czvf /opt/janus_1m_results.tar.gz output/ janus_mini16_sim/output/ 2>/dev/null || tar -czvf /opt/janus_1m_results.tar.gz -C /opt/janus output/

echo "[*] Uploading completed archive to Azure Storage..."
curl -X PUT -T /opt/janus_1m_results.tar.gz -H "x-ms-blob-type: BlockBlob" "__BLOB_URL__"

echo "[*] Upload complete! Powering down VM to save credit..."
sudo shutdown -h now
INNER_EOF

sed -i "s|__BLOB_URL__|${BLOB_URL}|g" /tmp/vm_finish_task.sh

az vm run-command invoke \
  --resource-group "${RESOURCE_GROUP}" \
  --name "${VM_NAME}" \
  --command-id RunShellScript \
  --scripts "@/tmp/vm_finish_task.sh" \
  --query "value[0].message" -o tsv

echo "========================================================================"
echo "  [SUCCESS] All 19 figures uploaded to Azure Storage!"
echo "  Downloading results archive locally..."
echo "========================================================================"

az storage blob download \
  --container-name "${CONTAINER_NAME}" \
  --account-name "${STORAGE_ACCOUNT}" \
  --name janus_1m_results.tar.gz \
  --file janus_1m_results.tar.gz \
  --account-key "${STORAGE_KEY}"

echo "[+] Done! 'janus_1m_results.tar.gz' downloaded successfully."
ls -lh janus_1m_results.tar.gz
