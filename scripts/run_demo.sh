#!/bin/bash
export PATH="$PATH:$(python3 -m site --user-base)/bin:$(python3 -c 'import sysconfig; print(sysconfig.get_path("scripts"))')"
export GCP_PROJECT_ID="i-for-ai"
# Ensure we don't use a stale key path that causes uplink errors
export GOOGLE_APPLICATION_CREDENTIALS=""

echo "🎬 TNG Antigravity OS - End-to-End Demo"
echo "----------------------------------------"
echo "Scenario: Zero-Division Error in Flight Control"
echo "Goal: Verify Telemetry, Jira Ticket Creation, and AI Self-Healing"
echo "----------------------------------------"

# Run Orchestrator
python3 .agent/runtime/orchestrator.py

# Check if Orchestrator actually failed (as expected)
RET=$?
if [ $RET -eq 1 ]; then
    echo ""
    echo "✅ Demo Successful: Orchestrator caught the failure and triggered the Mind."
    exit 0
else
    echo ""
    echo "❌ Demo Failed: Orchestrator did not exit with error (Did the test pass?)"
    exit 1
fi
