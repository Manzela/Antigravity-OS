#!/bin/bash
# Antigravity QA Orchestrator (Phase 7)
# Runs Static Analysis (ShellCheck) and Unit Tests (Pytest/Unittest)

set -e

echo "========================================"
echo "   ANTIGRAVITY QA SUITE (V2.5.1)        "
echo "========================================"

# 1. Static Analysis (Dockerized ShellCheck)
echo "[QA-1] Running ShellCheck (via Docker)..."
if command -v docker >/dev/null 2>&1; then
    # Linting build_product.sh and install.sh
    # Excluding SC2016 (Expressions in single quotes) if necessary, but broadly standard
    docker run --rm -v "$(pwd):/mnt" koalaman/shellcheck:stable         build_product.sh install.sh templates/scripts/*.sh         || echo "[WARN] ShellCheck found issues. Review output above."
else
    echo "[SKIP] Docker not found. Skipping ShellCheck."
fi

# 2. Unit Testing (Jira Bridge Logic)
echo "[QA-2] Running Unit Tests (Python)..."
export PYTHONPATH=$PYTHONPATH:$(pwd)
if python3 -c "import pytest" >/dev/null 2>&1; then
    python3 -m pytest templates/tests/test_jira_bridge.py -v
else
    echo "[INFO] Pytest not installed. Falling back to Unittest."
    python3 templates/tests/test_jira_bridge.py
fi

echo "========================================"
echo "[SUCCESS] QA Suite Completed."
echo "========================================"
