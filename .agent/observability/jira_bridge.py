import os, hashlib, redis, json
from jira import JIRA

# CONFIG
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', None)
JIRA_SERVER = "https://tngshopper.atlassian.net"
JIRA_USER = os.getenv('JIRA_USER_EMAIL')
JIRA_TOKEN = os.getenv('JIRA_API_TOKEN')
PROJECT_KEY = os.getenv('JIRA_PROJECT_KEY', 'TNG') # Enforced TNG

def get_redis():
    return redis.Redis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD, db=0)

def handle_failure(source, error_log, trace_id):
    r = get_redis()
    # 1. Deduplication
    fingerprint = hashlib.sha256(f"{source}:{error_log[:200]}".encode()).hexdigest()
    cache_key = f"jira:issue:{fingerprint}"
    
    if r.exists(cache_key):
        print(f"🛡️ [IMMUNE] Duplicate suppressed.")
        return

    # 2. Create Ticket
    print(f"🚨 [JIRA] Opening ticket in {PROJECT_KEY}...")
    try:
        jira = JIRA(server=JIRA_SERVER, basic_auth=(JIRA_USER, JIRA_TOKEN))
        summary = f"[{source}] Automated Alert: {error_log[:50]}..."
        description = f"Trace ID: {trace_id}\n\nError:\n{error_log}"
        
        issue = jira.create_issue(
            project=PROJECT_KEY,
            summary=summary,
            description=description,
            issuetype={'name': 'Bug'},
            labels=['antigravity-auto']
        )
        print(f"✅ [JIRA] Created {issue.key}")
        r.setex(cache_key, 604800, issue.key)
    except Exception as e:
        print(f"⚠️ [JIRA FAIL] {e}")
