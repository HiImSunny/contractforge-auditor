#!/usr/bin/env bash
# ContractForge Auditor — Backend health smoke test
# Usage: BACKEND_URL=https://your-backend.onrender.com bash scripts/smoke.sh

set -euo pipefail

BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"

echo "Checking backend health at ${BACKEND_URL}/api/health ..."
response=$(curl -fsS "${BACKEND_URL}/api/health")
echo "Response: ${response}"

# Validate the response contains "ok"
if echo "${response}" | grep -q '"status":"ok"'; then
    echo "✓ Backend is healthy"
    exit 0
else
    echo "✗ Backend health check failed"
    exit 1
fi
