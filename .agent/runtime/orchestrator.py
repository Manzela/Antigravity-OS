import subprocess, sys, os, time, json, uuid
import redis
# Cloud Imports
import vertexai
from vertexai.generative_models import GenerativeModel
from opentelemetry import trace
from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# Local Imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from agent.security import scrubber

# CONFIG
PROJECT_ID = os.getenv("GCP_PROJECT_ID")
TRACE_ID = str(uuid.uuid4())
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)
JIRA_USER = os.getenv("JIRA_USER_EMAIL")

def setup_telemetry():
    """Uplink to Google Cloud Trace"""
    try:
        if PROJECT_ID:
            exporter = CloudTraceSpanExporter(project_id=PROJECT_ID)
            provider = TracerProvider()
            provider.add_span_processor(BatchSpanProcessor(exporter))
            trace.set_tracer_provider(provider)
            print(f"📡 [UPLINK] Connected to Google Cloud Trace ({PROJECT_ID})")
        else:
            print("⚠️ [UPLINK] No Project ID. Telemetry disabled.")
    except Exception as e:
        print(f"⚠️ [UPLINK] Cloud Error: {e}")

def get_brain_connection():
    """Connect to Redis with Auth"""
    try:
        r = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            password=REDIS_PASSWORD, # AUTH SUPPORT
            socket_connect_timeout=2
        )
        r.ping()
        return r
    except Exception as e:
        print(f"⚠️ [BRAIN] Connection Failed to {REDIS_HOST}: {e}")
        return None

def heal_with_gemini(error_log):
    """Generative Healing via Vertex AI"""
    print(f"🧬 [GEMINI] Analyzing failure for User: {JIRA_USER}...")
    try:
        if not PROJECT_ID: return False
        # Uses GOOGLE_APPLICATION_CREDENTIALS from .env automatically
        vertexai.init(project=PROJECT_ID, location="us-central1")
        model = GenerativeModel("gemini-1.5-pro")
        prompt = f"Fix this Python error:\n{error_log}\nReturn ONLY code."
        response = model.generate_content(prompt)
        print(f"💡 [GEMINI SUGGESTION]:\n{response.text[:300]}...")
        return True
    except Exception:
        print("⚠️ [GEMINI] AI Offline.")
        return False

def run_phase(name, cmd):
    print(f"🔄 [ORCHESTRATOR] {name}...")
    instrumented_cmd = f"opentelemetry-instrument --service_name antigravity-agent {cmd}"
    result = subprocess.run(instrumented_cmd, shell=True, capture_output=True, text=True)
    safe_log = scrubber.scrub_payload(result.stderr + result.stdout)
    return {"success": result.returncode == 0, "log": safe_log}

def main():
    setup_telemetry()
    brain = get_brain_connection()
    if brain:
        print(f"🧠 [BRAIN] Connected to {REDIS_HOST}")
    
    phases = [("Build & Test", "python3 -m pytest tests/")]
    
    for name, cmd in phases:
        telemetry = run_phase(name, cmd)
        if not telemetry["success"]:
            print(f"❌ [FAIL] {name}")
            heal_with_gemini(telemetry["log"])
            sys.exit(1)
        print(f"✅ [PASS] {name}")

if __name__ == "__main__":
    main()
