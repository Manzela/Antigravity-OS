import sys
import hashlib
import subprocess
import os
import json
import base64
import argparse
import platform
import datetime
import time
import uuid

# Antigravity Jira Bridge V2.5.1 (Enterprise Edition)
# Connects Flight Recorder to Atlassian Jira (Cloud)
# Implements Real-Time Telemetry, Deduplication, Smart Assignment, and ADF Reporting

JIRA_BASE_URL = "https://tngshopper.atlassian.net"
PROJECT_KEY = "TNG"
MOCK_JIRA_DB = "/tmp/antigravity_jira_state.txt"

def get_credentials():
    email = os.getenv("JIRA_USER_EMAIL")
    token = os.getenv("JIRA_API_TOKEN")
    if not email or not token:
        if os.getenv("CI"):
            print("[WARN] CI Detected but Credentials Missing. Telemetry Disabled.")
        return None
    
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
        result = subprocess.check_output(cmd, stderr=subprocess.PIPE).decode("utf-8")
        if not result: return None
        return json.loads(result)
    except Exception as e:
        print(f"[ERROR] Curl Request Failed: {e}")
        return None

def find_user_by_email(headers, email):
    """R 2.3 Smart Assignment: Find Jira Account ID by Email."""
    if not email or "@" not in email: return None
    import urllib.parse
    query = f"/rest/api/3/user/search?query={urllib.parse.quote(email)}"
    resp = make_request("GET", query, headers)
    if resp and len(resp) > 0:
        return resp[0].get("accountId")
    return None

def get_git_info(filepath, line_number):
    """R 2.3 Dynamic Ownership: Use git blame to find author email and name."""
    if not filepath or not os.path.exists(filepath): 
        return "Unknown", "devops-oncall@tngshopper.com"
    try:
        cmd = ["git", "blame", "--line-porcelain", "-L", f"{line_number},{line_number}", filepath]
        result = subprocess.check_output(cmd, stderr=subprocess.PIPE).decode("utf-8")
        author_name = "Unknown"
        author_email = "devops-oncall@tngshopper.com"
        for line in result.split("\n"):
            if line.startswith("author "):
                author_name = line.split(" ", 1)[1]
            if line.startswith("author-mail "):
                author_email = line.split(" ", 1)[1].strip("<>")
        return author_name, author_email
    except:
        return "git-error", "devops-oncall@tngshopper.com"

def construct_flight_recorder_payload(trace_id, git_hash, log_content, owner, status_code="Error"):
    """R 6.5 Advanced Schema Enforcement: OpenTelemetry-style Flight Recorder."""
    
    # Generate Spans
    span_id = uuid.uuid4().hex[:16]
    start_ns = time.time_ns()
    end_ns = start_ns + 1000000000 # Mock 1s duration
    
    # Context
    repo = os.getenv("GITHUB_REPOSITORY", "Manzela/Antigravity-OS")
    server = os.getenv("GITHUB_SERVER_URL", "https://github.com")
    run_id = os.getenv("GITHUB_RUN_ID", "local-run")
    ref = os.getenv("GITHUB_REF_NAME", "unknown-branch")

    return {
      "trace_id": trace_id,
      "span_id": span_id,
      "parent_span_id": None, # Root span
      "start_time_unix_nano": start_ns,
      "end_time_unix_nano": end_ns,
      "status": { "code": status_code },
      "resource": {
        "service.name": "flight-recorder-service",
        "service.version": "2.1.0",
        "deployment.environment.name": "production",
        
        # VCS
        "vcs.repository.url.full": f"{server}/{repo}",
        "vcs.ref.head.name": ref,
        "vcs.revision.id": git_hash,

        # CI/CD
        "cicd.pipeline.name": "antigravity-gatekeeper",
        "cicd.pipeline.run.id": run_id,
        
        # Artifact
        "artifact.name": "antigravity-installer",
        "artifact.version": "2.5.1",
        "container.image.name": "flight-recorder",
        "container.image.tags": ["v2.5.1", "latest"]
      },
      "attributes": {
        "test.suite.name": "antigravity-e2e",
        "test.result": "fail" if status_code == "Error" else "pass",
        "owner": owner
      },
      "logs": [
        { 
          "timestamp": datetime.datetime.now(datetime.UTC).isoformat() + "Z", 
          "body": log_content, 
          "severity": "ERROR",
          "attributes": { "exception.type": "RuntimeError" } 
        }
      ]
    }

