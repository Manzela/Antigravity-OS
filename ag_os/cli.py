"""
Antigravity OS CLI — The `ag-os` command.

Subcommands:
    ag-os init     Initialize a new project with antigravity.yaml
    ag-os check    Run a solvency check against the budget cap
    ag-os demo     Run the 60-second governance demo
    ag-os status   Show current provider configuration
"""

import json
import sys
from pathlib import Path

import click
import yaml

from ag_os import __version__
from ag_os.config import _DEFAULT_CONFIG, load_config

# ──────────────────────────────────────────────────────────────
# CLI Group
# ──────────────────────────────────────────────────────────────


@click.group()
@click.version_option(__version__, prog_name="ag-os")
def main():
    """Antigravity OS -- The governance kernel for AI agents."""
    pass


# ──────────────────────────────────────────────────────────────
# ag-os init
# ──────────────────────────────────────────────────────────────


@main.command()
@click.option("--defaults", is_flag=True, help="Skip prompts, use all defaults.")
@click.option("--ci", type=click.Choice(["local", "github", "gitlab", "bitbucket"]), default=None)
def init(defaults, ci):
    """Initialize a new Antigravity OS project."""
    print()
    print("  Antigravity OS -- Interactive Setup")
    print()

    config = dict(_DEFAULT_CONFIG)

    if not defaults:
        # Interactive prompts with validated choices
        cap = click.prompt(
            "  Monthly budget cap (USD)",
            default=str(config["monthly_cap"]),
            type=float,
        )
        config["monthly_cap"] = cap

        issues = click.prompt(
            "  Issue tracker",
            default=config["providers"]["issues"],
            type=click.Choice(["console", "github", "linear", "jira"], case_sensitive=False),
        )
        config["providers"]["issues"] = issues

        state = click.prompt(
            "  State store",
            default=config["providers"]["state"],
            type=click.Choice(["sqlite", "redis", "file"], case_sensitive=False),
        )
        config["providers"]["state"] = state

        telemetry = click.prompt(
            "  Telemetry",
            default=config["providers"]["telemetry"],
            type=click.Choice(["console", "file", "otlp"], case_sensitive=False),
        )
        config["providers"]["telemetry"] = telemetry

        ci_platform = ci or click.prompt(
            "  CI platform",
            default=config["ci"]["platform"],
            type=click.Choice(["local", "github", "gitlab", "bitbucket"], case_sensitive=False),
        )
        config["ci"]["platform"] = ci_platform

        # Warn about providers that require optional extras
        extras_map = {
            "jira": "ag-os[jira]",
            "linear": "ag-os[linear]",
            "redis": "ag-os[redis]",
            "otlp": "ag-os[otlp]",
        }
        for surface_key in ("issues", "state", "telemetry"):
            chosen = config["providers"].get(surface_key, "")
            if chosen in extras_map:
                print(f"  [INFO] '{chosen}' requires: pip install {extras_map[chosen]}")
    else:
        if ci:
            config["ci"]["platform"] = ci

    print()

    # Write antigravity.yaml
    yaml_path = Path("antigravity.yaml")
    with open(yaml_path, "w", encoding="utf-8") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)
    print(f"  [OK] Created: {yaml_path}")

    # Create .agent/rules/ directory with Constitution
    rules_dir = Path(".agent/rules")
    rules_dir.mkdir(parents=True, exist_ok=True)
    _install_constitution(rules_dir)
    print(f"  [OK] Created: {rules_dir}/ (9 governance rules)")

    # Create Flight Recorder schema
    docs_dir = Path("docs")
    docs_dir.mkdir(exist_ok=True)
    schema_path = docs_dir / "Flight_Recorder_Schema.json"
    _write_flight_recorder_schema(schema_path)
    print(f"  [OK] Created: {schema_path}")

    # Install pre-push hook
    _install_git_hook()
    print("  [OK] Installed: pre-push git hook")

    print()
    print("  Run 'ag-os demo' to see it in action.")
    print()


# ──────────────────────────────────────────────────────────────
# ag-os check
# ──────────────────────────────────────────────────────────────


@main.command()
@click.argument("units", default=1.0, type=float)
@click.option("--tier", default="standard_cpu", help="Resource pricing tier.")
def check(units, tier):
    """Run a solvency check against the budget cap."""
    from ag_os.core.cost_guard import check_solvency, print_solvency_report

    config = load_config()
    result = check_solvency(units=units, tier=tier, config=config)
    print_solvency_report(result)

    if not result.is_solvent:
        sys.exit(1)


# ──────────────────────────────────────────────────────────────
# ag-os demo
# ──────────────────────────────────────────────────────────────


@main.command()
def demo():
    """Run the 60-second governance demo."""
    from ag_os.core.cost_guard import check_solvency, print_solvency_report
    from ag_os.core.flight_recorder import FlightRecorder
    from ag_os.core.rules_engine import evaluate_governance, print_policy_report

    config = load_config()

    print()
    print("  ================================================")
    print("  Antigravity OS -- 60-Second Governance Demo")
    print("  ================================================")
    print()

    # Step 1: Policy Check (Rule 00 -- Plan First)
    print("  Step 1: Policy Check (Rule 00 -- Plan First)")
    print("  ---------------------------------------------")
    result = evaluate_governance(
        {"requires_plan": True, "has_plan": True, "state": "PLANNING"},
        config=config,
    )
    print_policy_report(result)

    # Step 2: Solvency Check (Rule 08 -- Economic Safety)
    print("  Step 2: Solvency Check (Rule 08 -- Economic Safety)")
    print("  ----------------------------------------------------")
    solvency = check_solvency(units=1.0, tier="standard_cpu", config=config)
    print_solvency_report(solvency)

    # Step 3: Flight Recorder (Rule 05 -- State Tracking)
    print("  Step 3: Flight Recorder (Rule 05 -- State Tracking)")
    print("  ----------------------------------------------------")
    recorder = FlightRecorder(config=config)
    recorder.transition("demo-operation", "PLANNING")
    recorder.transition("demo-operation", "PLAN_APPROVED")
    recorder.transition("demo-operation", "BUILDING", metadata={"demo": True})
    recorder.transition("demo-operation", "VERIFYING")
    recorder.transition("demo-operation", "COMPLETE")
    recorder.reset("demo-operation")

    # Step 4: Blocked scenario
    print("  Step 4: Budget Exceeded Scenario")
    print("  ---------------------------------")
    blocked = check_solvency(units=100.0, tier="gpu_large", config=config)
    print_solvency_report(blocked)

    print("  ================================================")
    print("  Demo complete. All governance gates operational.")
    print("  ================================================")
    print()


