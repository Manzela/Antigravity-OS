"""
Antigravity OS CLI — The `ag-os` command.

Subcommands:
    ag-os init     Initialize a new project with antigravity.yaml
    ag-os check    Run a solvency check against the budget cap
    ag-os demo     Run the 60-second governance demo
    ag-os dream    Run the Dreaming Module self-improvement cycle
    ag-os status   Show current provider configuration
    ag-os serve    Start the MCP server for AI agent integration
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


@click.group(invoke_without_command=True)
@click.version_option(__version__, prog_name="ag-os")
@click.pass_context
def main(ctx):
    """Antigravity OS -- The governance kernel for AI agents."""
    if ctx.invoked_subcommand is None:
        try:
            from ag_os.interactive import interactive_main

            interactive_main()
        except ImportError:
            print("  [ERROR] Interactive shell dependencies missing.")
            print("  Run: pip install ag-os[interactive] or pip install prompt_toolkit rich")
            sys.exit(1)


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
@click.option(
    "--dream",
    is_flag=True,
    help="Include Dreaming Module demo (simulated failure).",
)
def demo(dream):
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

    if dream:
        # Step 5: Dreaming Module — simulated failure → self-improvement
        _run_dream_demo(config, recorder)

    print("  ================================================")
    print("  Demo complete. All governance gates operational.")
    print("  ================================================")
    print()


def _run_dream_demo(config: dict, recorder):
    """Simulate a failing agent and invoke the Dreaming Module."""
    import uuid

    from ag_os.core.dreaming import DreamEngine, print_dream_report

    print("  Step 5: Dreaming Module (Self-Improvement Loop)")
    print("  ────────────────────────────────────────────────")
    print()
    print("  Simulating a failing agent that loops and gets stuck...")
    print()

    # Create a unique operation that will exhibit multiple friction patterns
    op_id = f"demo-failing-agent-{uuid.uuid4().hex[:8]}"

    # Simulate: agent loops through PLANNING → BUILDING → VERIFYING → ROLLED_BACK
    # multiple times, demonstrating excessive transitions and rollback cycles.
    for cycle in range(3):
        if cycle == 0:
            # First cycle starts from IDLE → PLANNING
            recorder.transition(op_id, "PLANNING")
        # else: we are already in PLANNING from the ROLLED_BACK → PLANNING at end of prev cycle
        recorder.transition(op_id, "PLAN_APPROVED")
        recorder.transition(op_id, "BUILDING", metadata={"attempt": cycle + 1})
        recorder.transition(op_id, "VERIFYING")
        recorder.transition(
            op_id,
            "ROLLED_BACK",
            error="Tests failed: assertion error in integration suite",
        )
        recorder.transition(op_id, "PLANNING")  # Retry from ROLLED_BACK

    # Final attempt ends in BLOCKED (already in PLANNING from last cycle)
    recorder.transition(op_id, "PLAN_APPROVED")
    recorder.transition(op_id, "BUILDING", metadata={"attempt": 4, "desperate": True})
    recorder.transition(
        op_id,
        "BLOCKED",
        error="Max retries exhausted. Agent cannot resolve integration failures.",
    )

    print(f"  Simulated operation: {op_id}")
    print("  Result: 3 rollback cycles → BLOCKED (terminal failure)")
    print()
    print("  Now invoking the Dream Engine to analyze friction...")
    print()

    # Run the Dream Engine
    engine = DreamEngine(config=config)
    report = engine.dream()
    print_dream_report(report)

    # Clean up the simulated operation
    recorder.reset(op_id)


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
# ag-os serve
# ──────────────────────────────────────────────────────────────


@main.command()
def serve():
    """Start the MCP server for AI agent integration."""
    try:
        from ag_os.mcp.server import run_server
    except ImportError:
        print()
        print("  [ERROR] MCP dependencies not installed.")
        print("  Run: pip install ag-os[mcp]")
        print()
        sys.exit(1)

    print("  [OK] Starting Antigravity OS MCP Server (stdio)...", file=sys.stderr)
    run_server()


# ──────────────────────────────────────────────────────────────
# ag-os dream
# ──────────────────────────────────────────────────────────────


@main.group(invoke_without_command=True)
@click.option("--recall", default=0, type=int, help="Recall the N most recent dream reports.")
@click.option("--json-output", "use_json", is_flag=True, help="Output as JSON.")
@click.option("--dry-run", is_flag=True, help="Analyze friction but don't persist.")
@click.option("--apply", is_flag=True, help="Apply LOW-risk patches automatically.")
@click.option("--prune", "do_prune", is_flag=True, help="Prune old dream reports.")
@click.pass_context
def dream(ctx, recall, use_json, dry_run, apply, do_prune):
    """Run the Dreaming Module self-improvement cycle."""
    if ctx.invoked_subcommand is not None:
        return

    from ag_os.core.dreaming import DreamEngine, print_dream_report

    config = load_config()
    engine = DreamEngine(config=config)

    if do_prune:
        result = engine.prune()
        print()
        print(
            f"  Pruned {result['deleted_count']} reports "
            f"({result['consolidated_count']} consolidated). "
            f"{result['remaining_count']} remaining."
        )
        print()
        return

    if recall > 0:
        reports = engine.recall(n=recall)
        if not reports:
            print()
            print("  No dream reports found in memory.")
            print("  Run 'ag-os dream' to generate the first dream cycle.")
            print()
            return

        if use_json:
            import json as json_mod
            from dataclasses import asdict

            output = [asdict(r) for r in reports]
            print(json_mod.dumps(output, indent=2, default=str))
        else:
            for report in reports:
                print_dream_report(report)
        return

    # Dream cycle: scan -> synthesize -> (optionally persist)
    friction = engine.scan_friction()
    report = engine.synthesize(friction)

    if not dry_run:
        path = engine.persist(report)
        report_path_msg = f"  Persisted to: {path}"
    else:
        report_path_msg = "  [DRY RUN] Report not persisted."

    if use_json:
        import json as json_mod
        from dataclasses import asdict

        print(json_mod.dumps(asdict(report), indent=2, default=str))
    else:
        print_dream_report(report)
        print(report_path_msg)
        print()

    # Apply patches if requested
    if apply and report.proposed_patches:
        from ag_os.core.patch_applier import apply_patch, classify_risk

        # Pin the config target to the file we actually loaded so a CWD
        # change between load and apply cannot redirect writes to a
        # sibling project's antigravity.yaml.
        loaded_path = config.get("_config_path")
        pinned_config_path = Path(loaded_path) if loaded_path else None

        print("  Applying LOW-risk patches...")
        for patch in report.proposed_patches:
            risk = classify_risk(patch.patch_type)
            if risk == "LOW":
                success = apply_patch(
                    patch,
                    config_path=pinned_config_path,
                    interactive=False,
                )
                status = "applied" if success else "skipped"
                print(f"    [{status}] {patch.target}")
        print()


@dream.command("merge")
@click.argument("dirs", nargs=-1, required=True, type=click.Path(exists=True))
@click.option("--json-output", "use_json", is_flag=True, help="Output as JSON.")
def dream_merge(dirs, use_json):
    """Merge dream reports from multiple project directories."""
    from ag_os.core.aggregator import merge_dream_dirs, print_aggregated_report

    report = merge_dream_dirs(list(dirs))

    if use_json:
        import json as json_mod
        from dataclasses import asdict

        print(json_mod.dumps(asdict(report), indent=2, default=str))
    else:
        print_aggregated_report(report)


# ──────────────────────────────────────────────────────────────
# ag-os daemon
# ──────────────────────────────────────────────────────────────


@main.group()
def daemon():
    """Manage the Dream Daemon background process."""
    pass


@daemon.command("start")
def daemon_start():
    """Start the Dream Daemon in the foreground."""
    from ag_os.core.daemon import DreamDaemon

    config = load_config()
    d = DreamDaemon(config=config)
    d.run_forever()


@daemon.command("install")
def daemon_install():
    """Install the Dream Daemon as an OS service."""
    from ag_os.core.daemon import install_service

    config = load_config()
    path = install_service(config)
    print()
    print(f"  [OK] Service installed: {path}")
    print()
    if sys.platform == "darwin":
        print("  To start: launchctl load " + path)
    else:
        print("  To start: systemctl --user enable --now antigravity-daemon")
    print()


@daemon.command("uninstall")
def daemon_uninstall():
    """Remove the Dream Daemon OS service."""
    from ag_os.core.daemon import uninstall_service

    path = uninstall_service()
    if path:
        print()
        print(f"  [OK] Service removed: {path}")
        print()
    else:
        print()
        print("  No service installation found.")
        print()


@daemon.command("status")
def daemon_status():
    """Check Dream Daemon health."""
    from ag_os.core.daemon import get_daemon_status

    status = get_daemon_status()
    print()
    print("  Dream Daemon Status")
    print("  -------------------")
    print(f"  Running:     {'Yes' if status['running'] else 'No'}")
    print(f"  Healthy:     {'Yes' if status['healthy'] else 'No'}")
    if status["pid"]:
        print(f"  PID:         {status['pid']}")
    if status["last_tick"]:
        print(f"  Last tick:   {status['last_tick']}")
    print(f"  Cycles:      {status['cycle_count']}")
    if status["age_seconds"] is not None:
        age_h = status["age_seconds"] / 3600
        print(f"  Age:         {age_h:.1f}h since last tick")
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

# Locate ag-os: prefer venv, then PATH, then skip gracefully
AGOS=""
if [ -x ".venv/bin/ag-os" ]; then
    AGOS=".venv/bin/ag-os"
elif command -v ag-os >/dev/null 2>&1; then
    AGOS="ag-os"
else
    echo "  ⚠ ag-os not found (activate venv or install globally). Skipping check."
    exit 0
fi

$AGOS check 1.0 --tier standard_cpu
exit $?
"""
    hook_path.write_text(hook_content, encoding="utf-8")
    hook_path.chmod(0o755)


if __name__ == "__main__":
    main()
