import os
import sys
import json
import time
import uuid
import hashlib
from google.cloud import storage

# CONFIG
PROJECT_ID = os.getenv("GCP_PROJECT_ID")

def clean_logs(text):
    """Scrub emojis and non-ascii characters for professional logging."""
    if not text: return ""
    return text.encode('ascii', 'ignore').decode('ascii')

def build_thick_payload(trace_id, log_content):
    """Constructs the full Flight Recorder State Object schema."""
    timestamp_ns = int(time.time() * 1e9)
    span_id = uuid.uuid4().hex[:12]
    fingerprint = hashlib.sha256(log_content.encode()).hexdigest()
    
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
        "owner": os.getenv('JIRA_USER_EMAIL', 'unknown'),
        "cost_estimate": 0.0,
        "handover_manifest": {
            "build_image_digest": os.getenv("BUILD_DIGEST", "sha256:unknown"),
            "plan_md_path": "implementation_plan.md",
            "api_contract_version": "v3.5",
            "test_suite_id": "antigravity-e2e",
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
            "test.suite.name": "orchestrator-archive",
            "test.result": "fail",
            "owner": os.getenv('JIRA_USER_EMAIL', 'unknown')
        },
        "logs": [
            {
                "timestamp": time.strftime('%Y-%m-%dT%H:%M:%S.000Z', time.gmtime()),
                "severity": "ERROR",
                "attributes": {
                    "exception.type": "RuntimeError"
                },
                "body": clean_logs(log_content)
            }
        ]
    }
    return flight_recorder_event

def archive_log(trace_id, log_content):
    if not PROJECT_ID:
        print("⚠️ [STORAGE] Missing GCP_PROJECT_ID. Skipping upload.")
        return

    bucket_name = f"antigravity-logging-{PROJECT_ID}"
    
    try:
        client = storage.Client(project=PROJECT_ID)
        bucket = client.bucket(bucket_name)
        
        blob_name = f"crash-{trace_id}.json"
        blob = bucket.blob(blob_name)
        
        # Build Thick Payload
        payload_obj = build_thick_payload(trace_id, log_content)
        payload_json = json.dumps(payload_obj, indent=2)
        
        blob.upload_from_string(payload_json, content_type="application/json")
        print(f"📦 [STORAGE] Archived log to gs://{bucket_name}/{blob_name}")
        
    except Exception as e:
        print(f"⚠️ [STORAGE] Upload failed: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 archive_telemetry.py <trace_id> <log_content>")
        sys.exit(1)
        
    t_id = sys.argv[1]
    l_content = sys.argv[2]
    
    archive_log(t_id, l_content)
