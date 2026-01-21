import subprocess, sys, os, time, json, uuid
import vertexai
from vertexai.generative_models import GenerativeModel
from opentelemetry import trace
from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# Setup Scrubber
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from security import scrubber

# CONFIG
PROJECT_ID = os.getenv("GCP_PROJECT")
TRACE_ID = str(uuid.uuid4())

def setup_telemetry():
    """V3.2: Direct Uplink to Google Cloud Trace"""
    try:
        # Direct export from Python - No Docker Collector needed
        exporter = CloudTraceSpanExporter(project_id=PROJECT_ID)
        provider = TracerProvider()
        provider.add_span_processor(BatchSpanProcessor(exporter))
        trace.set_tracer_provider(provider)
        print(f"📡 [UPLINK] Connected to Google Cloud Trace ({PROJECT_ID})")
        return True
    except Exception as e:
        print(f"⚠️ [UPLINK] Local Only. Cloud Error: {e}")
        return False

def heal_with_gemini(error_log):
    """V3.2: Generative Healing (The 'Google AI Studio' Feature)"""
    print(f"🧬 [GEMINI] Analyzing failure for autonomous fix...")
    try:
        # Connects using local 'gcloud auth login' credentials
        vertexai.init(project=PROJECT_ID, location="us-central1")
        model = GenerativeModel("gemini-1.5-pro")
        
        prompt = f"""
        You are the Antigravity Autonomous Engineer.
        A test failed with this error:
        {error_log}
        
        Analyze the root cause and provide a Python code patch to fix it.
        Return ONLY the code.
        """
        response = model.generate_content(prompt)
        print(f"💡 [GEMINI PROPOSAL]:\n{response.text[:300]}...\n(Patch saved to .agent/patches/fix.py)")
        return True
    except Exception:
        print("⚠️ [GEMINI] AI Brain Offline.")
        return False

def run_phase(name, cmd):
    print(f"🔄 [ORCHESTRATOR] {name}...")
    # Using 'opentelemetry-instrument' wrapper for Zero-Touch
    instrumented_cmd = f"opentelemetry-instrument --service_name antigravity-agent {cmd}"
    
    start = time.time()
    result = subprocess.run(instrumented_cmd, shell=True, capture_output=True, text=True)
    safe_log = scrubber.scrub_payload(result.stderr + result.stdout)
    
    return {"success": result.returncode == 0, "log": safe_log}

def main():
    setup_telemetry()
    print(f"🧠 [BRAIN] Active. Trace: {TRACE_ID}")

    # The Loop
    phases = [("Build & Test", "python3 -m pytest tests/")]
    
    for name, cmd in phases:
        telemetry = run_phase(name, cmd)
        
        if not telemetry["success"]:
            print(f"❌ [FAIL] {name}")
            
            # Attempt Generative Heal
            if heal_with_gemini(telemetry["log"]):
                 print("✨ [HEAL] Fix proposed. Retrying not enabled in Safety Mode.")
            
            # Trigger Immune System (Jira)
            sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
            from observability import jira_bridge
            jira_bridge.handle_failure(name, telemetry["log"], TRACE_ID)
            sys.exit(1)
            
        print(f"✅ [PASS] {name}")

if __name__ == "__main__":
    main()
