import os
import sys
from jira import JIRA

# Ticket list provided by Forensic Audit
SPAM_TICKETS = [
    "TNG-41", "TNG-40", "TNG-39", "TNG-32",
    "TNG-42", "TNG-43", "TNG-44", "TNG-45", "TNG-46", "TNG-47", "TNG-48", "TNG-49", "TNG-50", "TNG-51", "TNG-52", "TNG-53", "TNG-54", "TNG-55", "TNG-56", "TNG-57", "TNG-58", "TNG-59", "TNG-62",
    "TNG-66", "TNG-67", "TNG-68", "TNG-69", "TNG-70", "TNG-71", "TNG-72", "TNG-73", "TNG-74", "TNG-75", "TNG-76", "TNG-77", "TNG-78"
]

def load_env_file(filepath):
    """Manually load .env variables if not present."""
    if not os.path.exists(filepath):
        return
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' in line:
                key, value = line.split('=', 1)
                # Remove quotes if present
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                os.environ[key] = value

def main():
    print("🧹 Antigravity Jira Cleaner")
    print("-------------------------")
    
    # Load .env relative to script location (../.env)
    env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '.env'))
    load_env_file(env_path)

    server = "https://manzela.atlassian.net"
    email = os.environ.get("JIRA_USER_EMAIL")
    token = os.environ.get("JIRA_API_TOKEN")

    if not email or not token:
        print("❌ Error: JIRA_USER_EMAIL or JIRA_API_TOKEN not found in environment.")
        print("👉 Run ./utils/seed_secrets.sh then ./install.sh first.")
        sys.exit(1)

    try:
        print(f"🔌 Connecting to {server} as {email}...")
        jira = JIRA(server=server, basic_auth=(email, token))
        
        success_count = 0
        fail_count = 0

        for ticket_id in SPAM_TICKETS:
            print(f"   🗑️  Processing {ticket_id}...", end=" ")
            try:
                issue = jira.issue(ticket_id)
                issue.delete()
                print("✅ Deleted")
                success_count += 1
            except Exception as e:
                if "404" in str(e):
                    print("⚠️  Not Found (Already deleted?)")
                else:
                    print(f"❌ Error: {str(e)}")
                fail_count += 1
        
        print("-------------------------")
        print(f"🏁 Cleanup Complete. Deleted: {success_count} | Failed/Skipped: {fail_count}")

    except Exception as e:
        print(f"\n❌ Critical Connection Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
