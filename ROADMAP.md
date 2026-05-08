# Roadmap

This document outlines the planned development trajectory for Antigravity OS.
Priorities may shift based on community feedback.

---

## V1.0 -- Governance Kernel (Released)

- [x] Provider-agnostic architecture with 6 integration surfaces
- [x] Zero-dependency default stack (SQLite, Console, Local JSON)
- [x] Cost Guard solvency gate (Rule 08)
- [x] Flight Recorder deterministic state machine (Rule 05)
- [x] Built-in policy evaluator reading Markdown rules
- [x] CLI: `init`, `check`, `demo`, `status`
- [x] Configuration via `antigravity.yaml`
- [x] Unit test suite for all default providers
- [ ] GitHub Actions Marketplace integration
- [ ] CI template generators (GitHub, GitLab, Bitbucket)

## V1.1 -- Community and Ecosystem

- [x] Dreaming Module: Self-improvement loop that analyzes friction logs and auto-proposes governance patches
- [x] MCP Server: Expose Cost Guard and Flight Recorder as MCP tools
- [ ] A2A Handover Protocol: Formalized agent handover contracts
- [ ] GitHub Issues provider (REST API, auto-token in Actions)
- [ ] File-based telemetry provider (JSONL output)
- [ ] Redis state provider
- [ ] OPA policy provider

## V1.3 -- Credential Management (Released)

- [x] OS Keychain-backed credential storage via `keyring`
- [x] Provider credential registry with live validation
- [x] Environment variable override for CI/CD
- [x] Graceful fallback to local file for headless environments
- [x] FTUX credential prompts after provider selection

## V1.4 -- DreamEngine Convergence (Released)

- [x] Success Pattern Extraction: Inverse anomaly detection (CLEAN_COMPLETION, FAST_COMPLETION, FIRST_ATTEMPT_SUCCESS)
- [x] GitOps Patch Applier: Risk-based governance patch application with HITL gates
- [x] Dream Daemon: Background process for continuous self-improvement cycles
- [x] Cross-Repo Aggregator: Enterprise fleet-wide friction correlation
- [x] Tiered Memory Consolidation: TTL and count-based pruning with rollup
- [x] CNCF Governance Documentation (GOVERNANCE.md, MAINTAINERS.md, ADOPTERS.md)
- [x] Architecture Decision Records (ADR-001 through ADR-004)
- [x] Pre-commit hooks and pip-audit in CI

## V1.2 -- Enterprise Signal

- [ ] Jira issue provider
- [ ] Linear issue provider
- [ ] GCP Billing cost provider
- [ ] AWS Cost Explorer cost provider
- [ ] OTLP telemetry exporter
- [ ] Dashboard: Web UI for flight recorder history and cost trends
- [ ] `ag-os generate ci` command for multi-platform CI templates

## V2.0 -- Platform

- [ ] Antigravity Cloud: Hosted governance dashboard
- [ ] Enterprise SSO (SAML/OIDC)
- [ ] Audit log with retention policies
- [ ] Multi-tenant governance (team budgets, per-team rules)
- [ ] Cedar policy provider (AWS)
- [ ] CNCF Sandbox application

---

## How to Influence the Roadmap

- Open a [Feature Request](https://github.com/Manzela/Antigravity-OS/issues/new?template=feature_request.yml)
- Vote on existing proposals with thumbs-up reactions
- Join the discussion in GitHub Discussions or Discord
