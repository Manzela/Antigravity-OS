import os
import google.auth
from google.auth.transport.requests import Request
import vertexai
from vertexai.preview.generative_models import GenerativeModel
import requests

def check_auth():
    print("Locked & Loaded: Checking Credentials...")
    try:
        credentials, project = google.auth.default()
        print(f"✅ Credentials found for project: {project}")
        print(f"✅ Service Account: {getattr(credentials, 'service_account_email', 'User Credentials')}")
        
        # Refresh to check validity
        credentials.refresh(Request())
        print("✅ Credentials refreshed successfully.")
        return project
    except Exception as e:
        print(f"❌ Auth Check Failed: {e}")
        return None

def check_jira():
    print("\nTargeting Jira...")
    user = os.getenv('JIRA_USER_EMAIL')
    token = os.getenv('JIRA_API_TOKEN')
    server = "https://tngshopper.atlassian.net"
    project_key = "TNG"
    
    if not user or not token:
        print("❌ Missing Jira Env Vars (JIRA_USER_EMAIL or JIRA_API_TOKEN)")
        return

    auth = (user, token)
    url = f"{server}/rest/api/2/project/{project_key}"
    
    try:
        resp = requests.get(url, auth=auth)
        if resp.status_code == 200:
            print(f"✅ Jira Project {project_key} found!")
        else:
            print(f"❌ Jira Project Check Failed: {resp.status_code} - {resp.text[:100]}")
    except Exception as e:
        print(f"❌ Jira Connection Failed: {e}")

def check_vertex(project_id):
    print(f"\nScanning Vertex AI in {project_id}...")
    locations = ["us-central1", "us-west1", "us-east1", "europe-west1"]
    models = ["gemini-2.0-flash-001", "gemini-1.5-flash", "gemini-1.0-pro"]
    
    for loc in locations:
        print(f"  📍 Region: {loc}")
        try:
            vertexai.init(project=project_id, location=loc)
            for m_name in models:
                try:
                    model = GenerativeModel(m_name)
                    # Just instantiation doesn't hit API, generate does
                    resp = model.generate_content("Ping")
                    print(f"    ✅ {m_name} SUCCESS in {loc}")
                    return # Found one!
                except Exception as e:
                    print(f"    ❌ {m_name} failed: {e}")
        except Exception as e:
            print(f"    ⚠️ Init failed for {loc}: {e}")

if __name__ == "__main__":
    # Ensure env vars are loaded from .env if possible (simple parse)
    if os.path.exists(".env"):
        print("Loading .env...")
        with open(".env") as f:
            for line in f:
                if "=" in line and not line.startswith("#"):
                    k, v = line.strip().split("=", 1)
                    if not os.getenv(k): # Don't overwrite existing
                        os.environ[k] = v.strip('"')

    proj = check_auth()
    if proj:
        check_vertex(proj)
    check_jira()