def upload_to_gcs(payload, bucket_name, trace_id):
    """R 6.5 Upload validated JSON payload to GCS."""
    if not bucket_name or not trace_id: return None
    
    filename = f"trace_{trace_id}.json"
    local_path = f"/tmp/{filename}"
    gcs_path = f"{bucket_name}/{filename}"
    
    try:
        with open(local_path, "w") as f:
            json.dump(payload, f, indent=2)
            
        cmd = ["gsutil", "cp", local_path, gcs_path]
        subprocess.check_call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Construct HTTPS Link
        # Pattern: https://storage.cloud.google.com/<bucket>/<file>
        # Strip gs:// prefix if present
        clean_bucket = bucket_name.replace("gs://", "")
        return f"https://storage.cloud.google.com/{clean_bucket}/{filename}"
    except Exception as e:
        print(f"[WARN] GCS Upload Failed: {e}")
        return None

# --- ADF Helper Functions ---
def adf_text(text, marks=None):
    content = {"type": "text", "text": text}
    if marks: content["marks"] = marks
    return content

def adf_paragraph(content_list):
    # content_list can be a list of dicts (nodes) or strings
    nodes = []
    for item in content_list:
        if isinstance(item, str): nodes.append(adf_text(item))
        else: nodes.append(item)
    return {"type": "paragraph", "content": nodes}

def adf_heading(text, level=3):
    return {
        "type": "heading",
        "attrs": {"level": level},
        "content": [adf_text(text)]
    }

def adf_code_block(text, language="text"):
    return {
        "type": "codeBlock",
        "attrs": {"language": language},
        "content": [adf_text(text or "")]
    }

def adf_table_row(cells, header=False):
    cell_type = "tableHeader" if header else "tableCell"
    row_content = []
    for cell_content in cells:
        # If cell_content is a string, wrap in paragraph
        if isinstance(cell_content, str):
            inner = [adf_paragraph([adf_text(cell_content, marks=[{"type": "strong"}] if header else None)])]
        elif isinstance(cell_content, list): # List of nodes
             inner = cell_content
        else:
             inner = [cell_content] # Single node
             
        row_content.append({
            "type": cell_type,
            "attrs": {},
            "content": inner
        })
    return {"type": "tableRow", "content": row_content}

def adf_table(rows):
    # Rows should be list of lists of strings/content
    # First row is treated as header if we want, but for flexibility let's assume rows are already processed or we check first
    # Ref: Our usage passes strings usually.
    return {
        "type": "table",
        "attrs": {"isNumberColumnEnabled": False, "layout": "default", "width": 100},
        "content": rows
    }

def adf_task_item(text, state="TODO"):
    return {
        "type": "taskItem",
        "attrs": {"state": state},
        "content": [adf_paragraph([text])]
    }

def adf_task_list(items):
    return {
        "type": "taskList",
        "attrs": {"localId": uuid.uuid4().hex},
        "content": items
    }

