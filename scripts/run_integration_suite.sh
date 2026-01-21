#!/bin/bash
# Antigravity Master Integration Suite
# Orchestrates QA and E2E verification

set -e

echo "🚀 Starting Master Integration Suite..."

# 1. QA Suite
bash scripts/run_qa.sh

# 2. E2E Suite
bash scripts/run_e2e.sh

echo "✅ Master Integration Suite Completed."
