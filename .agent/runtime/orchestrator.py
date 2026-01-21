import subprocess
import sys
import os
import time
import json
import uuid
import requests
import redis

# FIX: Robust Import Logic for Hidden Directory
current_dir = os.path.dirname(os.path.abspath(__file__))
security_dir = os.path.join(current_dir, '../security')
observability_dir = os.path.join(current_dir, '../observability')
sys.path.append(security_dir)
sys.path.append(observability_dir)

import scrubber
# jira_bridge is imported dynamically on failure

OPA_URL = "http://localhost:8181/v1/data/antigravity/governance"
TRACE_ID = str(uuid.uuid4())
MAX_RETRIES = 2  # The Optimization Factor

def get_changed_files():
    """Real Input: Extract context from Git"""
    try:
        cmd = "git diff --name-only HEAD"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return [f for f in result.stdout.strip().split('\n') if f]
    except: return []

def check_governance():
    """Protocol F: Check Policy Engine"""
    files = get_changed_files()
    if not files: return False
    try:
        payload = {"input": {"files": files}} 
        res = requests.post(OPA_URL, json=payload).json()
        if res.get("result", {}).get("skip_gates"):
            print(f"[OPA] Skipping gates (Protocol F) - Docs Only.")
            return True
    except: pass
    return False

def run_phase(name, cmd):
    print(f"[ORCHESTRATOR] Executing: {name}...")
    
    # Risk R-Infra-01: Zero-Touch Wrapper (No K8s required)
    instrumented_cmd = (
        f"opentelemetry-instrument "
        f"--service_name antigravity-agent "
        f"--traces_exporter otlp "
        f"{cmd}"
    )
    
    start = time.time()
    result = subprocess.run(instrumented_cmd, shell=True, capture_output=True, text=True)
    safe_log = scrubber.scrub_payload(result.stderr + result.stdout)
    
    return {
        "success": result.returncode == 0,
        "log": safe_log,
        "duration": time.time() - start
    }

def main():
    print(f"[BRAIN] Active. Trace: {TRACE_ID}")
    
    if check_governance():
        print("[GOVERNANCE] Gates bypassed per Protocol F.")
        sys.exit(0)

    phases = [
        ("Cost Guard", "echo 'Simulating Infracost'"), 
        ("Build & Test", "pytest tests/")
    ]
    
    for name, cmd in phases:
        # THE OPTIMIZATION LOOP (Heal)
        attempt = 0
        success = False
        while attempt <= MAX_RETRIES and not success:
            telemetry = run_phase(name, cmd)
            if telemetry["success"]:
                print(f"[PASS] {name} ({telemetry['duration']:.2f}s)")
                success = True
            else:
                attempt += 1
                print(f"[WARN] {name} Failed. Self-Healing Attempt {attempt}/{MAX_RETRIES}...")
                time.sleep(1) # Backoff
        
        if not success:
            print(f"[FAIL] {name} Unrecoverable.")
            import jira_bridge
            jira_bridge.handle_failure(name, telemetry["log"], TRACE_ID)
            sys.exit(1)

if __name__ == "__main__":
    main()