def create_rich_description(summary, description, log_content, owner_name, owner_email, fingerprint, gcs_link, env_info, repro_cmd):
    """R 5.1 Rich Context: Generate Professional ADF Description (No Emojis)."""
    
    # Truncate log if too long (Jira limit)
    if len(log_content) > 2000:
        log_content = log_content[:2000] + "... [TRUNCATED]"

    content = []

    # Section 1: System Impact & Governance Metadata (Table)
    content.append(adf_heading("System Impact & Governance", 3))

    # Governance Table Data
    gov_rows_data = [
        ["Attribute", "Value"],
        ["Execution Model", "Deterministic"],
        ["Failure Mode", "Fail-Closed"],
        ["Risk Level", "High (Blocking CI)" if "blocking" in description.lower() else "Medium"],
        ["Compliance Rule", "R-02, R-08"],
        ["Owner", f"{owner_name} ({owner_email})"],
        ["Error Fingerprint", fingerprint]
    ]

    gov_table_rows = [adf_table_row(gov_rows_data[0], header=True)]
    for r in gov_rows_data[1:]:
        gov_table_rows.append(adf_table_row(r))

    content.append(adf_table(gov_table_rows))

    # Section 2: Environment Specification & Reproduction
    content.append(adf_heading("Environment & Reproduction", 3))
    
    # Env Table Data
    env_rows_data = [["Context", "Details"]] + [[k, v] for k, v in env_info.items()]
    env_table_rows = [adf_table_row(env_rows_data[0], header=True)]
    for r in env_rows_data[1:]:
        env_table_rows.append(adf_table_row(r))
        
    content.append(adf_table(env_table_rows))

    # Diagnosis / Logs
    if gcs_link:
         link_mark = [{"type": "link", "attrs": {"href": gcs_link}}]
         content.append(adf_paragraph([
             "Full Log Archive: ", 
             adf_text("Download from GCS", marks=link_mark)
         ]))

    content.append(adf_heading("Reproduction Command", 4))
    content.append(adf_code_block(repro_cmd, "bash"))

    content.append(adf_heading("System Logs / Stack Trace", 4))
    content.append(adf_code_block(log_content or "No logs provided."))

    # Section 3: Acceptance Criteria (Definition of Done)
    content.append(adf_heading("Acceptance Criteria (Definition of Done)", 3))
    
    ac_texts = [
        "Root cause identified and documented",
        "Fix implemented in local environment",
        "Reproduction command now passes",
        "New regression test added (if applicable)",
        "CI Pipeline passing",
        "Code reviewed by peer"
    ]
    
    task_items = [adf_task_item(t) for t in ac_texts]
    content.append(adf_task_list(task_items))
    
    return {"type": "doc", "version": 1, "content": content}

