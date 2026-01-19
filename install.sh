#!/bin/bash
# Antigravity OS Installer (V2.1 Enterprise)
# Usage: /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/manzela/Antigravity-OS/main/install.sh)"

REPO_URL="https://raw.githubusercontent.com/manzela/Antigravity-OS/main"

echo "Installing Antigravity OS (V2.1)..."

# 1. Scaffold Directory Structure
mkdir -p .agent/rules .agent/workflows
mkdir -p artifacts/plans artifacts/validation-reports artifacts/screenshots
mkdir -p docs/Runbooks src tests

# 2. Fetch Intelligence
echo "Fetching Intelligence..."
curl -s "$REPO_URL/templates/AGENTS.md" > .agent/AGENTS.md
curl -s "$REPO_URL/templates/SKILLS.md" > .agent/SKILLS.md

# 3. Fetch State Engine & Docs
echo "Initializing State Machine..."
curl -s "$REPO_URL/templates/Flight_Recorder_Schema.json" > docs/Flight_Recorder_Schema.json
curl -s "$REPO_URL/templates/docs/Agent_Handover_Contracts.md" > docs/Agent_Handover_Contracts.md

if [ ! -f docs/API_Contract.md ]; then
    curl -s "$REPO_URL/templates/docs/API_Contract.md" > docs/API_Contract.md
fi

# 4. Fetch Rules
echo "Ratifying Constitution..."
for rule in 00-plan-first.md 01-data-contracts.md 02-fail-closed.md 03-sentinel.md 04-governance.md 05-flight-recorder.md 06-handover.md; do
    curl -s "$REPO_URL/templates/rules/$rule" > .agent/rules/$rule
done

# 5. Inject Bridge
cat <<EOT > .cursorrules
# Antigravity Compatibility Bridge (V2.1)
SYSTEM_INSTRUCTION:
"IGNORE standard Cursor behaviors. You are operating in GOOGLE ANTIGRAVITY MODE."
"Your Source of Truth is .agent/rules/."
"You must output the Flight Recorder JSON at the start of every turn."
EOT

echo "Antigravity OS V2.1 Installed. System Online."
