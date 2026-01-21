#!/bin/bash
set -e
export PATH="$PATH:/Library/Frameworks/Python.framework/Versions/3.13/bin:/Users/danielmanzela/Library/Python/3.13/bin"

echo "🪐 Initializing Antigravity OS V3.3 (Deep Integration)..."

# ---------------------------------------------------------
# PHASE 1: IDENTITY & AUTHENTICATION
# ---------------------------------------------------------
echo "🔍 Verifying @tngshopper.com Identity..."
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

# ---------------------------------------------------------
# PHASE 2: SECRET HYDRATION (Critical Fix)
# ---------------------------------------------------------
echo "☁️  Hydrating Secrets from Google Secret Manager..."

# Helper: Try exact name first, then antigravity- prefix
fetch_secret() {
    local NAME=$1
    local VAL=$(gcloud secrets versions access latest --secret="$NAME" --quiet 2>/dev/null || \
                gcloud secrets versions access latest --secret="antigravity-$NAME" --quiet 2>/dev/null || echo "")
    if [ -z "$VAL" ]; then
        echo "   ⚠️  Missing Cloud Secret: $NAME" >&2
    else
        echo "   ✅ Fetched: $NAME" >&2
    fi
    echo "$VAL"
}

# 1. Fetch Infrastructure Secrets
GCP_BILLING_ID=$(fetch_secret "GCP_BILLING_ACCOUNT_ID")
REDIS_HOST=$(fetch_secret "REDIS_HOST")
REDIS_PORT=$(fetch_secret "REDIS_PORT")
REDIS_PASS=$(fetch_secret "REDIS_PASSWORD")
REDIS_USER=$(fetch_secret "REDIS_USER")
GCP_SA_KEY=$(fetch_secret "GCP_SA_KEY")
LOG_BUCKET=$(fetch_secret "ANTIGRAVITY_LOG_BUCKET")

# 2. Fetch App Secrets
JIRA_TOKEN=$(fetch_secret "JIRA_API_TOKEN")
JIRA_EMAIL=$(fetch_secret "JIRA_USER_EMAIL")

# 3. Handle Service Account Key (JSON)
if [ ! -z "$GCP_SA_KEY" ]; then
    mkdir -p .agent
    echo "$GCP_SA_KEY" > .agent/gcp_sa_key.json
    chmod 600 .agent/gcp_sa_key.json
    export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/.agent/gcp_sa_key.json"
    echo "   🔑 Service Account Key saved to .agent/gcp_sa_key.json"
else
    # Fallback to ADC if no key provided
    export GOOGLE_APPLICATION_CREDENTIALS=""
fi

# ---------------------------------------------------------
# PHASE 3: BRAIN STRATEGY (Smart Connectivity)
# ---------------------------------------------------------
echo "🧠 Configuring Brain..."

# Default to Local
USE_LOCAL_DB=true

# If Host is set and not localhost, test connectivity
if [ ! -z "$REDIS_HOST" ] && [ "$REDIS_HOST" != "localhost" ]; then
    echo "   📡 Remote Redis Configured: $REDIS_HOST"
    # Use Python to test connection (Portability Check)
    if python3 -c "import socket; socket.create_connection(('$REDIS_HOST', int('${REDIS_PORT:-6379}')), timeout=2)" 2>/dev/null; then
        echo "   ✅ Connection Successful. Using Production Brain."
        USE_LOCAL_DB=false
    else
        echo "   ⚠️  Remote Host Unreachable (VPN Issue?). Falling back to Local Brain."
    fi
fi

if [ "$USE_LOCAL_DB" = true ]; then
    REDIS_HOST="antigravity-brain"
    REDIS_PORT="6379"
    REDIS_PASS="" 
    echo "   🔹 Booting Local Brain Container..."
    command -v docker >/dev/null || { echo "❌ Docker missing"; exit 1; }
    docker-compose up -d antigravity-brain
    until docker exec antigravity-brain redis-cli ping | grep PONG; do sleep 1; done
else
    # Only boot Sentinel (OPA) locally
    command -v docker >/dev/null && docker-compose up -d antigravity-sentinel 2>/dev/null
fi

# ---------------------------------------------------------
# PHASE 4: WRITE ENVIRONMENT
# ---------------------------------------------------------
cat <<EOF > .env
GCP_PROJECT_ID="${PROJECT_ID}"
GCP_BILLING_ACCOUNT_ID="${GCP_BILLING_ID}"
JIRA_API_TOKEN="${JIRA_TOKEN}"
JIRA_USER_EMAIL="${JIRA_EMAIL}"
REDIS_HOST="${REDIS_HOST}"
REDIS_PORT="${REDIS_PORT:-6379}"
REDIS_PASSWORD="${REDIS_PASS}"
REDIS_USER="${REDIS_USER}"
ANTIGRAVITY_LOG_BUCKET="${LOG_BUCKET}"
GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/.agent/gcp_sa_key.json"
EOF

# ---------------------------------------------------------
# PHASE 5: INSTALL & WIRE
# ---------------------------------------------------------
echo "📦 Installing Dependencies..."
pip3 install -r requirements.txt >/dev/null
opentelemetry-bootstrap -a install >/dev/null

echo "🪝 Wiring Git Hooks..."
echo "#!/bin/sh
# Load the Hydrated Environment
set -a
. \"$(pwd)/.env\"
set +a
export PATH=\"\$PATH:/Library/Frameworks/Python.framework/Versions/3.13/bin:/Users/danielmanzela/Library/Python/3.13/bin\"
python3 .agent/runtime/orchestrator.py" > .git/hooks/pre-push
chmod +x .git/hooks/pre-push

echo "✅ V3.3 Installed. Deep Integration Active."
