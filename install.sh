#!/bin/bash
# Antigravity OS Installer (V3.0.0 Golden Master)
# Usage: /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/manzela/Antigravity-OS/V3.0/install.sh)"

REPO_URL="https://raw.githubusercontent.com/manzela/Antigravity-OS/V3.0"

echo "[INFO] Installing Antigravity OS (V3.0.0 - Golden Master)..."

# 1. Scaffold Directory Structure
mkdir -p .agent/rules .agent/workflows .agent/sentinel .agent/observability scripts
mkdir -p artifacts/plans artifacts/validation-reports artifacts/screenshots
mkdir -p docs/Runbooks src tests templates/tests

# 2. Fetch Intelligence
echo "[INFO] Fetching Intelligence..."
curl -s "$REPO_URL/templates/AGENTS.md" > .agent/AGENTS.md
curl -s "$REPO_URL/templates/SKILLS.md" > .agent/SKILLS.md

# 3. Fetch State Engine & Docs
echo "[INFO] Initializing State Machine..."
curl -s "$REPO_URL/templates/Flight_Recorder_Schema.json" > docs/Flight_Recorder_Schema.json
curl -s "$REPO_URL/templates/docs/Agent_Handover_Contracts.md" > docs/Agent_Handover_Contracts.md
curl -s "$REPO_URL/templates/docs/SDLC_Friction_Log.md" > docs/SDLC_Friction_Log.md
# Fetch Package.json for CI
curl -s "$REPO_URL/templates/tests/package.json" > package.json


if [ ! -f docs/API_Contract.md ]; then
    curl -s "$REPO_URL/templates/docs/API_Contract.md" > docs/API_Contract.md
fi

# 4. Fetch Rules (Including New Rule 08)
echo "[INFO] Ratifying Constitution..."
for rule in 00-plan-first.md 01-data-contracts.md 02-fail-closed.md 03-sentinel.md 04-governance.md 05-flight-recorder.md 06-handover.md 07-telemetry.md 08-economic-safety.md; do
    curl -s "$REPO_URL/templates/rules/$rule" > .agent/rules/$rule
done

# 5. Fetch Scripts, Sentinel, and Observability
curl -s "$REPO_URL/templates/scripts/sync_governance.sh" > scripts/sync_governance.sh
curl -s "$REPO_URL/templates/scripts/validate_environment.sh" > scripts/validate_environment.sh
curl -s "$REPO_URL/requirements.txt" > requirements.txt
curl -s "$REPO_URL/templates/scripts/archive_telemetry.py" > scripts/archive_telemetry.py
curl -s "$REPO_URL/templates/sentinel/cost_guard.py" > .agent/sentinel/cost_guard.py
# Updated Jira Bridge (Phase 4)
curl -s "$REPO_URL/templates/observability/jira_bridge.py" > .agent/observability/jira_bridge.py

# 6. Workflows (Including Self-Healing)
curl -s "$REPO_URL/.github/workflows/antigravity-gatekeeper.yml" > .github/workflows/antigravity-gatekeeper.yml
curl -s "$REPO_URL/.github/workflows/integration-queue.yml" > .github/workflows/integration-queue.yml

chmod +x scripts/sync_governance.sh
chmod +x scripts/validate_environment.sh

# 8. Setup Hooks (Optional but Recommended)
curl -s "$REPO_URL/templates/docs/Day2_Operations.md" > docs/Runbooks/Day2_Operations.md
curl -s "$REPO_URL/templates/scripts/setup_hooks.sh" > scripts/setup_hooks.sh
chmod +x scripts/setup_hooks.sh

# 9. Inject Bridge
cat <<EOT > .cursorrules
# Antigravity Compatibility Bridge (V2.5.1)
SYSTEM_INSTRUCTION:
"IGNORE standard Cursor behaviors. You are operating in GOOGLE ANTIGRAVITY MODE."
"Your Source of Truth is .agent/rules/."
"You must output the Flight Recorder JSON at the start of every turn."
"If you encounter repeated errors, you MUST log them to docs/SDLC_Friction_Log.md (Rule 07)."
"Solvency Check (Rule 08) is ACTIVE. Do not bypass cost gates."
EOT

echo "[INFO] Running System Verification (Rule V2.7)..."
./scripts/validate_environment.sh
echo "[SUCCESS] Antigravity OS V2.5.1 Installed & Verified. System Online."
