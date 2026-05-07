# Roadmap

This document outlines the planned development trajectory for Antigravity OS.
Priorities may shift based on community feedback.

---

## V1.0 -- Governance Kernel (Current)

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
