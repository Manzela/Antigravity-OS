# Changelog

All notable changes to Antigravity OS are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
