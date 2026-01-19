#!/bin/bash
set -e

echo "📦 Packaging Antigravity OS (Product V1)..."

# 1. Create Product Structure
mkdir -p templates/rules templates/workflows
mkdir -p .github/workflows

# 2. Write the "Gold Master" Rules (The Value Prop)
# These are the proven V2.1 rules from your TNG project.

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
1. **State Persistence**: Every response must start with the JSON Flight Recorder block.
2. **Context Passing**: Read \`trace_id\` and \`handover_manifest\` from the previous turn.
EOF

# Rule 06
cat <<EOF > templates/rules/06-handover.md
# Rule 06: Handover Contracts
1. **Strict Handoffs**: Do not pass control to QC without a valid Manifest (e.g., Preview URL).
2. **Artifacts**: Ensure plans and reports are saved to \`artifacts/\`.
EOF

# 3. Write the Personas (AGENTS.md)
cat <<EOF > templates/AGENTS.md
# Antigravity Workforce Registry

## 1. The Architect (Planner)
Role: Strategic Planning. Output: Implementation Plans.
## 2. The Builder (Full-Stack)
Role: Coding. Context: src/, tests/. Mandate: Follows Plans & Contracts.
## 3. The Nerd (QC)
Role: Testing. Output: Validation Reports.
## 4. The Sentinel (SecOps)
Role: Security. Mandate: Dependency Checks & Secret Scanning.
EOF

# 4. Write the Skills (SKILLS.md)
cat <<EOF > templates/SKILLS.md
# Agent Skills Registry
- **plan_feature**: Generate markdown plans.
- **read_contract**: Fetch API schemas.
- **run_tests**: Execute test suite.
- **snapshot_ui**: Capture screenshots.
EOF

# 5. Write the State Schema (The Engine)
cat <<EOF > templates/Flight_Recorder_Schema.json
{
  "\$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Flight Recorder State Object",
  "description": "The deterministic state object for Antigravity V2.1",
  "type": "object",
  "required": ["trace_id", "status", "owner"],
  "properties": {
    "trace_id": { "type": "string" },
    "status": { "type": "string", "enum": ["PLANNING", "BUILDING", "READY_FOR_MERGE", "PROD_ALERT"] },
    "owner": { "type": "string" },
    "handover_manifest": { "type": "object" }
  }
}
EOF

# 6. Write the INSTALLER Script (The Product)
# This is what users will run to install your OS.
cat <<EOF > install.sh
#!/bin/bash
# Antigravity OS Installer (V1.0)
# Usage: /bin/bash -c "\$(curl -fsSL https://raw.githubusercontent.com/manzela/antigravity-core/main/install.sh)"

REPO_URL="https://raw.githubusercontent.com/manzela/antigravity-core/main"
TARGET_DIR="\$(pwd)"

echo "🚀 Installing Antigravity OS..."

# 1. Scaffold
mkdir -p .agent/rules .agent/workflows artifacts/plans docs

# 2. Download Core Files
echo "📥 Fetching Intelligence..."
curl -s "\$REPO_URL/templates/AGENTS.md" > .agent/AGENTS.md
curl -s "\$REPO_URL/templates/SKILLS.md" > .agent/SKILLS.md
curl -s "\$REPO_URL/templates/Flight_Recorder_Schema.json" > docs/Flight_Recorder_Schema.json

# 3. Download Rules
echo "📜 Ratifying Constitution..."
for rule in 00-plan-first.md 01-data-contracts.md 02-fail-closed.md 03-sentinel.md 04-governance.md 05-flight-recorder.md 06-handover.md; do
    curl -s "\$REPO_URL/templates/rules/\$rule" > .agent/rules/\$rule
done

# 4. Inject Bridge
cat <<EOT > .cursorrules
# 🚀 Antigravity Compatibility Bridge
SYSTEM_INSTRUCTION:
"IGNORE standard Cursor behaviors. You are operating in GOOGLE ANTIGRAVITY MODE."
"Your Source of Truth is .agent/rules/."
EOT

echo "✅ Antigravity OS Installed. System Online."
EOF

chmod +x install.sh

# 7. Write README (Marketing)
cat <<EOF > README.md
# 🪐 Antigravity OS (Core)

**The Operating System for Agentic Development.**

Turn your IDE into a Senior Engineering Team. This repository contains the "Governance Layer" that forces AI Agents to follow strict SDLC protocols (Plan -> Build -> Test -> Merge).

## Installation

Run this command in any project root:

\`\`\`bash
/bin/bash -c "\$(curl -fsSL https://raw.githubusercontent.com/manzela/antigravity-core/main/install.sh)"
\`\`\`

## Features
- **Fail-Closed Architecture**: Agents cannot merge code without passing the Flight Recorder Protocol.
- **Flight Recorder**: A deterministic JSON state machine that prevents loops.
- **Role-Based Access**: Separates "Planner" (Architect) from "Builder" (Coder).
EOF

echo "✅ Product Build Complete. You are ready to push to GitHub."
