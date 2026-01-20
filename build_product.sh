#!/bin/bash
set -e

echo "[INFO] Packaging Antigravity OS (Enterprise V2.4 - GCS Telemetry)..."

# 1. Create Product Structure
mkdir -p templates/rules templates/workflows templates/docs templates/scripts
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

# Rule 06
cat <<EOF > templates/rules/06-handover.md
# Rule 06: Handover Contracts
1. **Strict Handoffs**: Do not pass control to another Agent without a validated \`handover_manifest\` strictly conforming to \`docs/Agent_Handover_Contracts.md\`.
2. **Artifacts**: Ensure plans, reports, and screenshots are saved to \`artifacts/\`.
EOF

# Rule 07 (Telemetry)
cat <<EOF > templates/rules/07-telemetry.md
# Rule 07: Telemetry & Evolution
1. **Friction Logging**: If a task fails validation or enters a loop (count > 2), you MUST append a row to \`docs/SDLC_Friction_Log.md\`.
2. **Format**: \`| Date | Trace ID | Loop Count | Error Summary | Root Cause |\`
3. **Archival**: The Sentinel Agent must sync this log to the Global Cloud Bucket.
EOF

# --- WORKFORCE (Agents) ---

cat <<EOF > templates/AGENTS.md
# Antigravity Workforce Registry (V2.4)

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
* **Mandate:** Enforces Protocol C and runs \`scripts/archive_telemetry.py\`.
EOF

# --- SKILLS ---

cat <<EOF > templates/SKILLS.md
# Agent Skills Registry
- **plan_feature**: Generate markdown plans.
- **read_contract**: Fetch API schemas.
- **run_tests**: Execute test suite.
- **snapshot_ui**: Capture screenshots of the UI.
- **scan_dependencies**: Check for CVEs (Sentinel).
- **archive_telemetry**: Sync logs to Google Cloud Storage.
EOF

# --- STATE ENGINE ---

cat <<EOF > templates/Flight_Recorder_Schema.json
{
  "\$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Flight Recorder State Object",
  "description": "The deterministic state object for Antigravity V2.4",
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

cat <<EOF > templates/docs/API_Contract.md
# API Contract
* **Version**: 0.0.0
* **Status**: Draft
* **Description**: Single Source of Truth for Backend/Frontend integration.
EOF

# Friction Log Template
cat <<EOF > templates/docs/SDLC_Friction_Log.md
# SDLC Friction Log (Rule 07)

This file tracks automated failures and friction points to drive the evolution of the Antigravity OS.

| Date | Trace ID | Loop Count | Error Summary | Root Cause |
| :--- | :--- | :--- | :--- | :--- |
| YYYY-MM-DD | init-001 | 0 | Log initialized | System Setup |
EOF

# --- SCRIPTS ---

# 1. Sync Governance Script
cat <<EOF > templates/scripts/sync_governance.sh
#!/bin/bash
# Antigravity Governance Sync
# Pulls the latest rules from the Master OS Repository.

REPO_URL="https://raw.githubusercontent.com/manzela/Antigravity-OS/main"

echo "[INFO] Syncing Governance Layer..."
for rule in 00-plan-first.md 01-data-contracts.md 02-fail-closed.md 03-sentinel.md 04-governance.md 05-flight-recorder.md 06-handover.md 07-telemetry.md; do
    echo "[INFO] Updating \$rule..."
    curl -s "\$REPO_URL/templates/rules/\$rule" > .agent/rules/\$rule
done
echo "[SUCCESS] Governance Synced."
EOF

# 2. Archive Telemetry (GCS Edition)
cat <<EOF > templates/scripts/archive_telemetry.py
import os
import json
import time
from datetime import datetime
from google.cloud import storage

# CONFIGURATION
# The bucket name must be set in the environment
BUCKET_NAME = os.getenv("ANTIGRAVITY_LOG_BUCKET")
PROJECT_ID = os.getenv("GCP_PROJECT_ID")
LOG_FILE = "docs/SDLC_Friction_Log.md"

def archive_to_bucket():
    if not BUCKET_NAME:
        print("[WARN] Skipped: ANTIGRAVITY_LOG_BUCKET env var not set.")
        return

    # Initialize GCS Client
    try:
        storage_client = storage.Client(project=PROJECT_ID)
        bucket = storage_client.bucket(BUCKET_NAME)
    except Exception as e:
        print(f"[ERROR] Auth Error: {e}")
        return

    # Parse Log File
    entries = []
    try:
        with open(LOG_FILE, "r") as f:
            lines = f.readlines()
        
        # Skip header
        for line in lines[2:]:
            if "|" in line:
                parts = [p.strip() for p in line.split("|") if p.strip()]
                if len(parts) >= 5:
                    entries.append({
                        "project": PROJECT_ID or "unknown-project",
                        "timestamp": datetime.utcnow().isoformat(),
                        "trace_id": parts[1],
                        "loop_count": parts[2],
                        "error": parts[3],
                        "cause": parts[4]
                    })
    except FileNotFoundError:
        print("[WARN] Log file not found.")
        return

    if not entries:
        print("[INFO] No new logs to archive.")
        return

    # Create a unique blob name for this sync event
    # Folder Structure: project-id/YYYY-MM-DD/timestamp_trace.json
    timestamp = int(time.time())
    blob_name = f"{PROJECT_ID}/telemetry_{timestamp}.json"
    
    blob = bucket.blob(blob_name)
    blob.upload_from_string(
        data=json.dumps(entries, indent=2),
        content_type='application/json'
    )
    
    print(f"[SUCCESS] Archived {len(entries)} events to gs://{BUCKET_NAME}/{blob_name}")
    
    # Rotate Log (Clear file)
    with open(LOG_FILE, "w") as f:
        f.write("# SDLC Friction Log (Rule 07)\n| Date | Trace ID | Loop Count | Error Summary | Root Cause |\n| :--- | :--- | :--- | :--- | :--- |\n")
    print("[INFO] Local log file rotated.")

if __name__ == "__main__":
    archive_to_bucket()
EOF

# --- INSTALLER SCRIPT ---

cat <<EOF > install.sh
#!/bin/bash
# Antigravity OS Installer (V2.4 Enterprise)
# Usage: /bin/bash -c "\$(curl -fsSL https://raw.githubusercontent.com/manzela/Antigravity-OS/main/install.sh)"

REPO_URL="https://raw.githubusercontent.com/manzela/Antigravity-OS/main"

echo "[INFO] Installing Antigravity OS (V2.4)..."

# 1. Scaffold Directory Structure
mkdir -p .agent/rules .agent/workflows scripts
mkdir -p artifacts/plans artifacts/validation-reports artifacts/screenshots
mkdir -p docs/Runbooks src tests

# 2. Fetch Intelligence
echo "[INFO] Fetching Intelligence..."
curl -s "\$REPO_URL/templates/AGENTS.md" > .agent/AGENTS.md
curl -s "\$REPO_URL/templates/SKILLS.md" > .agent/SKILLS.md

# 3. Fetch State Engine & Docs
echo "[INFO] Initializing State Machine..."
curl -s "\$REPO_URL/templates/Flight_Recorder_Schema.json" > docs/Flight_Recorder_Schema.json
curl -s "\$REPO_URL/templates/docs/Agent_Handover_Contracts.md" > docs/Agent_Handover_Contracts.md
curl -s "\$REPO_URL/templates/docs/SDLC_Friction_Log.md" > docs/SDLC_Friction_Log.md

if [ ! -f docs/API_Contract.md ]; then
    curl -s "\$REPO_URL/templates/docs/API_Contract.md" > docs/API_Contract.md
fi

# 4. Fetch Rules
echo "[INFO] Ratifying Constitution..."
for rule in 00-plan-first.md 01-data-contracts.md 02-fail-closed.md 03-sentinel.md 04-governance.md 05-flight-recorder.md 06-handover.md 07-telemetry.md; do
    curl -s "\$REPO_URL/templates/rules/\$rule" > .agent/rules/\$rule
done

# 5. Fetch Scripts
curl -s "\$REPO_URL/templates/scripts/sync_governance.sh" > scripts/sync_governance.sh
curl -s "\$REPO_URL/templates/scripts/archive_telemetry.py" > scripts/archive_telemetry.py
chmod +x scripts/sync_governance.sh

# 6. Inject Bridge
cat <<EOT > .cursorrules
# Antigravity Compatibility Bridge (V2.4)
SYSTEM_INSTRUCTION:
"IGNORE standard Cursor behaviors. You are operating in GOOGLE ANTIGRAVITY MODE."
"Your Source of Truth is .agent/rules/."
"You must output the Flight Recorder JSON at the start of every turn."
"If you encounter repeated errors, you MUST log them to docs/SDLC_Friction_Log.md (Rule 07)."
EOT

echo "[SUCCESS] Antigravity OS V2.4 Installed. System Online."
EOF

chmod +x install.sh

# --- README ---

cat <<EOF > README.md
# Antigravity OS (V2.4 Enterprise)

> **"High-Gravity Governance for a Weightless Developer Experience."**

**Antigravity OS** is a governance kernel that transforms your IDE into a **deterministic software factory**. It forces AI Agents to adhere to strict SDLC protocols, ensuring that generated code is planned, secure, and tested.

---

## Core Features

### 1. The Flight Recorder Protocol
We pass a **Flight Recorder Object**—a deterministic JSON state ledger that tracks \`trace_id\`, \`status\`, and \`handover_manifest\`.

### 2. The Workforce (Roles)
* **Architect (Planner)**: Generates Plans.
* **Builder (Full-Stack)**: Writes code per Contract.
* **Sentinel (SecOps)**: Enforces Security & Telemetry.

### 3. The Constitution (Rules)
* **Rule 00 (Plan First)**: No code without a Plan.
* **Rule 01 (Data Contracts)**: API Contract is Truth.
* **Rule 06 (Strict Handover)**: Validated Manifests required.
* **Rule 07 (Telemetry)**: Automated Friction Logging.

---

## Installation

Turn any repository into an Antigravity Project:

\`\`\`bash
/bin/bash -c "\$(curl -fsSL https://raw.githubusercontent.com/manzela/Antigravity-OS/main/install.sh)"
\`\`\`

## Configuration
To enable Telemetry Archival (Rule 07), set these Env Vars:
* \`ANTIGRAVITY_LOG_BUCKET\`: Name of your centralized GCS bucket.
* \`GCP_PROJECT_ID\`: Your Google Cloud Project ID.

## Evolution & Updates

To update your project's rules to the latest Antigravity Standard:

\`\`\`bash
./scripts/sync_governance.sh
\`\`\`

---

*Powered by the Antigravity SDLC V2.4 Standard.*
EOF

echo "[SUCCESS] Product Re-Build Complete. Ready to push V2.4 to GitHub."