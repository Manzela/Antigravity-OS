<p align="center">
  <h1 align="center">Antigravity OS</h1>
  <p align="center">The governance kernel for AI agents.</p>
</p>

<p align="center">
  <a href="https://github.com/Manzela/Antigravity-OS/actions/workflows/ci.yml"><img src="https://github.com/Manzela/Antigravity-OS/actions/workflows/ci.yml/badge.svg" alt="CI" /></a>
  <a href="https://github.com/Manzela/Antigravity-OS/blob/main/LICENSE"><img src="https://img.shields.io/github/license/Manzela/Antigravity-OS" alt="License" /></a>
  <a href="https://pypi.org/project/ag-os/"><img src="https://img.shields.io/pypi/v/ag-os" alt="PyPI" /></a>
  <a href="https://pypi.org/project/ag-os/"><img src="https://img.shields.io/pypi/pyversions/ag-os" alt="Python" /></a>
</p>

<p align="center">
  <a href="https://manzela.github.io/Antigravity-OS/"><strong>🔬 Pipeline Observatory (Interactive Demo)</strong></a>
</p>

---

## The Problem

AI agents can write code. But who stops them from:

- Burning $10,000 on GPU instances overnight?
- Deploying broken code to production without a plan?
- Looping forever on a failed task?

## The Solution

```bash
pip install ag-os && ag-os init && ag-os demo
```

Antigravity OS is an **integrated, opinionated governance kernel** that combines:

- **Cost Enforcement** -- Block execution when projected spend exceeds budget.
- **Policy-as-Code** -- 9 governance rules ("The Constitution") enforced at every state transition.
- **Deterministic State Tracking** -- Flight Recorder state machine with full audit trail.
- **Self-Healing CI** -- Pre-push hooks and CI gates that prevent broken deployments.
- **Dreaming Module** -- Self-improvement loop that analyzes friction and proposes governance patches.

All provider-agnostic. All in one install. No cloud accounts required.

---

## Quick Start

```bash
# Install
pip install ag-os

# Initialize (creates antigravity.yaml, Constitution rules, git hooks)
ag-os init --defaults

# See it in action (60-second governance demo)
ag-os demo

# Check solvency before allocating resources
ag-os check 1.0 --tier standard_cpu

# View configured providers
ag-os status
```

---

## How It Works

Antigravity OS operates through **6 provider surfaces**, each with a
swappable backend:

| Surface | Default | What It Does |
|:---|:---|:---|
| **Secrets** | OS Keychain | Securely store and retrieve credentials |
| **Issues** | Console + JSONL | Create and deduplicate governance issues |
| **Cost** | Local JSON | Track spend, enforce budget caps |
| **State** | SQLite | Persist flight recorder state and leases |
| **Telemetry** | Console | Emit traces and metrics |
| **Policy** | Built-in | Evaluate governance rules (The Constitution) |

### Zero-Dependency Defaults

The default stack requires **nothing but Python**. No Docker, no cloud
accounts, no API tokens. Value in 60 seconds.

### Upgrade When Ready

```bash
pip install ag-os[mcp]     # MCP Server for AI agent integration
pip install ag-os[gcp]     # GCP Secret Manager, Billing API, Cloud Trace
pip install ag-os[aws]     # AWS Secrets Manager, Cost Explorer
pip install ag-os[jira]    # Jira issue tracking
pip install ag-os[redis]   # Redis state store
```

---

## MCP Server

