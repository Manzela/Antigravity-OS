import os
import vertexai
from vertexai.preview.generative_models import GenerativeModel

PROJECT_ID = os.getenv("GCP_PROJECT_ID", "i-for-ai")
LOCATION = "us-central1"

print(f"Checking models for {PROJECT_ID} in {LOCATION}...")

try:
    vertexai.init(project=PROJECT_ID, location=LOCATION)
    # There isn't a direct "list_models" in GenerativeModel, but we can try to instantiate a few common ones
    # or use the Model Garden API if available.
    # A simpler way is to just try a simple generation with a few candidates.
    
    candidates = ["gemini-2.0-flash-001", "gemini-1.5-flash", "gemini-1.5-pro", "gemini-1.0-pro", "gemini-pro"]
    
    for model_name in candidates:
        print(f"Testing {model_name}...")
        try:
            model = GenerativeModel(model_name)
            response = model.generate_content("Hello")
            print(f"✅ {model_name} is AVAILABLE. Response: {response.text}")
            import sys; sys.exit(0) # Found one!
        except Exception as e:
            print(f"❌ {model_name} failed: {e}")

except Exception as e:
    print(f"Fatal error initializing Vertex AI: {e}")
