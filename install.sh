#!/bin/bash
set -e
echo "🪐 Initializing Antigravity OS V3.2 (The Connected Mind)..."

# 1. IDENTITY CHECK (The Ultimate Objective)
echo "🔍 Verifying @tngshopper.com Identity..."
# Ensure gcloud is installed
command -v gcloud >/dev/null || { echo "❌ gcloud missing. Install Google Cloud SDK."; exit 1; }

# Force Login if not authenticated
gcloud auth print-access-token >/dev/null 2>&1 || gcloud auth login

# Verify Organization
ACCOUNT=$(gcloud config get-value account 2>/dev/null)
if [[ "$ACCOUNT" != *"@tngshopper.com"* ]]; then
    echo "❌ [AUTH FAIL] You must use a @tngshopper.com account. Current: $ACCOUNT"
    exit 1
fi
PROJECT_ID=$(gcloud config get-value project)
echo "✅ Authenticated as: $ACCOUNT ($PROJECT_ID)"

# 2. KEYSTONE: Cloud Hydration
echo "☁️  Fetching Secrets from Google Secret Manager..."
# Fetches the token. Fails gracefully if secret doesn't exist (mocking for new projects)
JIRA_TOKEN=$(gcloud secrets versions access latest --secret="antigravity-jira-token" --quiet 2>/dev/null || echo "MOCK_TOKEN_FOR_DEV")

cat <<EOF > .env
JIRA_TOKEN=${JIRA_TOKEN}
GCP_PROJECT=${PROJECT_ID}
REDIS_HOST=antigravity-brain
EOF

# 3. BOOT BRAIN (Infrastructure)
echo "🧠 Starting Local State Machine..."
command -v docker >/dev/null || { echo "❌ Docker missing"; exit 1; }
docker-compose up -d
until docker exec antigravity-brain redis-cli ping | grep PONG; do sleep 1; done

# 4. INSTALL NERVOUS SYSTEM (Dependencies)
echo "📦 Installing Dependencies..."
pip3 install -r requirements.txt
export PATH="$PATH:/Library/Frameworks/Python.framework/Versions/3.13/bin:/Users/danielmanzela/Library/Python/3.13/bin"
opentelemetry-bootstrap -a install

# 5. WIRE HOOKS
echo "#!/bin/sh
export REDIS_HOST=localhost
export GCP_PROJECT=${PROJECT_ID}
python3 .agent/runtime/orchestrator.py" > .git/hooks/pre-push
chmod +x .git/hooks/pre-push

echo "✅ V3.2 Installed. System is Autonomous & Connected."
