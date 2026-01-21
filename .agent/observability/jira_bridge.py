import os
import hashlib
import redis
import json

r = redis.Redis(host=os.getenv('REDIS_HOST', 'localhost'), port=6379, db=0)

def handle_failure(source, error_log, trace_id):
    # 1. Semantic Deduplication
    fingerprint = hashlib.sha256(f"{source}:{error_log[:200]}".encode()).hexdigest()
    cache_key = f"jira:issue:{fingerprint}"

    if r.exists(cache_key):
        count = r.incr(f"jira:count:{fingerprint}")
        print(f"[IMMUNE] Suppressed Duplicate Error (Count: {count})")
        return

    # 2. Hybrid Schema
    payload = {
        "trace_id": trace_id,
        "fingerprint": fingerprint,
        "ai_trace": "langfuse-link-pending"
    }

    print(f"[ALERT] New Incident Created: {json.dumps(payload)}")
    r.setex(cache_key, 604800, "TICKET-PENDING")