Antigravity OS includes a built-in [MCP](https://modelcontextprotocol.io) server
that exposes governance tools to any MCP-compatible AI agent:

```bash
pip install ag-os[mcp]
ag-os serve
```

### Available Tools

| Tool | What It Does |
|:---|:---|
| `check_solvency` | Run the Cost Guard against the budget cap |
| `transition_state` | Advance the Flight Recorder state machine |
| `evaluate_policy` | Execute governance rules against operation context |
| `get_status` | Return current configuration and providers |
| `get_history` | Retrieve the Flight Recorder audit trail |
| `dream` | Run the Dreaming Module self-improvement cycle |
| `recall_dreams` | Retrieve past Dream Reports from long-term memory |

### Client Configuration

Add to your MCP client configuration (e.g. Claude Desktop, Cursor):

```json
{
  "mcpServers": {
    "antigravity-os": {
      "command": "ag-os",
      "args": ["serve"]
    }
  }
}
```

---

## Dreaming Module

The Dreaming Module gives any LLM agent a **sleep cycle** — a model-agnostic,
zero-dependency self-improvement loop that analyzes past execution friction and
proposes governance improvements. No fine-tuning. No RAG. No vector database.

```bash
# Run the dream cycle (analyzes friction, proposes improvements)
ag-os dream

# Recall past learnings (long-term memory)
ag-os dream --recall 5

# Output as JSON for programmatic consumption
ag-os dream --json-output

# See it in action (simulates failure → dream → self-improvement)
ag-os demo --dream
```

### How It Works

1. **Friction Scan** — Queries the Flight Recorder for operations that looped,
   rolled back, exceeded budgets, or got stuck.
2. **Pattern Detection** — Classifies friction into 5 archetypes: loop detection,
   rollback cycles, budget overruns, blocked terminals, excessive transitions.
3. **Dream Report** — Synthesizes a structured report with root-cause diagnoses
   and proposed governance patches (new rules, config changes, threshold adjustments).
4. **Long-Term Memory** — Persists Dream Reports to `~/.antigravity/dreams/` as
   YAML files that accumulate across sessions.

Any AI agent that reads `ag-os dream` output gains self-improvement capabilities.

---

## The Constitution

Antigravity OS enforces 9 governance rules, installed as Markdown files
in `.agent/rules/`:

| Rule | Name | What It Enforces |
|:---|:---|:---|
| 00 | Plan First | No code changes without an approved plan |
| 01 | Data Contracts | All data exchange uses explicit, validated contracts |
| 02 | Fail Closed | Unknown states halt execution and escalate |
| 03 | Zero Trust Dependencies | All external inputs/outputs are validated |
| 04 | Governance Gate | All state transitions pass through the gate |
| 05 | Flight Recorder | Every operation is tracked through the state machine |
| 06 | Agent Handover | Structured handover contracts for agent transfers |
| 07 | Loop Detection | Max retry loops enforced with human escalation |
| 08 | Economic Safety | The Solvency Gate -- block if over budget |

---

## Configuration

All settings live in `antigravity.yaml`:

```yaml
version: "1.0"

monthly_cap: 50.00
max_loop_count: 5

providers:
  secrets: local         # local | env | gcp | aws | vault
  issues: console        # console | github | linear | jira
  cost: local            # local | gcp | aws | azure | litellm
  state: sqlite          # sqlite | redis | file
  telemetry: console     # console | file | otlp | gcp | datadog
  policy: builtin        # builtin | opa | cedar

ci:
  platform: local        # local | github | gitlab | bitbucket
  self_healing: true
```

Environment variable overrides (highest precedence):

```bash
export AG_OS_MONTHLY_CAP=100.00
export AG_OS_MAX_LOOPS=10
```

---

## Writing a Custom Provider

Every provider is a Python class with a `@register` decorator:

```python
from ag_os.providers.registry import register
from ag_os.providers.cost import CostProvider

@register("cost", "my_cloud")
class MyCloudCostProvider(CostProvider):
    def get_current_spend(self) -> float:
        return self._client.get_month_to_date()

    def get_tier_rate(self, tier: str) -> float:
        return self._rates[tier]
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full provider development guide.

---

## Project Structure

```
ag-os/
├── ag_os/
│   ├── cli.py                  # ag-os CLI (init, check, demo, status)
│   ├── config.py               # antigravity.yaml loader
│   ├── interactive.py           # Interactive shell (FTUX, /commands)
│   ├── core/
│   │   ├── cost_guard.py       # Solvency logic (Rule 08)
│   │   ├── credentials.py      # OS Keychain credential manager
│   │   ├── dreaming.py         # Dreaming Module (self-improvement)
│   │   ├── flight_recorder.py  # State machine (Rule 05)
│   │   └── rules_engine.py     # Policy evaluator
│   └── providers/
│       ├── registry.py         # @register + get_provider()
│       ├── secrets/            # SecretsProvider ABC + local, env
│       ├── issues/             # IssueProvider ABC + console
│       ├── cost/               # CostProvider ABC + local
│       ├── state/              # StateProvider ABC + sqlite
│       ├── telemetry/          # TelemetryProvider ABC + console
│       └── policy/             # PolicyProvider ABC + builtin
├── antigravity.yaml
├── pyproject.toml
├── LICENSE
├── CONTRIBUTING.md
├── SECURITY.md
├── CHANGELOG.md
└── ROADMAP.md
```

---

## Contributing

Contributions are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

Key areas where help is needed:

- New providers (AWS, GCP, Linear, Datadog, OPA)
- CI template generators (GitLab, Bitbucket)
- Documentation and tutorials
- Unit tests

---

## License

[MIT](LICENSE) -- Daniel Manzela, 2026.

---

## Links

- [Changelog](CHANGELOG.md)
- [Roadmap](ROADMAP.md)
- [Security Policy](SECURITY.md)
- [Code of Conduct](CODE_OF_CONDUCT.md)
