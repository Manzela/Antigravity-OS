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