def create_ticket(summary, description, project_id, filepath=None, line=1, log_file=None, gcs_bucket=None):
    headers = get_credentials()
    
    # Ingestion: Read Logs
    log_content = ""
    if log_file and os.path.exists(log_file):
        try:
            with open(log_file, "r") as f:
                log_content = f.read()
        except:
            log_content = "[ERROR] Could not read log file."

    # Traceability
    owner_name, owner_email = get_git_info(filepath, line)
    # Get Git Hash
    try:
        git_hash = subprocess.check_output(["git", "rev-parse", "HEAD"], stderr=subprocess.PIPE).decode("utf-8").strip()
    except:
        git_hash = "unknown"
        
    try:
        git_branch = subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"], stderr=subprocess.PIPE).decode("utf-8").strip()
    except:
        git_branch = "unknown"

    # Environment Info
    env_info = {
        "OS": f"{platform.system()} {platform.release()}",
        "Python": platform.python_version(),
        "Git Branch": git_branch,
        "Git Commit": git_hash,
        "CI Context": "Yes" if os.getenv("CI") else "Local Development"
    }
    
    # Reproduction Command
    reproduce_cmd = f"git checkout {git_hash}\n"
    if filepath:
        if filepath.endswith(".py"):
             reproduce_cmd += f"python3 {filepath} # (Check line {line})"
        elif filepath.endswith(".sh"):
             reproduce_cmd += f"bash {filepath}"
        elif filepath.endswith(".js"):
             reproduce_cmd += f"node {filepath}"
        else:
             reproduce_cmd += f"cat {filepath} # (Inspect file)"
    else:
        reproduce_cmd += "./build_product.sh # (or relevant script)"

    trace_id = os.getenv("TRACE_ID", hashlib.md5(f"{summary}{description}".encode()).hexdigest()[:8])
    error_fingerprint = hashlib.md5(f"{summary}|{description}".encode()).hexdigest()
    
    # Schema Enforcement & Upload
    gcs_link = None
    if gcs_bucket:
        payload = construct_flight_recorder_payload(trace_id, git_hash, log_content, owner_email)
        print(f"[TRACE] Uploading Flight Recorder Payload to {gcs_bucket}...")
        gcs_link = upload_to_gcs(payload, gcs_bucket, trace_id)
    
    # Create Issue Payload
    desc_doc = create_rich_description(summary, description, log_content, owner_name, owner_email, error_fingerprint, gcs_link, env_info, reproduce_cmd)
    
    # Handle Project ID
    target_project = project_id if project_id else PROJECT_KEY

    # Mock Fallback
    if not headers:
        print(f"[MOCK-JIRA] Would create ticket: {summary}")
        # Validate JSON serialization for debug
        try:
             json.dumps(desc_doc)
        except Exception as e:
             print(f"[ERROR] ADF Serialization Failed: {e}")
             
        with open(MOCK_JIRA_DB, "a") as f:
            f.write(f"[{target_project}] {summary} (Owner: {owner_email}) | FP: {error_fingerprint}\n")
        return "MOCK-123"

    # Smart Assignment
    assignee_id = find_user_by_email(headers, owner_email)
    
    # Deduplication
    print("[JIRA] Checking for duplicates...")
    existing = find_duplicate_issue(headers, error_fingerprint) # Re-use existing func logic (assumed in scope)
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
    
    payload = {
        "fields": {
            "project": {"key": target_project},
            "summary": summary,
            "description": desc_doc,
            "issuetype": {"name": "Task"},
            "priority": {"id": "2"}, # High Priority
            "labels": ["auto-generated", "build-failure", "blocking", "governance-enforced", "fail-closed", f"fp:{error_fingerprint}"],
            # Note: "components" field varies by project. Omitting to avoid API 400 if not exists.
        }
    }
    
    if assignee_id:
        payload["fields"]["assignee"] = {"id": assignee_id}
    
    print(f"[JIRA] Creating Ticket in {PROJECT_KEY}...")
    resp = make_request("POST", "/rest/api/3/issue", headers, payload)
    if resp and "key" in resp:
        print(f"[SUCCESS] Created {resp['key']}")
        return resp['key']
    else:
        print("[FAIL] Could not create ticket.")
        # print(resp) # Debug
        sys.exit(1)

# Helper for deduplication (same as V4)
def find_duplicate_issue(headers, fingerprint):
    import urllib.parse
    jql = f"project = {PROJECT_KEY} AND labels = \"fp:{fingerprint}\""
    resp = make_request("GET", f"/rest/api/3/search?jql={urllib.parse.quote(jql)}", headers)
    if resp and resp.get("total", 0) > 0:
        return resp["issues"][0]
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

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("summary", nargs="?")
    parser.add_argument("description", nargs="?")
    parser.add_argument("project", nargs="?")
    parser.add_argument("--fetch", action="store_true", help="Fetch ticket logs")
    parser.add_argument("--file", help="Source file for blame")
    parser.add_argument("--line", type=int, default=1, help="Line number for blame")
    parser.add_argument("--log-file", help="Path to log file for ingestion")
    parser.add_argument("--gcs-bucket", help="Target GCS Bucket for Flight Recorder Payload")
    
    args = parser.parse_args()
    
    if args.fetch:
        fetch_logs(get_credentials())
    else:
        if not args.summary:
             if get_credentials(): print("[INFO] Auth Valid."); sys.exit(0)
             else: sys.exit(1)
        create_ticket(args.summary, args.description or "No Desc", args.project, args.file, args.line, args.log_file, args.gcs_bucket)
