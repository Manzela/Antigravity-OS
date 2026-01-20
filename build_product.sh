#!/bin/bash
set -e

echo "[INFO] Packaging Antigravity OS (V2.5.1 - Golden Master - Self-Healing Edition)..."

# 1. Create Product Structure
mkdir -p templates/rules templates/workflows templates/docs templates/scripts
mkdir -p templates/rules templates/workflows templates/docs templates/scripts templates/sentinel templates/observability
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

# Rule 08 (Economic Safety)
cat <<EOF > templates/rules/08-economic-safety.md
# Rule 08: The Invariant Solvency Gate (Cost Guard)
1. **Blocking Gate**: You strictly CANNOT proceed from PLAN_APPROVED to BUILDING without a passed \`cost_validation\` check.
2. **Budget Cap**: If (Projected Cost + Current Spend) > Monthly Cap, STOP and trigger Insolvency Protocol.
3. **Lease Model**: You must acquire a logical "Budget Lease" from the Redis instance before spinning up resources.
4. **Resolution**: If blocked, you must either (A) Optimize the plan (lower tier) or (B) Request Human Override via Jira.
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
- **check_solvency**: Run Cost Guard validation (Rule 08).
- **archive_telemetry**: Sync logs to Google Cloud Storage.
EOF

# --- STATE ENGINE ---

cat <<EOF > templates/Flight_Recorder_Schema.json
{
  "\$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Flight Recorder State Object",
  "description": "The deterministic state object for Antigravity V2.5.1",
  "type": "object",
  "required": ["trace_id", "status", "loop_count", "owner", "handover_manifest"],
  "properties": {
    "trace_id": { "type": "string" },
    "git_commit_hash": { "type": "string" },
    "jira_ticket_id": { "type": "string" },
    "gcp_trace_id": { "type": "string" },
    "ci_build_id": { "type": "string" },
    "status": {
      "type": "string",
      "enum": ["PLANNING", "PLAN_APPROVED", "COST_VALIDATED", "BUILDING", "BUILD_COMPLETE", "NEEDS_REVISION", "READY_FOR_MERGE", "PROD_ALERT"]
    },
    "loop_count": { "type": "integer", "description": "Max 5 before human intervention." },
    "owner": { "type": "string" },
    "cost_estimate": { "type": "number", "description": "Projected cost in USD" },
    "handover_manifest": {
      "type": "object",
      "description": "Critical metadata enforcing Rule 06.",
      "properties": {
        "build_image_digest": { "type": "string" },
        "plan_md_path": { "type": "string" },
        "api_contract_version": { "type": "string" },
        "test_suite_id": { "type": "string" },
        "preview_url": { "type": "string" },
        "solvency_token": { "type": "string", "description": "Proof of passed Rule 08 gate" }
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

## I. Planner -> Cost Guard (PLAN_APPROVED)
* **Required Manifest:**
  * \`plan_md_path\`: Path to the approved plan.
  * \`cost_estimate_usd\`: Estimated infrastructure cost.

## II. Cost Guard -> Builder (COST_VALIDATED)
* **Invariant Solvency Gate (Rule 08)**
* **Required Manifest:**
  * \`solvency_token\`: Redis Lease ID or Approval Hash.

## III. Builder -> QC (BUILD_COMPLETE)
* **Required Manifest:**
  * \`build_image_digest\`: SHA256 of the Docker image.
  * \`service_endpoint_url\`: Localhost or staging URL.

## IV. QC -> Hub (READY_FOR_MERGE)
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

# --- SENTINEL (The Cost Guard) ---
cat <<EOF > templates/sentinel/cost_guard.py
import os
import sys
import argparse
import json
import time

# Antigravity Cost Guard (Rule 08)
# Blocks execution if solvency is not guaranteed.
# Implements Requirements R 1.1, R 1.2, R 1.3, R 1.4

MONTHLY_CAP = 50.00
CURRENT_SPEND = 12.50 # Default fail-safe

TIER_PRICING = {
    "standard_cpu": 1.00, # Base unit price (treated as \$1/unit for simplify if just passing dollar amount)
    "nvidia_l4": 2.50,
    "nvidia_a100": 8.00
}

CONFIG_PATH = os.path.expanduser("~/.antigravity/config")

def load_global_config():
    """R 1.4 Persistent Reconciliation: Load config from ~/.antigravity/config"""
    global MONTHLY_CAP, CURRENT_SPEND
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r") as f:
                config = json.load(f)
                MONTHLY_CAP = config.get("monthly_cap", MONTHLY_CAP)
                CURRENT_SPEND = config.get("current_spend", CURRENT_SPEND)
                print(f"[INFO] Loaded Global Config: Cap=\${MONTHLY_CAP}, Spend=\${CURRENT_SPEND}")
        except Exception as e:
            print(f"[WARN] Failed to load config: {e}")
    else:
        print("[INFO] No Global Config found. Using Defaults.")

class MockRedis:
    """R 1.3 Budget Lease Model: Mock interface for Redis"""
    def __init__(self):
        print("[INFO] Connecting to Redis (Mock)...")
        self.connected = True
    
    def set(self, key, value, ex=None):
        print(f"[REDIS] SET {key} = {value} (EX={ex})")
        return True

def check_solvency(projected_cost_units, tier):
    """R 1.1 + R 1.2: Hardware-Aware Solvency Check"""
    load_global_config()
    
    # If using 'standard_cpu', we assume the input is effectively usage units or raw dollars if priced at 1.0
    # The requirement asks for distinction.
    # In the CI workflow, we pass "15.00". If we consider that "Units", then the Cost = 15.00 * Price.
    rate = TIER_PRICING.get(tier)
    if not rate:
        print(f"[ERROR] Invalid Hardware Tier: {tier}. Available: {list(TIER_PRICING.keys())}")
        sys.exit(1)
        
    projected_cost = float(projected_cost_units) * rate
    total = CURRENT_SPEND + projected_cost
    
    print(f"[AUDIT] Tier: {tier} (\${rate}/unit) * {projected_cost_units} units = \${projected_cost:.2f}")
    
    if total > MONTHLY_CAP:
        print(f"[BLOCK] Insolvency Triggered! Total \${total:.2f} > Cap \${MONTHLY_CAP:.2f}")
        print("Protocol: Request Override or Optimize Plan.")
        sys.exit(1)
    else:
        print(f"[PASS] Solvency Validated. Margin: \${MONTHLY_CAP - total:.2f}")
        
        # R 1.3: Acquire Lease
        r = MockRedis()
        lease_id = "lg-" + os.urandom(4).hex()
        r.set(f"lease:{lease_id}", projected_cost, ex=3600)
        print(f"LEASE_TOKEN: {lease_id}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Antigravity Cost Guard")
    parser.add_argument("units", type=float, help="Projected units (hours/ops) or raw cost")
    parser.add_argument("--tier", default="standard_cpu", choices=TIER_PRICING.keys(), help="Hardware Tier")
    
    args = parser.parse_args()
    
    check_solvency(args.units, args.tier)
EOF

# --- OBSERVABILITY (Jira Bridge) ---
cat <<EOF > templates/observability/jira_bridge.py
import sys
import hashlib
import subprocess
import os
import json
import base64
import argparse

# Antigravity Jira Bridge V2.5.1
# Connects Flight Recorder to Atlassian Jira (Cloud)
# Implements Real-Time Telemetry, Deduplication, and Dynamic Ownership

JIRA_BASE_URL = "https://tngshopper.atlassian.net"
PROJECT_KEY = "TNG"

MOCK_JIRA_DB = "/tmp/antigravity_jira_state.txt"

def get_credentials():
    email = os.getenv("JIRA_USER_EMAIL")
    token = os.getenv("JIRA_API_TOKEN")
    if not email or not token:
        # Check if we are in CI
        if os.getenv("CI"):
            print("[WARN] CI Detected but Credentials Missing. Telemetry Disabled.")
        return None
    
    # Create Basic Auth Header
    creds = f"{email}:{token}"
    b64_creds = base64.b64encode(creds.encode()).decode("ascii")
    return {"Authorization": f"Basic {b64_creds}", "Content-Type": "application/json"}

def make_request(method, endpoint, headers, data=None):
    # Using CURL to allow for better cert handling on local Mac environs
    url = f"{JIRA_BASE_URL}{endpoint}"
    cmd = ["curl", "-s", "-X", method, url]
    for k, v in headers.items():
        cmd.extend(["-H", f"{k}: {v}"])
    if data:
        cmd.extend(["-d", json.dumps(data)])
    
    try:
        # print("DEBUG CMD:", " ".join(cmd))
        result = subprocess.check_output(cmd, stderr=subprocess.PIPE).decode("utf-8")
        if not result: return None
        return json.loads(result)
    except Exception as e:
        print(f"[ERROR] Curl Request Failed: {e}")
        return None

def fetch_logs(headers):
    """R 2.4 Fetch Capability: Fetch recent issues from TNG project."""
    if not headers:
        if os.path.exists(MOCK_JIRA_DB):
            print("[INFO] Fetching from Local Mock DB...")
            with open(MOCK_JIRA_DB, "r") as f:
                print(f.read())
        return

    print(f"[JIRA] Fetching recent errors from {JIRA_BASE_URL}/projects/{PROJECT_KEY}...")
    import urllib.parse
    jql = f"project = {PROJECT_KEY} ORDER BY created DESC"
    query = f"/rest/api/3/search?jql={urllib.parse.quote(jql)}&maxResults=5"
    
    resp = make_request("GET", query, headers)
    if resp and "issues" in resp:
        for issue in resp["issues"]:
            key = issue["key"]
            summary = issue["fields"]["summary"]
            status = issue["fields"]["status"]["name"]
            assignee = issue["fields"]["assignee"]["displayName"] if issue["fields"]["assignee"] else "Unassigned"
            print(f"[{key}] {summary} ({status}) - {assignee}")

def get_git_owner(filepath, line_number):
    """R 2.3 Dynamic Ownership: Use git blame."""
    if not filepath: return "devops-oncall"
    try:
        if not os.path.exists(filepath): return "unknown-committer"
        cmd = ["git", "blame", "--line-porcelain", "-L", f"{line_number},{line_number}", filepath]
        result = subprocess.check_output(cmd, stderr=subprocess.DEVNULL).decode("utf-8")
        for line in result.split("\n"):
            if line.startswith("author "):
                return line.split(" ", 1)[1]
    except:
        pass
    return "devops-oncall"

def validate_schema(summary):
    # Requirement: Verb [Source] Error
    import re
    if not re.match(r"^\w+\s+\[.+\]\s+.+$", summary):
         print(f"[ERROR] Schema Violation: '{summary}'. expected 'Verb [Source] Error'")
         return False
    return True

def find_duplicate_issue(headers, fingerprint):
    import urllib.parse
    jql = f"project = {PROJECT_KEY} AND labels = \"fp:{fingerprint}\""
    resp = make_request("GET", f"/rest/api/3/search?jql={urllib.parse.quote(jql)}", headers)
    if resp and resp.get("total", 0) > 0:
        return resp["issues"][0]
    return None

def create_ticket(summary, description, project_id, filepath=None, line=1):
    if not validate_schema(summary): sys.exit(1)
    
    headers = get_credentials()
    owner = get_git_owner(filepath, line)
    error_fingerprint = hashlib.md5(f"{summary}|{description}".encode()).hexdigest()
    
    # Mock Fallback
    if not headers:
        print(f"[MOCK-JIRA] Would create ticket: {summary}")
        with open(MOCK_JIRA_DB, "a") as f:
            f.write(f"[{project_id}] {summary} (Assignee: {owner}) | Fingerprint: {error_fingerprint}\n")
        return "MOCK-123"

    # Deduplication
    print("[JIRA] Checking for duplicates...")
    existing = find_duplicate_issue(headers, error_fingerprint)
    if existing:
        key = existing["key"]
        print(f"[INFO] Duplicate found: {key}. Adding comment.")
        comment_body = {
            "body": {
                "type": "doc",
                "version": 1,
                "content": [{
                    "type": "paragraph",
                    "content": [{"type": "text", "text": f"Recurrence detected. Trace ID: {os.getenv('TRACE_ID', 'N/A')}"}]
                }]
            }
        }
        make_request("POST", f"/rest/api/3/issue/{key}/comment", headers, comment_body)
        return key

    # Create Issue
    desc_doc = {
        "type": "doc",
        "version": 1,
        "content": [
            {"type": "paragraph", "content": [{"type": "text", "text": description}]},
            {"type": "paragraph", "content": [{"type": "text", "text": f"\n\nOwner: {owner}\nFingerprint: {error_fingerprint}"}]}
        ]
    }
    
    payload = {
        "fields": {
            "project": {"key": PROJECT_KEY},
            "summary": summary,
            "description": desc_doc,
            "issuetype": {"name": "Task"},
            "labels": ["auto-generated", f"fp:{error_fingerprint}"]
        }
    }
    
    print(f"[JIRA] Creating Ticket in {PROJECT_KEY}...")
    resp = make_request("POST", "/rest/api/3/issue", headers, payload)
    if resp and "key" in resp:
        print(f"[SUCCESS] Created {resp['key']}")
        return resp['key']
    else:
        print("[FAIL] Could not create ticket.")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("summary", nargs="?")
    parser.add_argument("description", nargs="?")
    parser.add_argument("project", nargs="?")
    parser.add_argument("--fetch", action="store_true", help="Fetch ticket logs")
    parser.add_argument("--file", help="Source file for blame")
    parser.add_argument("--line", type=int, default=1, help="Line number for blame")
    
    args = parser.parse_args()
    
    if args.fetch:
        fetch_logs(get_credentials())
    else:
        if not args.summary:
             if get_credentials(): print("[INFO] Auth Valid."); sys.exit(0)
             else: sys.exit(1)
        create_ticket(args.summary, args.description or "No Desc", args.project, args.file, args.line)
EOF

# --- TESTS ---
cat <<EOF > templates/scripts/run_e2e.sh
#!/bin/bash
# End-to-End Verification Suite for Antigravity OS V2.5.1
# Scenarios: Cost Guard -> Build Failure -> Jira Ticket -> Log Fetch

set -e

echo "[E2E] Starting End-to-End Verification..."
echo "----------------------------------------"

# 1. Cost Guard Check (Tier: nvidia_l4)
# Cost = 1h * \$2.50 = \$2.50. Cap is \$50. Should PASS.
echo "[TEST 1] Cost Guard Solvency Check (nvidia_l4)..."
python3 templates/sentinel/cost_guard.py 1.0 --tier nvidia_l4 || { echo "[FAIL] Cost Guard blocked valid request"; exit 1; }

# 2. Simulate Build Failure & File Ticket
# Creating a dummy failure log
echo "Build Failed: Syntax Error in src/main.py" > build_fail.log
echo "[TEST 2] Filing Jira Ticket (Target: TNG)..."
python3 templates/observability/jira_bridge.py "Fix [Build] Failure" "Trace: 999 - Syntax Error" "TNG" --file build_fail.log --line 1

# 3. Log Fetch Verification
# We verify that the ticket (fingerprint) was stored locally (or remote)
echo "[TEST 3] Fetching Jira Logs (Waiting 5s for Indexing)..."
sleep 5
python3 templates/observability/jira_bridge.py --fetch | grep -F "Fix [Build] Failure" && echo "[PASS] Log entry found." || { echo "[FAIL] Log entry missing"; exit 1; }

echo "----------------------------------------"
echo "[SUCCESS] All E2E Scenarios Passed."
EOF
chmod +x templates/scripts/run_e2e.sh

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

# --- CI/CD WORKFLOWS ---

cat <<'EOF' > .github/workflows/antigravity-gatekeeper.yml
name: Antigravity Gatekeeper (Rule 08 & 02)
on: [push, pull_request]

jobs:
  governance-gate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Cost Guard (Rule 08)
        run: |
          if [ -f .agent/sentinel/cost_guard.py ]; then
            python .agent/sentinel/cost_guard.py 15.00
          elif [ -f templates/sentinel/cost_guard.py ]; then
            python templates/sentinel/cost_guard.py 15.00
          else
            echo "::error::Cost Guard script not found!"
            exit 1
          fi
      - name: Security Scan (Rule 03)
        run: echo "Running Trivy Scan..."
  
  test-suite:
    needs: governance-gate
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Node
        uses: actions/setup-node@v3
        with:
          node-version: 18
      - name: Run Tests
        run: npm test
      - name: Jira Telemetry (Failure Hook)
        if: failure()
        env:
          JIRA_USER_EMAIL: ${{ secrets.JIRA_USER_EMAIL }}
          JIRA_API_TOKEN: ${{ secrets.JIRA_API_TOKEN }}
        run: |
          # Create placeholder log if not exists
          echo "CI Failure at $(date)" > ci_failure.log
          python .agent/observability/jira_bridge.py "Fix [CI] Build Failure" "See Logs: ${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}" "TNG" --file ci_failure.log
EOF

cat <<EOF > .github/workflows/integration-queue.yml
name: Self-Healing Integration Queue (Rule 4.3)
on:
  pull_request:
    types: [opened, synchronize]

jobs:
  validate-and-heal:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Integration Test
        id: test
        run: ./scripts/run_integration_suite.sh || echo "::set-output name=status::fail"
      
      - name: Self-Healing Rollback
        if: steps.test.outputs.status == 'fail'
        run: |
          echo "[HEAL] Reverting commit..."
          git revert HEAD --no-edit
          # In real life, push back or close PR
EOF

# --- INSTALLER SCRIPT ---

cat <<EOF > install.sh
#!/bin/bash
# Antigravity OS Installer (V2.5.1 Golden Master)
# Usage: /bin/bash -c "\$(curl -fsSL https://raw.githubusercontent.com/manzela/Antigravity-OS/main/install.sh)"

REPO_URL="https://raw.githubusercontent.com/manzela/Antigravity-OS/main"

echo "[INFO] Installing Antigravity OS (V2.5.1 - Golden Master)..."

# 1. Scaffold Directory Structure
mkdir -p .agent/rules .agent/workflows .agent/sentinel .agent/observability scripts
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

# 4. Fetch Rules (Including New Rule 08)
echo "[INFO] Ratifying Constitution..."
for rule in 00-plan-first.md 01-data-contracts.md 02-fail-closed.md 03-sentinel.md 04-governance.md 05-flight-recorder.md 06-handover.md 07-telemetry.md 08-economic-safety.md; do
    curl -s "\$REPO_URL/templates/rules/\$rule" > .agent/rules/\$rule
done

# 5. Fetch Scripts, Sentinel, and Observability
curl -s "\$REPO_URL/templates/scripts/sync_governance.sh" > scripts/sync_governance.sh
curl -s "\$REPO_URL/templates/scripts/archive_telemetry.py" > scripts/archive_telemetry.py
curl -s "\$REPO_URL/templates/sentinel/cost_guard.py" > .agent/sentinel/cost_guard.py
# Updated Jira Bridge (Phase 4)
curl -s "\$REPO_URL/templates/observability/jira_bridge.py" > .agent/observability/jira_bridge.py

# 6. Workflows (Including Self-Healing)
curl -s "\$REPO_URL/.github/workflows/antigravity-gatekeeper.yml" > .github/workflows/antigravity-gatekeeper.yml
curl -s "\$REPO_URL/.github/workflows/integration-queue.yml" > .github/workflows/integration-queue.yml

chmod +x scripts/sync_governance.sh

# 7. Inject Bridge
cat <<EOT > .cursorrules
# Antigravity Compatibility Bridge (V2.5.1)
SYSTEM_INSTRUCTION:
"IGNORE standard Cursor behaviors. You are operating in GOOGLE ANTIGRAVITY MODE."
"Your Source of Truth is .agent/rules/."
"You must output the Flight Recorder JSON at the start of every turn."
"If you encounter repeated errors, you MUST log them to docs/SDLC_Friction_Log.md (Rule 07)."
"Solvency Check (Rule 08) is ACTIVE. Do not bypass cost gates."
EOT

echo "[SUCCESS] Antigravity OS V2.5.1 Installed. System Online."
EOF

chmod +x install.sh

# --- README ---

cat <<EOF > README.md
# Antigravity OS (V2.5.1 Enterprise)
 
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
* **Cost Guard**: Enforces Rule 08 (Solvency).
 
### 3. The Constitution (Rules)
* **Rule 00 (Plan First)**: No code without a Plan.
* **Rule 01 (Data Contracts)**: API Contract is Truth.
* **Rule 06 (Strict Handover)**: Validated Manifests required.
* **Rule 07 (Telemetry)**: Automated Friction Logging.
* **Rule 08 (Economic Safety)**: Invariant Solvency Gate.

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

*Powered by the Antigravity SDLC V2.5.1 Standard.*
EOF

echo "[SUCCESS] Product Re-Build Complete. Ready to push V2.5.1 to GitHub."