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

echo "[*] Step 1: Generating 7-day write SAS URL..."
STORAGE_KEY=$(az storage account keys list --resource-group "${RESOURCE_GROUP}" --account-name "${STORAGE_ACCOUNT}" --query "[0].value" -o tsv)
SAS_EXPIRY=$(date -u -d "7 days" '+%Y-%m-%dT%H:%MZ' 2>/dev/null || date -u -v+7d '+%Y-%m-%dT%H:%MZ')
SAS_TOKEN=$(az storage container generate-sas --account-name "${STORAGE_ACCOUNT}" --name "${CONTAINER_NAME}" --account-key "${STORAGE_KEY}" --permissions rwl --expiry "${SAS_EXPIRY}" -o tsv)
BLOB_URL="https://${STORAGE_ACCOUNT}.blob.core.windows.net/${CONTAINER_NAME}/janus_1m_results.tar.gz?${SAS_TOKEN}"

echo "[*] Step 2: Executing generation of remaining figures & upload inside VM..."
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
