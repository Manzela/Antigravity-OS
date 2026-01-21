#!/bin/bash
set -e

echo "[INSTALL] Initializing Antigravity OS V3.1..."

# 1. Dependency Checks including ADC
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found! Install Docker Desktop."
    exit 1
fi
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI not found! Install Google Cloud SDK."
    exit 1
fi

ADC_FILE="$HOME/.config/gcloud/application_default_credentials.json"
if [ ! -f "$ADC_FILE" ]; then
    echo "❌ GCP Application Default Credentials not found!"
    echo "📣 Please run: 'gcloud auth application-default login'"
    echo "   (Required for OTel Trace Export)"
    exit 1
fi
echo "✅ Dependencies & Auth Verified."

# 2. Keystone: Hydrate Secrets (Secure Fetch)
echo "[SEC] Fetching secrets from Google Secret Manager..."
PROJECT_ID="i-for-ai"

# Try to fetch secrets (suppress errors if not logged in or secret missing)
JIRA_TOKEN=$(gcloud secrets versions access latest --secret="antigravity-jira-token" --project="$PROJECT_ID" --quiet 2>/dev/null || echo "")
GEMINI_KEY=$(gcloud secrets versions access latest --secret="antigravity-gemini-key" --project="$PROJECT_ID" --quiet 2>/dev/null || echo "")

if [ -z "$JIRA_TOKEN" ]; then
    echo "[WARN] Jira Token not found in Secret Manager."
fi
if [ -z "$GEMINI_KEY" ]; then
    echo "[WARN] Gemini API Key not found in Secret Manager."
    # Non-blocking fallback for automation safe-fail
    GEMINI_KEY=""
fi

echo "[SEC] generating local secrets configuration..."
cat <<EOF > .env
JIRA_TOKEN=$JIRA_TOKEN
GEMINI_API_KEY=$GEMINI_KEY
REDIS_HOST=antigravity-brain
EOF

# 3. Boot Brain
echo "[INFRA] Starting Containers..."
docker-compose up -d --remove-orphans
until docker exec antigravity-brain redis-cli ping | grep PONG; do 
    echo "[WAIT] Waiting for Brain..."
    sleep 2
done

# 4. Install Nervous System
echo "[DEPS] Installing Dependencies..."

# Ensure pip3 is available
if ! command -v pip3 &> /dev/null; then
    echo "[WARN] pip3 not found, trying pip..."
    PIP_CMD=pip
else
    PIP_CMD=pip3
fi

# Robustness Check
if [ -f requirements.txt ]; then
    $PIP_CMD install -r requirements.txt
else
    # Fallback to prevent crash if file missing
    $PIP_CMD install redis requests jira opentelemetry-distro opentelemetry-exporter-otlp opentelemetry-instrumentation pytest
fi

# Ensure python scripts are in path (Robust detection via sysconfig)
SCRIPTS_DIR=$(python3 -c 'import sysconfig; print(sysconfig.get_path("scripts"))')
if [ -d "$SCRIPTS_DIR" ]; then
    export PATH="$PATH:$SCRIPTS_DIR"
    echo "[PATH] Added $SCRIPTS_DIR to PATH"
fi

# Also check user base bin just in case
USER_BIN="$(python3 -m site --user-base)/bin"
if [ -d "$USER_BIN" ]; then
    export PATH="$PATH:$USER_BIN"
    echo "[PATH] Added $USER_BIN to PATH"
fi

opentelemetry-bootstrap -a install

# 5. Git Hook Wiring
# 5. Git Hook Wiring
echo "#!/bin/sh
export PATH=\"\$PATH:$SCRIPTS_DIR:$USER_BIN\"
export REDIS_HOST=localhost
export GEMINI_API_KEY=\"$GEMINI_KEY\"
export JIRA_TOKEN=\"$JIRA_TOKEN\"
python3 .agent/runtime/orchestrator.py" > .git/hooks/pre-push
chmod +x .git/hooks/pre-push

echo "[SUCCESS] V3.1 Installed. The Mind is Active."
