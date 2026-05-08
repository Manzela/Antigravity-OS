# Changelog

All notable changes to Antigravity OS are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.4.0] - 2026-05-08

### Added

- **Success Pattern Extraction** (Feature 2) — Inverse anomaly detection
  identifies CLEAN_COMPLETION, FAST_COMPLETION, and FIRST_ATTEMPT_SUCCESS
  patterns from operational telemetry.
- **GitOps Patch Applier** (Feature 3) — Risk-based governance patch
  application with comment-preserving YAML round-trips (ruamel.yaml).
  LOW-risk patches auto-apply; HIGH-risk patches require human approval.
  Full audit trail to `~/.antigravity/patch_audit.yaml`.
- **Dream Daemon** (Feature 1) — Background process for continuous
  self-improvement cycles. OS-native service installation for launchd
  (macOS) and systemd (Linux). PID/health file management with
  structured logging.
- **Cross-Repo Aggregator** (Feature 4) — Enterprise fleet-wide friction
  correlation via `ag-os dream merge`. Detects systemic patterns across
  multiple repositories.
- **Tiered Memory Consolidation** (Feature 5) — TTL and count-based
  pruning with statistical rollup to `historical_aggregates.jsonl`.
- **CNCF Governance Documentation** — GOVERNANCE.md, MAINTAINERS.md,
  ADOPTERS.md.
- **Architecture Decision Records** — ADR-001 through ADR-004 in
  `docs/adr/`.
- **Pre-commit hooks** — ruff, detect-secrets, and standard hygiene
  hooks.
- **pip-audit in CI** — Supply-chain vulnerability scanning on every
  build.
- **Credential tests** — Test coverage for the keyring/fallback
  credential lifecycle.

### Changed

- **CI matrix** — Added Python 3.14 to match pyproject.toml classifiers.
- **Default config** — Reset to offline-first providers (console, local,
  sqlite) for open-source release. Added `dreaming` section to config
  schema.
- **Dream CLI** — Upgraded from `@main.command()` to `@main.group()` to
  support subcommands (`merge`) and new flags (`--apply`, `--prune`).

### Dependencies

- Added `ruamel.yaml>=0.18` for comment-preserving YAML round-trips.

## [1.3.0] - 2026-05-08

### Added

- **Secure Credential Manager** — OS Keychain-backed secret storage via `keyring`.
  - macOS Keychain / Linux Secret Service / Windows Credential Locker.
  - Same pattern as GitHub CLI (`gh auth`).
  - Provider credential registry with validation (GitHub, Linear, Jira, Redis, OTLP).
  - Environment variable override for CI/CD (highest priority).
  - Graceful fallback to `~/.config/ag-os/credentials.json` for headless environments.
- **FTUX Phase 2** — Provider authentication prompts after provider selection.
  - Masked input for sensitive tokens.
  - Live validation (GitHub `/user`, Linear GraphQL, Jira `/myself`, Redis PING).
  - Skips already-configured credentials.
- **`/auth` command** — Post-setup credential management (view, add, revoke).
- **`.gitignore` protection** — Auto-adds `.env`, `.env.*`, `credentials.json` during setup.

### Fixed

- **`/dream` command crash** — Fixed 5 wrong attribute names on `DreamReport` and `GovernancePatch` dataclasses.
- **Provider fallback** — `FlightRecorder` and `DreamEngine` gracefully fall back to `sqlite`/`console` when configured provider isn't installed.
- **Pre-push git hook** — Now searches `.venv/bin/ag-os` before PATH; skips gracefully if not found.
- **Test isolation** — Fixtures no longer polluted by local `antigravity.yaml` configuration.

---

## [1.2.0] - 2026-05-07

### Added

- **Dreaming Module** — Self-improvement loop for AI agents.
  - `ag-os dream` CLI command with `--recall`, `--json-output`, `--dry-run` flags.
  - `ag-os demo --dream` flag for simulated failure → self-improvement demo.
  - `dream` and `recall_dreams` MCP tools for AI agent integration.
  - Friction scanning: 5 detection archetypes (loop, rollback, budget, blocked, excessive).
  - Dream Reports: structured YAML with root-cause diagnosis and governance patches.
  - Long-term memory: persistent storage in `~/.antigravity/dreams/`.
  - 20 new unit tests covering scan, synthesis, persistence, recall, MCP tools.

---

## [1.1.0] - 2026-05-07

### Added

- MCP Server (`ag-os serve`) exposing 5 governance tools for AI agent integration.
  - `check_solvency` -- Budget cap verification.
  - `transition_state` -- Flight Recorder state machine control.
  - `evaluate_policy` -- Governance rule evaluation.
  - `get_status` -- Configuration and provider overview.
  - `get_history` -- Audit trail retrieval.
- Optional dependency group: `pip install ag-os[mcp]`.
- PyPI Trusted Publisher workflow (`.github/workflows/publish.yml`).
- CI status badge in README.
- PEP 639 compliant license declaration.

---

## [1.0.0] - 2026-05-07

### Added

- Provider-agnostic architecture with 6 integration surfaces.
- Provider Registry with `@register` decorator and `get_provider()` factory.
- Default providers (zero-dependency, zero-cloud):
  - Secrets: `.env` file reader (`local`) and `os.environ` reader (`env`).
  - Issues: Console output + JSONL + friction log (`console`).
  - Cost: Local JSON files for pricing and spend (`local`).
  - State: SQLite database at `~/.antigravity/state.db` (`sqlite`).
  - Telemetry: Human-readable stdout traces and metrics (`console`).
  - Policy: Markdown rule evaluator reading `.agent/rules/*.md` (`builtin`).
- Core governance modules:
  - Cost Guard: Economic solvency gate (Rule 08).
  - Flight Recorder: Deterministic state machine with 8 states (Rule 05).
  - Rules Engine: Policy evaluation orchestrator.
- CLI (`ag-os`):
  - `ag-os init` -- Interactive project setup with validated prompts.
  - `ag-os check` -- Solvency verification with exit code 1 on failure.
  - `ag-os demo` -- 60-second governance demonstration.
  - `ag-os status` -- Provider configuration overview.
- Configuration system:
  - `antigravity.yaml` with walk-up directory discovery.
  - Deep merge semantics for nested config.
  - Environment variable overrides (`AG_OS_MONTHLY_CAP`, `AG_OS_MAX_LOOPS`).
- The Constitution: 9 governance rules (00-08) installed by `ag-os init`.
- Flight Recorder JSON Schema.
- Pre-push git hook installed by `ag-os init`.

### Technical Details

- Python 3.10+ required.
- Core dependencies: `pyyaml>=6.0`, `click>=8.0`.
- Optional extras: `gcp`, `aws`, `vault`, `jira`, `linear`, `redis`, `datadog`.
- PEP 639 license expression for Python 3.14+ compatibility.
