#!/bin/bash
set -e

# Antigravity "System Rule" - Environment Validator
# This script enforces the setup prerequisites before ANY development can ensure.

echo "===================================================="
echo "   ANTIGRAVITY SYSTEM VALIDATION (Rule V2.7)"
echo "===================================================="

FAILURES=0

check_cmd() {
    if ! command -v "$1" &> /dev/null; then
        echo "[FAIL] Missing Command: $1"
        FAILURES=$((FAILURES + 1))
    else
        echo "[OK] Found Command: $1"
    fi
}

check_env() {
    if [ -z "${!1}" ]; then
        echo "[WARN] Missing Environment Variable: $1 (Required for Production/Test)"
        # We warn locally, but failure might be optional depending on dev mode.
        # For the "System Rule", we will treat key secrets as critical.
        if [[ "$1" == "GCP_BILLING_ACCOUNT_ID" ]] || [[ "$1" == "REDIS_HOST" ]]; then
             FAILURES=$((FAILURES + 1))
        fi
    else
        echo "[OK] Found Variable: $1"
    fi
}

echo "--- 1. Software Dependencies ---"
check_cmd python3
check_cmd docker
check_cmd git
check_cmd curl
check_cmd gcloud

echo "--- 2. Python Libraries (Pip) ---"
# Check if requirements are installed
if python3 -m pip freeze | grep -q 'redis' && python3 -m pip freeze | grep -q 'google-cloud-storage'; then
    echo "[OK] Critical Python Libraries verified."
else
    echo "[WARN] Missing Python dependencies. Installing..."
    # Attempt install if missing (to make it frictionless)
    if [ -f "requirements.txt" ]; then
        python3 -m pip install -r requirements.txt
    else
        echo "[FAIL] requirements.txt not found!"
        FAILURES=$((FAILURES + 1))
    fi
fi

echo "--- 3. Credential Configuration ---"
check_env "GCP_BILLING_ACCOUNT_ID"
check_env "GCP_PROJECT_ID"
check_env "ANTIGRAVITY_LOG_BUCKET"
check_env "REDIS_HOST"
check_env "REDIS_PORT"
check_env "REDIS_USER"
check_env "REDIS_PASSWORD"
check_env "JIRA_API_TOKEN"
check_env "GCP_SA_KEY"

echo "--- 4. Network Connectivity ---"
# Simple connectivity check to Google (confirming internet access)
if curl -s --connect-timeout 3 https://www.google.com > /dev/null; then
    echo "[OK] Internet Connectivity Verified."
else
    echo "[FAIL] No Internet Connectivity."
    FAILURES=$((FAILURES + 1))
fi

echo "===================================================="
if [ $FAILURES -eq 0 ]; then
    echo "[SUCCESS] SYSTEM READY. You may proceed with development."
    exit 0
else
    echo "[ERROR] SYSTEM VALIDATION FAILED. $FAILURES issues found."
    echo "Please review the README.md 'Prerequisites' section and configure your environment."
    exit 1
fi