# ──────────────────────────────────────────────────────────────
# ag-os status
# ──────────────────────────────────────────────────────────────


@main.command()
def status():
    """Show current provider configuration."""
    config = load_config()
    config_path = config.get("_config_path", "Not found")

    print()
    print("  Antigravity OS Status")
    print("  ---------------------")
    print(f"  Config:      {config_path}")
    print(f"  Monthly cap: ${config.get('monthly_cap', 0):.2f}")
    print(f"  Max loops:   {config.get('max_loop_count', 5)}")
    print()
    print("  Providers:")
    providers = config.get("providers", {})
    for surface, name in sorted(providers.items()):
        print(f"    {surface:12s} -> {name}")
    print()
    print(f"  CI platform: {config.get('ci', {}).get('platform', 'local')}")
    print()


# ──────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────

_CONSTITUTION_RULES = {
    "00-plan-first": (
        "# Rule 00: Plan First\n"
        "\n"
        "Every task requires an approved plan before execution begins.\n"
        "No code changes without a written, reviewed implementation plan.\n"
    ),
    "01-data-contracts": (
        "# Rule 01: Data Contracts\n"
        "\n"
        "All inter-service and inter-agent data exchange must use\n"
        "explicit, validated data contracts. Schema changes require review.\n"
    ),
    "02-fail-closed": (
        "# Rule 02: Fail Closed\n"
        "\n"
        "On any ambiguous, unknown, or error state, the system halts\n"
        "and escalates to a human operator. Never proceed on uncertainty.\n"
    ),
    "03-sentinel": (
        "# Rule 03: Zero Trust Dependencies\n"
        "\n"
        "Every external dependency (API, service, model) is treated as\n"
        "untrusted until verified. Validate inputs. Validate outputs.\n"
    ),
    "04-governance": (
        "# Rule 04: Governance Gate\n"
        "\n"
        "All state transitions must pass through the governance gate.\n"
        "No direct state mutations. Every change is auditable.\n"
    ),
    "05-flight-recorder": (
        "# Rule 05: Flight Recorder\n"
        "\n"
        "Every operation is tracked through a deterministic state machine.\n"
        "State transitions are logged, timestamped, and persisted.\n"
    ),
    "06-handover": (
        "# Rule 06: Agent Handover\n"
        "\n"
        "When transferring work between agents, a structured handover\n"
        "contract must be created containing context, state, and next steps.\n"
    ),
    "07-telemetry": (
        "# Rule 07: Loop Detection\n"
        "\n"
        "Maximum retry loops are enforced. If an agent exceeds the\n"
        "configured max_loop_count, execution halts and escalates.\n"
    ),
    "08-economic-safety": (
        "# Rule 08: Economic Safety (The Solvency Gate)\n"
        "\n"
        "No operation may proceed if the projected spend would exceed\n"
        "the monthly budget cap. The Cost Guard enforces this gate.\n"
    ),
}


def _install_constitution(rules_dir: Path):
    """Write the 9 Constitution rules as Markdown files."""
    for filename, content in _CONSTITUTION_RULES.items():
        rule_path = rules_dir / f"{filename}.md"
        if not rule_path.exists():
            rule_path.write_text(content, encoding="utf-8")


def _write_flight_recorder_schema(path: Path):
    """Write the Flight Recorder JSON Schema."""
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "Flight Recorder Entry",
        "type": "object",
        "required": ["trace_id", "operation", "state", "timestamp"],
        "properties": {
            "trace_id": {"type": "string"},
            "operation": {"type": "string"},
            "state": {
                "type": "string",
                "enum": [
                    "IDLE",
                    "PLANNING",
                    "PLAN_APPROVED",
                    "BUILDING",
                    "VERIFYING",
                    "COMPLETE",
                    "BLOCKED",
                    "ROLLED_BACK",
                ],
            },
            "timestamp": {"type": "string", "format": "date-time"},
            "previous_state": {"type": "string"},
            "metadata": {"type": "object"},
            "error": {"type": "string"},
        },
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(schema, f, indent=2)


def _install_git_hook():
    """Install a pre-push git hook that runs ag-os check."""
    hooks_dir = Path(".git/hooks")
    if not hooks_dir.exists():
        return  # Not a git repo

    hook_path = hooks_dir / "pre-push"
    hook_content = """#!/bin/sh
# Antigravity OS -- Pre-push governance check
# Runs solvency verification before allowing push

echo "  Running Antigravity OS pre-push check..."
ag-os check 1.0 --tier standard_cpu
exit $?
"""
    hook_path.write_text(hook_content, encoding="utf-8")
    hook_path.chmod(0o755)


if __name__ == "__main__":
    main()
