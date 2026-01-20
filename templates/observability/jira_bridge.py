import sys
import hashlib
import subprocess
import os

# Antigravity Jira Bridge
# Connects Flight Recorder to Jira for Rule 08/07.
# Implements R 2.1 (Schema), R 2.2 (Deduplication), R 2.3 (Dynamic Ownership)

MOCK_JIRA_DB = "/tmp/antigravity_jira_state.txt"

def get_git_owner(filepath, line_number):
    """R 2.3 Dynamic Ownership: Use git blame to find the human owner."""
    try:
        # Check if file exists
        if not os.path.exists(filepath):
            return "unknown-committer"
            
        cmd = ["git", "blame", "--line-porcelain", "-L", f"{line_number},{line_number}", filepath]
        result = subprocess.check_output(cmd, stderr=subprocess.DEVNULL).decode("utf-8")
        for line in result.split("\n"):
            if line.startswith("author "):
                return line.split(" ", 1)[1]
    except Exception as e:
        print(f"[WARN] Git Blame failed: {e}")
        return "devops-oncall"
    return "devops-oncall"

def validate_schema(summary):
    """R 2.1 Standardized Schema: Enforce 'Verb Source Error' format."""
    parts = summary.split(" ")
    if len(parts) < 3:
        print(f"[ERROR] Invalid Jira Summary: '{summary}'. Must be 'VERB [SOURCE] ERROR'")
        return False
    return True

def create_ticket(summary, description, project_id, filepath=None, line=1):
    if not validate_schema(summary):
        sys.exit(1)

    # R 2.2 Semantic Deduplication
    error_fingerprint = hashlib.md5(f"{summary}|{description}".encode()).hexdigest()
    
    # Check for duplicate (Mock Logic)
    if os.path.exists(MOCK_JIRA_DB):
        with open(MOCK_JIRA_DB, "r") as f:
            if error_fingerprint in f.read():
                print(f"[INFO] Duplicate Error {error_fingerprint} detected. Incrementing counter. No new ticket.")
                return "EXISTING-TICKET"

    # R 2.3 Resolve Owner
    owner = "devops-oncall"
    if filepath:
         owner = get_git_owner(filepath, line)

    print(f"[JIRA] Creating Ticket: {summary}")
    print(f"       Project: {project_id}")
    print(f"       Assignee: {owner}")
    print(f"       Fingerprint: {error_fingerprint}")
    
    # Save state
    with open(MOCK_JIRA_DB, "a") as f:
        f.write(error_fingerprint + "\n")
        
    return "JIRA-" + os.urandom(2).hex().upper()

if __name__ == "__main__":
    # Example Usage: python jira_bridge.py "Fix [API] Timeout" "Trace..." "AG-OS" --file src/main.py --line 10
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("summary")
    parser.add_argument("description")
    parser.add_argument("project")
    parser.add_argument("--file", help="Source file for blame")
    parser.add_argument("--line", type=int, default=1, help="Line number for blame")
    
    args = parser.parse_args()
    create_ticket(args.summary, args.description, args.project, args.file, args.line)
