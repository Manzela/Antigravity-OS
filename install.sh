#!/bin/bash
set -e

echo "[INSTALL] Initializing Antigravity OS V3.1..."

# 1. Dependency Check
command -v docker >/dev/null || { echo "[ERROR] Docker missing"; exit 1; }

# 2. Keystone: Hydrate Secrets (Fixes R-Sec-02)
echo "[SEC] Generating local secrets configuration..."
cat <<EOF > .env
JIRA_TOKEN=${JIRA_TOKEN:-""}
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
echo "#!/bin/sh
export PATH=\"\$PATH:$SCRIPTS_DIR:$USER_BIN\"
export REDIS_HOST=localhost
python3 .agent/runtime/orchestrator.py" > .git/hooks/pre-push
chmod +x .git/hooks/pre-push

echo "[SUCCESS] V3.1 Installed. The Mind is Active."
