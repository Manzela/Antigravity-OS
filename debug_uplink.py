import os, sys, traceback
from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry import trace

PROJECT_ID = os.getenv("GCP_PROJECT_ID", "i-for-ai")

def debug_uplink():
    print(f"DEBUG: PROJECT_ID={PROJECT_ID}")
    print(f"DEBUG: GOOGLE_APPLICATION_CREDENTIALS={os.getenv('GOOGLE_APPLICATION_CREDENTIALS')}")
    try:
        if PROJECT_ID:
            exporter = CloudTraceSpanExporter(project_id=PROJECT_ID)
            provider = TracerProvider()
            provider.add_span_processor(BatchSpanProcessor(exporter))
            trace.set_tracer_provider(provider)
            print("✅ Uplink Successful")
        else:
            print("❌ No Project ID")
    except Exception:
        traceback.print_exc()

if __name__ == "__main__":
    debug_uplink()
