import sys
import hashlib
import subprocess
import os
import json
import base64
import argparse

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

def create_rich_description(summary, description, log_content, owner_name, owner_email, fingerprint):
    """R 5.1 Rich Context: Generate Professional ADF Description (No Emojis)."""
    
    # Truncate log if too long (Jira limit)
    if len(log_content) > 2000:
        log_content = log_content[:2000] + "... [TRUNCATED]"

    content = [
        # Section 1: Issue Summary
        {
            "type": "heading",
            "attrs": {"level": 3},
            "content": [{"type": "text", "text": "Issue Summary"}]
        },
        {
            "type": "paragraph",
            "content": [{"type": "text", "text": description}]
        },
        # Section 2: Diagnostics
        {
            "type": "heading",
            "attrs": {"level": 3},
            "content": [{"type": "text", "text": "Diagnostics"}]
        },
        {
            "type": "bulletList",
            "content": [
                {"type": "listItem", "content": [{"type": "paragraph", "content": [{"type": "text", "text": f"Error Fingerprint: {fingerprint}"}]}]},
                {"type": "listItem", "content": [{"type": "paragraph", "content": [{"type": "text", "text": f"Detected Owner: {owner_name} ({owner_email})"}]}]},
                {"type": "listItem", "content": [{"type": "paragraph", "content": [{"type": "text", "text": f"Component: DevOps / Infrastructure"}]}]}
            ]
        },
        # Section 3: System Logs
        {
            "type": "heading",
            "attrs": {"level": 3},
            "content": [{"type": "text", "text": "System Logs / Stack Trace"}]
        },
        {
            "type": "codeBlock",
            "attrs": {"language": "text"},
            "content": [{"type": "text", "text": log_content or "No logs provided."}]
        },
        # Section 4: Suggested Action
        {
            "type": "heading",
            "attrs": {"level": 3},
            "content": [{"type": "text", "text": "Suggested Action"}]
        },
        {
            "type": "paragraph",
            "content": [{"type": "text", "text": "Please review the attached logs and the commit history. Verify syntax and configuration files."}]
        }
    ]
    
    return {"type": "doc", "version": 1, "content": content}

def create_ticket(summary, description, project_id, filepath=None, line=1, log_file=None):
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
    error_fingerprint = hashlib.md5(f"{summary}|{description}".encode()).hexdigest()
    
    # Mock Fallback
    if not headers:
        print(f"[MOCK-JIRA] Would create ticket: {summary}")
        with open(MOCK_JIRA_DB, "a") as f:
            f.write(f"[{project_id}] {summary} (Owner: {owner_email}) | FP: {error_fingerprint}\n")
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

    # Create Issue Payload
    desc_doc = create_rich_description(summary, description, log_content, owner_name, owner_email, error_fingerprint)
    
    payload = {
        "fields": {
            "project": {"key": PROJECT_KEY},
            "summary": summary,
            "description": desc_doc,
            "issuetype": {"name": "Task"},
            "priority": {"id": "2"}, # High Priority
            "labels": ["auto-generated", "build-failure", "blocking", f"fp:{error_fingerprint}"],
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
    
    args = parser.parse_args()
    
    if args.fetch:
        fetch_logs(get_credentials())
    else:
        if not args.summary:
             if get_credentials(): print("[INFO] Auth Valid."); sys.exit(0)
             else: sys.exit(1)
        create_ticket(args.summary, args.description or "No Desc", args.project, args.file, args.line, args.log_file)
