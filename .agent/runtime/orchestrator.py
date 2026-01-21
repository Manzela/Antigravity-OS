import subprocess, sys, os, time, json, uuid
import redis
import vertexai
from vertexai.generative_models import GenerativeModel
from google.cloud import storage
from opentelemetry import trace
from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor

# Local Imports
# ADAPTED: Corrected path for .agent directory structure
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from security import scrubber

# CONFIG
PROJECT_ID = os.getenv("GCP_PROJECT_ID")
TRACE_ID = str(uuid.uuid4())
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)

def setup_telemetry():
    """Uplink to Google Cloud Trace with Fallback"""
    try:
        # If GOOGLE_APPLICATION_CREDENTIALS is empty or points to a bad file, unset it to force ADC
        cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if not cred_path:
            os.environ.pop("GOOGLE_APPLICATION_CREDENTIALS", None)
        elif os.path.exists(cred_path):
             with open(cred_path, 'r') as f:
                 try:
                     json.load(f)
                 except json.JSONDecodeError:
                     print("⚠️ [UPLINK] Corrupt SA Key detected. Switching to User Auth (ADC).")
                     os.environ.pop("GOOGLE_APPLICATION_CREDENTIALS", None)

        if PROJECT_ID:
            exporter = CloudTraceSpanExporter(project_id=PROJECT_ID)
            provider = TracerProvider()
            provider.add_span_processor(SimpleSpanProcessor(exporter))
            trace.set_tracer_provider(provider)
            print(f"📡 [UPLINK] Connected to Google Cloud Trace ({PROJECT_ID})")
        else:
            print("⚠️ [UPLINK] No Project ID. Telemetry disabled.")
    except Exception as e:
        print(f"⚠️ [UPLINK] Offline: {e}")

def consult_mind(error_log):
    """Consult Gemini Pro for a fix"""
    print(f"🧠 [MIND] Analyze Error...")
    try:
        vertexai.init(project=PROJECT_ID, location="us-central1")
        model = GenerativeModel("gemini-2.0-flash-001")
        
        prompt = f"""
        act as a Senior Python Engineer. Analyze this error trace and return a code patch to fix it.
        Be concise. Return ONLY the code block.
        
        Error Trace:
        {error_log}
        """
        
        response = model.generate_content(prompt)
        print(f"\n💡 [MIND] Proposed Fix:\n{response.text}\n")
        return response.text
    except Exception as e:
        print(f"⚠️ [MIND] Silent: {e}")



def main():
    setup_telemetry()
    # ... (Rest of logic remains consistent)
    phases = [("Build & Test", "python3 -m pytest tests/")]
    
    for name, cmd in phases:
        print(f"🔄 [ORCHESTRATOR] {name}...")
        instrumented_cmd = f"opentelemetry-instrument --service_name antigravity-agent {cmd}"
        result = subprocess.run(instrumented_cmd, shell=True, capture_output=True, text=True)
        safe_log = scrubber.scrub_payload(result.stderr + result.stdout)
        
        if result.returncode != 0:
            print(f"❌ [FAIL] {name}")
            print(f"📄 [LOGS] \n{safe_log}\n") # Added debug log
            # ADAPTED: Importing from correct module path
            from observability import jira_bridge
            jira_bridge.handle_failure(name, safe_log, TRACE_ID)
            
            # External Archive Call
            try:
                subprocess.run([
                    sys.executable, 
                    "scripts/archive_telemetry.py", 
                    TRACE_ID, 
                    safe_log
                ], check=False)
            except Exception as e:
                print(f"⚠️ [STORAGE] Script invocation failed: {e}")

            consult_mind(safe_log)
            sys.exit(1)
        else:
            print(f"✅ [PASS] {name}")

if __name__ == "__main__":
    main()
