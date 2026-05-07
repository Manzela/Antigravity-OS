# Contributing to Antigravity OS

Thank you for your interest in contributing. This document covers the process
for submitting changes, the expectations for code quality, and how to build
a new provider.

---

## Code of Conduct

All participants are expected to follow the [Code of Conduct](CODE_OF_CONDUCT.md).

---

## Getting Started

```bash
git clone https://github.com/Manzela/Antigravity-OS.git
cd Antigravity-OS
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
ag-os init --defaults
ag-os demo
```

---

## Development Workflow

1. **Fork and branch.** Create a feature branch from `main`.
2. **Write code.** Follow existing patterns (see Style Guide below).
3. **Test.** Run `pytest` and ensure all tests pass.
4. **Lint.** Run `ruff check .` and `ruff format --check .` to verify formatting.
5. **Commit.** Use clear, descriptive commit messages.
6. **Open a PR.** Fill in the PR template. Reference related issues.

---

## Style Guide

- Python 3.10+ (type hints required on all public APIs).
- Line length: 100 characters (configured in `pyproject.toml`).
- Linter: `ruff` with rules `E`, `F`, `I`, `N`, `W`.
- Docstrings: Google style on every public class and function.
- No emojis in code, CLI output, or documentation.
- Use `[OK]`, `[INFO]`, `[BLOCKED]`, `[ERROR]` for status indicators.

---

## Writing a New Provider

Every Antigravity OS integration is a **provider** -- a class that implements
an Abstract Base Class for one of the 7 integration surfaces.

### Step 1: Choose a surface

| Surface | ABC | File Location |
|:---|:---|:---|
| Secrets | `SecretsProvider` | `ag_os/providers/secrets/` |
| Issues | `IssueProvider` | `ag_os/providers/issues/` |
| Cost | `CostProvider` | `ag_os/providers/cost/` |
| State | `StateProvider` | `ag_os/providers/state/` |
| Telemetry | `TelemetryProvider` | `ag_os/providers/telemetry/` |
| Policy | `PolicyProvider` | `ag_os/providers/policy/` |

### Step 2: Create the provider file

```python
# ag_os/providers/cost/my_cloud.py

from ag_os.providers.registry import register
from ag_os.providers.cost import CostProvider


@register("cost", "my_cloud")
class MyCloudCostProvider(CostProvider):
    def __init__(self, **kwargs):
        # Initialize client
        ...

    def get_current_spend(self) -> float:
        # Query API
        ...

    def get_tier_rate(self, tier: str) -> float:
        # Return rate
        ...
```

### Step 3: Register the import

Add your module to `ag_os/providers/registry.py` in `_discover_builtins()`,
or publish it as a separate package that users import.

### Step 4: Add tests

Create `tests/providers/cost/test_my_cloud.py` with unit tests.

### Step 5: Document

Update the README provider table and add configuration examples.

---

## Good First Issues

Look for issues labeled `good first issue` in the issue tracker.
These are specifically chosen to be approachable for new contributors.

---

## Reporting Bugs

Use the [Bug Report](https://github.com/Manzela/Antigravity-OS/issues/new?template=bug_report.yml)
template. Include:

- Antigravity OS version (`ag-os --version`)
- Python version
- Operating system
- Steps to reproduce
- Expected vs. actual behavior
- Contents of `antigravity.yaml` (redact secrets)

---

## Proposing New Features

Use the [Feature Request](https://github.com/Manzela/Antigravity-OS/issues/new?template=feature_request.yml)
template. Describe the use case before proposing a solution.

---

## Contributor Tiers

| Tier | Criteria | Recognition |
|:---|:---|:---|
| Pioneer | First PR merged | Name in CONTRIBUTORS.md |
| Builder | 3+ PRs or 1 provider shipped | README mention |
| Guardian | 10+ PRs or maintains a provider | Commit access to provider dir |
| Core | Sustained contribution, invite-based | Write access to core |
