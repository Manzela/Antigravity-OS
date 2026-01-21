import os, hashlib, redis, json, time, uuid
from jira import JIRA

# CONFIG
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', None)
JIRA_SERVER = "https://tngshopper.atlassian.net"
JIRA_USER = os.getenv('JIRA_USER_EMAIL')
JIRA_TOKEN = os.getenv('JIRA_API_TOKEN')
PROJECT_KEY = "TNG"

def get_redis():
    return redis.Redis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD, db=0)

def clean_logs(text):
    """Scrub emojis and non-ascii characters for professional logging."""
    if not text: return ""
    return text.encode('ascii', 'ignore').decode('ascii')

def handle_failure(source, error_log, trace_id):
    try:
        r = get_redis()
        # 1. Deduplication using full log content
        fingerprint = hashlib.sha256(f"{source}:{error_log}".encode()).hexdigest()
        cache_key = f"jira:issue:{fingerprint}"
        
        if r.exists(cache_key):
            print(f"🛡️ [IMMUNE] Duplicate suppressed.")
            return

        # 2. Universal Schema Construction
        # Enforce strict field population
        clean_error = clean_logs(error_log)
        timestamp_ns = int(time.time() * 1e9)
        span_id = uuid.uuid4().hex[:12] 
        
        # Flight Recorder State Object
        flight_recorder_event = {
            "trace_id": trace_id,
            "span_id": span_id,
            "parent_span_id": None,
            "start_time_unix_nano": timestamp_ns,
            "end_time_unix_nano": timestamp_ns,
            "status": {
                "code": "Critical"
            },
            "loop_count": 0,
            "owner": JIRA_USER or "unknown",
            "cost_estimate": 0.0,
            "handover_manifest": {
                "build_image_digest": os.getenv("BUILD_DIGEST", "sha256:unknown"),
                "plan_md_path": "implementation_plan.md",
                "api_contract_version": "v3.5",
                "test_suite_id": f"antigravity-test-{source.replace(' ', '-').lower()}",
                "preview_url": "",
                "solvency_token": "valid"
            },
            "feedback_chain": [],
            "resource": {
                "service.name": "flight-recorder-service",
                "service.version": "3.5.0",
                "deployment.environment.name": os.getenv("DEPLOY_ENV", "local-development"),
                "vcs.repository.url.full": "https://github.com/Manzela/Antigravity-OS",
                "vcs.ref.head.name": "Upgraded-V3.5",
                "vcs.revision.id": fingerprint[:7],
                "cicd.pipeline.name": "antigravity-gatekeeper",
                "artifact.name": "antigravity-installer"
            },
            "attributes": {
                "test.suite.name": source,
                "test.result": "fail",
                "owner": JIRA_USER or "unknown"
            },
            "logs": [
                {
                    "timestamp": time.strftime('%Y-%m-%dT%H:%M:%S.000Z', time.gmtime()),
                    "severity": "ERROR",
                    "attributes": {
                        "exception.type": "RuntimeError"
                    },
                    "body": clean_error
                }
            ]
        }

        # 3. Create Ticket with Schema
        print(f"🚨 [JIRA] Opening ticket in {PROJECT_KEY}...")
        jira = JIRA(server=JIRA_SERVER, basic_auth=(JIRA_USER, JIRA_TOKEN))
        summary = f"[{source}] Automated Alert: {clean_error[:50]}..."
        
        description = f"h3. Flight Recorder Event\n{{code:json}}\n{json.dumps(flight_recorder_event, indent=2)}\n{{code}}"
        
        issue = jira.create_issue(
            project=PROJECT_KEY,
            summary=summary,
            description=description,
            issuetype={'name': 'Bug'},
            labels=['antigravity-auto']
        )
        print(f"✅ [JIRA] Created {issue.key}")
        # Prevent spam for 7 days
        r.setex(cache_key, 604800, issue.key)
        
    except Exception as e:
        print(f"⚠️ [JIRA FAIL] Could not create ticket: {e}")
