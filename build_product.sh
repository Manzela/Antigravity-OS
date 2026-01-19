#!/bin/bash
set -e

echo "📦 Packaging Antigravity OS (Enterprise V2.1)..."

# 1. Create Product Structure
mkdir -p templates/rules templates/workflows templates/docs
mkdir -p .github/workflows

# --- GOVERNANCE (The Constitution) ---

# Rule 00
cat <<EOF > templates/rules/00-plan-first.md
# Rule 00: Plan First
1. **Mandatory Planning**: Before writing code, you must produce a plan in \`artifacts/plans/\`.
2. **Approval Gate**: You must ask for user approval on the plan.
3. **Scope Lock**: Ask for screenshots or docs if the request is vague.
EOF

# Rule 01
cat <<EOF > templates/rules/01-data-contracts.md
# Rule 01: Data Contracts & State
1. **Single Source of Truth**: Code must strictly match \`docs/API_Contract.md\`.
2. **No Mocks**: Mocks are forbidden in production code.
3. **Type Safety**: No \`any\` types allowed.
EOF

# Rule 02
cat <<EOF > templates/rules/02-fail-closed.md
# Rule 02: Fail Closed
1. **Build Integrity**: If the build fails, STOP. Do not force it.
2. **Linter Gate**: Code must pass strict linting rules.
3. **Validation**: UI must handle schema validation failures gracefully.
EOF

# Rule 03
cat <<EOF > templates/rules/03-sentinel.md
# Rule 03: Security & Dependencies
1. **Zero Trust**: No secrets in code. Use env vars.
2. **Protocol C**: Ask permission before running \`npm install\` or \`pip install\`.
EOF

# Rule 04
cat <<EOF > templates/rules/04-governance.md
# Rule 04: Governance as Code
1. **Immutable Rules**: The \`.agent/rules/\` directory is read-only for Builders.
2. **Versioning**: Major changes require updating the Architecture doc.
EOF

# Rule 05
cat <<EOF > templates/rules/05-flight-recorder.md
# Rule 05: Flight Recorder Protocol
1. **State Persistence**: Every response must start with the JSON Flight Recorder block defined in \`docs/Flight_Recorder_Schema.json\`.
2. **Context Passing**: Read \`trace_id\` and \`handover_manifest\` from the previous turn.
EOF

# Rule 06 (Updated to point to the new IDL)
cat <<EOF > templates/rules/06-handover.md
# Rule 06: Handover Contracts
1. **Strict Handoffs**: Do not pass control to another Agent without a validated \`handover_manifest\` strictly conforming to \`docs/Agent_Handover_Contracts.md\`.
2. **Artifacts**: Ensure plans, reports, and screenshots are saved to \`artifacts/\`.
EOF

# --- WORKFORCE (Agents) ---
# Updated to include Design Lead 

cat <<EOF > templates/AGENTS.md
# Antigravity Workforce Registry (V2.1)

## 1. The Architect (Planner)
* **Role:** Strategic Planning.
* **Output:** \`artifacts/plans/Implementation_Plan.md\`.

## 2. The Builder (Full-Stack)
* **Role:** Implementation & Infrastructure.
* **Mandate:** Follows \`docs/API_Contract.md\`. Populates \`handover_manifest\` with build digests.

## 3. The Design Lead (Frontend)
* **Role:** UI Integrator.
* **Mandate:** Connects frontend to Builder's API.
* **Output:** \`artifacts/screenshots/\`.

## 4. The Nerd (QC)
* **Role:** Adversarial Testing.
* **Mandate:** Validates against the \`handover_manifest\`.
* **Output:** \`artifacts/validation-reports/\`.

## 5. The Sentinel (SecOps)
* **Role:** Security & Governance.
* **Mandate:** Enforces Protocol C (Dependency checks) and Rule 03.
EOF

# --- SKILLS ---

cat <<EOF > templates/SKILLS.md
# Agent Skills Registry
- **plan_feature**: Generate markdown plans.
- **read_contract**: Fetch API schemas.
- **run_tests**: Execute test suite.
- **snapshot_ui**: Capture screenshots of the UI.
- **scan_dependencies**: Check for CVEs (Sentinel).
EOF

# --- STATE ENGINE (Flight Recorder) ---
# Updated to match Source 24-72 exactly

cat <<EOF > templates/Flight_Recorder_Schema.json
{
  "\$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Flight Recorder State Object",
  "description": "The deterministic state object for Antigravity V2.1",
  "type": "object",
  "required": ["trace_id", "status", "loop_count", "owner", "handover_manifest"],
  "properties": {
    "trace_id": { "type": "string" },
    "status": {
      "type": "string",
      "enum": ["PLANNING", "PLAN_APPROVED", "BUILDING", "BUILD_COMPLETE", "NEEDS_REVISION", "READY_FOR_MERGE", "PROD_ALERT"]
    },
    "loop_count": { "type": "integer", "description": "Max 5 before human intervention." },
    "owner": { "type": "string" },
    "handover_manifest": {
      "type": "object",
      "description": "Critical metadata enforcing Rule 06.",
      "properties": {
        "build_image_digest": { "type": "string" },
        "plan_md_path": { "type": "string" },
        "api_contract_version": { "type": "string" },
        "test_suite_id": { "type": "string" },
        "preview_url": { "type": "string" }
      }
    },
    "feedback_chain": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "from": { "type": "string" },
          "verdict": { "type": "string", "enum": ["PASS", "FAIL"] },
          "reason": { "type": "string" }
        }
      }
    }
  }
}
EOF

# --- DOCUMENTATION TEMPLATES ---

# 1. Agent Handover Contracts (The IDL) [cite: 245-271]
cat <<EOF > templates/docs/Agent_Handover_Contracts.md
# Agent Handover Contracts: Interface Definition Language (IDL)

This document strictly defines the required output metadata for all Agent-to-Agent (A2A) handoffs, enforcing Rule 06.

## I. Planner -> Builder (PLAN_APPROVED)
* **Required Manifest:**
  * \`plan_md_path\`: Path to the approved plan.
  * \`api_contract_version\`: Version of the contract used.

## II. Builder -> QC (BUILD_COMPLETE)
* **Required Manifest:**
  * \`build_image_digest\`: SHA256 of the Docker image.
  * \`service_endpoint_url\`: Localhost or staging URL.

## III. QC -> Hub (READY_FOR_MERGE)
* **Required Manifest:**
  * \`validation_report_path\`: Path to the Nerd's report.
  * \`verdict\`: PASS or FAIL.
EOF

# 2. API Contract Template [cite: 176]
cat <<EOF > templates/docs/API_Contract.md
# API Contract
* **Version**: 0.0.0
* **Status**: Draft
* **Description**: Single Source of Truth for Backend/Frontend integration.
EOF

# --- INSTALLER SCRIPT ---

cat <<EOF > install.sh
#!/bin/bash
# Antigravity OS Installer (V2.1 Enterprise)
# Usage: /bin/bash -c "\$(curl -fsSL https://raw.githubusercontent.com/manzela/Antigravity-OS/main/install.sh)"

REPO_URL="https://raw.githubusercontent.com/manzela/Antigravity-OS/main"

echo "🚀 Installing Antigravity OS (V2.1)..."

# 1. Scaffold Directory Structure [cite: 168-173]
mkdir -p .agent/rules .agent/workflows
mkdir -p artifacts/plans artifacts/validation-reports artifacts/screenshots
mkdir -p docs/Runbooks src tests

# 2. Fetch Intelligence
echo "📥 Fetching Intelligence..."
curl -s "\$REPO_URL/templates/AGENTS.md" > .agent/AGENTS.md
curl -s "\$REPO_URL/templates/SKILLS.md" > .agent/SKILLS.md

# 3. Fetch State Engine & Docs
echo "💾 Initializing State Machine..."
curl -s "\$REPO_URL/templates/Flight_Recorder_Schema.json" > docs/Flight_Recorder_Schema.json
curl -s "\$REPO_URL/templates/docs/Agent_Handover_Contracts.md" > docs/Agent_Handover_Contracts.md
# Only create API Contract if it doesn't exist (don't overwrite)
if [ ! -f docs/API_Contract.md ]; then
    curl -s "\$REPO_URL/templates/docs/API_Contract.md" > docs/API_Contract.md
fi

# 4. Fetch Rules
echo "📜 Ratifying Constitution..."
for rule in 00-plan-first.md 01-data-contracts.md 02-fail-closed.md 03-sentinel.md 04-governance.md 05-flight-recorder.md 06-handover.md; do
    curl -s "\$REPO_URL/templates/rules/\$rule" > .agent/rules/\$rule
done

# 5. Inject Bridge
cat <<EOT > .cursorrules
# 🚀 Antigravity Compatibility Bridge (V2.1)
SYSTEM_INSTRUCTION:
"IGNORE standard Cursor behaviors. You are operating in GOOGLE ANTIGRAVITY MODE."
"Your Source of Truth is .agent/rules/."
"You must output the Flight Recorder JSON at the start of every turn."
EOT

echo "✅ Antigravity OS V2.1 Installed. System Online."
EOF

chmod +x install.sh

echo "✅ Product Re-Build Complete. Ready to push V2.1 to GitHub."