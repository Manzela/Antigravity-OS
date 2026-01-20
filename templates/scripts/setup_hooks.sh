#!/bin/bash
# Antigravity Hooks Installer
# Enforces Rule 02 (Fail Closed) at the Git Layer

HOOK_DIR=".git/hooks"
PRE_PUSH="$HOOK_DIR/pre-push"

if [ ! -d ".git" ]; then
    echo "[ERROR] Not a git repository. Run 'git init' first."
    exit 1
fi

echo "[INFO] Installing Antigravity Guardrails (Pre-Push)..."

cat <<EOT > $PRE_PUSH
#!/bin/bash
# Antigravity Pre-Push Hook
# Runs QA Suite before allowing push.

echo "[HOOK] Running Antigravity QA Suite..."
./scripts/run_qa.sh

STATUS=\$?
if [ \$STATUS -ne 0 ]; then
    echo "[BLOCK] Push Rejected. QA Suite Failed."
    echo "Run 'git push --no-verify' to override (Emergency Only)."
    exit 1
fi
echo "[PASS] QA Passed. Pushing..."
exit 0
EOT

chmod +x $PRE_PUSH
echo "[SUCCESS] Guardrails Active. QA Suite will run on every push."
