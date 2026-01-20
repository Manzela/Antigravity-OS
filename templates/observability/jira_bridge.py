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
