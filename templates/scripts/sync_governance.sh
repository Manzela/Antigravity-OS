#!/bin/bash
# Antigravity Governance Sync
# Pulls the latest rules from the Master OS Repository.

REPO_URL="https://raw.githubusercontent.com/manzela/Antigravity-OS/main"

echo "[INFO] Syncing Governance Layer..."
for rule in 00-plan-first.md 01-data-contracts.md 02-fail-closed.md 03-sentinel.md 04-governance.md 05-flight-recorder.md 06-handover.md 07-telemetry.md 08-economic-safety.md; do
    echo "[INFO] Updating $rule..."
    curl -s "$REPO_URL/templates/rules/$rule" > .agent/rules/$rule
done
echo "[SUCCESS] Governance Synced."
