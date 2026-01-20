#!/bin/bash
# End-to-End Verification Suite for Antigravity OS V2.5.1
# Scenarios: Cost Guard -> Build Failure -> Jira Ticket -> Log Fetch

set -e

echo "[E2E] Starting End-to-End Verification..."
echo "----------------------------------------"

# 1. Cost Guard Check (Tier: nvidia_l4)
# Cost = 1h * $2.50 = $2.50. Cap is $50. Should PASS.
echo "[TEST 1] Cost Guard Solvency Check (nvidia_l4)..."
python3 templates/sentinel/cost_guard.py 1.0 --tier nvidia_l4 || { echo "[FAIL] Cost Guard blocked valid request"; exit 1; }

# 2. Simulate Build Failure & File Ticket
# Creating a dummy failure log
echo "Build Failed: Syntax Error in src/main.py" > build_fail.log
echo "[TEST 2] Filing Jira Ticket (Target: TNG)..."
python3 templates/observability/jira_bridge.py "Fix [Build] Failure" "Trace: 999 - Syntax Error" "TNG" --file build_fail.log --line 1

# 3. Log Fetch Verification
# We verify that the ticket (fingerprint) was stored locally (or remote)
echo "[TEST 3] Fetching Jira Logs (Waiting 10s for Indexing)..."
sleep 10
python3 templates/observability/jira_bridge.py --fetch | grep -F "Fix [Build] Failure" && echo "[PASS] Log entry found." || { echo "[FAIL] Log entry missing"; exit 1; }

echo "----------------------------------------"
echo "[SUCCESS] All E2E Scenarios Passed."
