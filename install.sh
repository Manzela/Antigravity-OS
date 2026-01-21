#!/bin/bash
set -e
export PATH="$PATH:$(python3 -m site --user-base)/bin:$(python3 -c 'import sysconfig; print(sysconfig.get_path("scripts"))')"
echo "🪐 Initializing Antigravity OS V3.4.5 (Stability Patch)..."

# 1. IDENTITY & AUTHENTICATION
echo "🔍 Verifying @tngshopper.com Identity..."
gcloud auth print-access-token >/dev/null 2>&1 || gcloud auth login
ACCOUNT=$(gcloud config get-value account 2>/dev/null)
PROJECT_ID=$(gcloud config get-value project)
echo "✅ Authenticated as: $ACCOUNT ($PROJECT_ID)"

# 2. SECRET HYDRATION
echo "☁️  Hydrating Secrets..."
fetch_secret() {
    local NAME=$1
    local VAL=$(gcloud secrets versions access latest --secret="$NAME" --quiet 2>/dev/null || \
                gcloud secrets versions access latest --secret="antigravity-$NAME" --quiet 2>/dev/null || echo "")
    echo "$VAL"
}

GCP_BILLING_ID=$(fetch_secret "GCP_BILLING_ACCOUNT_ID")
REDIS_HOST=$(fetch_secret "REDIS_HOST")
REDIS_PORT=$(fetch_secret "REDIS_PORT")
REDIS_PASS=$(fetch_secret "REDIS_PASSWORD")
GCP_SA_KEY=$(fetch_secret "GCP_SA_KEY")
JIRA_TOKEN=$(fetch_secret "JIRA_API_TOKEN")
JIRA_EMAIL=$(fetch_secret "JIRA_USER_EMAIL")

# 3. CRITICAL FIX: SA KEY VALIDATION
# Prevents JSONDecodeError by checking if key contains 'private_key'
SA_KEY_PATH=""
if [ ! -z "$GCP_SA_KEY" ] && [[ "$GCP_SA_KEY" == *"private_key"* ]]; then
    mkdir -p .agent
    echo "$GCP_SA_KEY" > .agent/gcp_sa_key.json
    chmod 600 .agent/gcp_sa_key.json
    export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/.agent/gcp_sa_key.json"
    SA_KEY_PATH="$(pwd)/.agent/gcp_sa_key.json"
    echo "   🔑 Service Account Key verified & saved."
else
    echo "   ⚠️  GCP_SA_KEY secret is invalid or empty. Falling back to User Auth (ADC)."
    export GOOGLE_APPLICATION_CREDENTIALS=""
    rm -f .agent/gcp_sa_key.json
    SA_KEY_PATH=""
fi

# 4. BRAIN STRATEGY
USE_LOCAL_DB=true
if [ ! -z "$REDIS_HOST" ] && [ "$REDIS_HOST" != "localhost" ]; then
    # Test Connectivity
    if python3 -c "import socket; socket.create_connection(('$REDIS_HOST', int('${REDIS_PORT:-6379}')), timeout=2)" 2>/dev/null; then
        echo "   ✅ Connected to Remote Brain ($REDIS_HOST)."
        USE_LOCAL_DB=false
    else
        echo "   ⚠️  Remote Brain Unreachable (Off VPN?). Fallback to Local."
    fi
fi

if [ "$USE_LOCAL_DB" = true ]; then
    REDIS_HOST="localhost"
    REDIS_PORT="6379"
    REDIS_PASS="" 
    echo "   🔹 Booting Local Brain (Redis 7.2)..."
    docker-compose down 2>/dev/null # Stop old container
    docker-compose up -d antigravity-brain
    until docker exec antigravity-brain redis-cli ping | grep PONG >/dev/null 2>&1; do sleep 1; done
else
    # Ensure Sentinel is running
    docker-compose up -d antigravity-sentinel 2>/dev/null
fi

# 5. WRITE ENV (With TNG Project Key)
cat <<EOF > .env
GCP_PROJECT_ID="${PROJECT_ID}"
JIRA_API_TOKEN="${JIRA_TOKEN}"
JIRA_USER_EMAIL="${JIRA_EMAIL}"
REDIS_HOST="${REDIS_HOST}"
REDIS_PORT="${REDIS_PORT:-6379}"
REDIS_PASSWORD="${REDIS_PASS}"
GOOGLE_APPLICATION_CREDENTIALS="${SA_KEY_PATH}"
JIRA_PROJECT_KEY="TNG"
EOF

# 6. INSTALL & WIRE
pip3 install -r requirements.txt >/dev/null
opentelemetry-bootstrap -a install >/dev/null

echo "#!/bin/sh
set -a
. \"$(pwd)/.env\"
set +a
python3 .agent/runtime/orchestrator.py" > .git/hooks/pre-push
chmod +x .git/hooks/pre-push

echo "✅ V3.4.5 Installed. Tracing & Targeting Fixed."
