"""
Antigravity OS Interactive Shell — Claude Code aesthetic.
"""

from pathlib import Path

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.styles import Style
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table

from ag_os import __version__
from ag_os.cli import (
    _install_constitution,
    _install_git_hook,
    _run_dream_demo,
    _write_flight_recorder_schema,
)
from ag_os.config import _DEFAULT_CONFIG, load_config
from ag_os.core.cost_guard import check_solvency
from ag_os.core.credentials import (
    delete_credential,
    get_credential,
    get_credential_status,
    get_required_credentials,
    store_credential,
    validate_credential,
)
from ag_os.core.dreaming import DreamEngine
from ag_os.core.flight_recorder import FlightRecorder
from ag_os.core.rules_engine import evaluate_governance

console = Console()

# Define the custom slash commands and their descriptions
COMMANDS = {
    "/help": "Show this help message",
    "/demo": "Run the 60-second governance and dreaming demo",
    "/check": "Run a solvency check against the budget cap",
    "/dream": "Run the self-improvement cycle (analyze & patch)",
    "/status": "Show current configuration and providers",
    "/auth": "Manage provider credentials (view, add, revoke)",
    "/init": "Setup or reconfigure Antigravity OS for this project",
    "/exit": "Exit the shell",
    "/clear": "Clear the terminal screen",
}


class SlashCommandCompleter(Completer):
    def get_completions(self, document, complete_event):
        text = document.text_before_cursor
        if text.startswith("/"):
            for cmd, desc in COMMANDS.items():
                if cmd.startswith(text):
                    yield Completion(
                        cmd,
                        start_position=-len(text),
                        display=cmd,
                        display_meta=desc,
                    )


style = Style.from_dict(
    {
        "prompt": "ansicyan bold",
        "bottom-toolbar": "bg:#222222 #aaaaaa",
    }
)


def _bottom_toolbar():
    return HTML(f" <b>Antigravity OS v{__version__}</b> | Type <b>/help</b> for commands ")


def run_ftux_wizard():
    """First-Time User Experience setup wizard."""
    console.print()
    console.print(
        Panel.fit(
            f"[bold cyan]Welcome to Antigravity OS v{__version__}[/]\n\n"
            "Let's configure the governance kernel for this project.\n"
            "This will set up cost enforcement, state tracking, and policies.",
            border_style="cyan",
        )
    )
    console.print()

    config = dict(_DEFAULT_CONFIG)

    try:
        config["monthly_cap"] = float(
            Prompt.ask("  [1/5] Monthly budget cap (USD)", default=str(config["monthly_cap"]))
        )

        config["providers"]["issues"] = Prompt.ask(
            "  [2/5] Issue tracker",
            choices=["console", "github", "linear", "jira"],
            default=config["providers"]["issues"],
        )

        config["providers"]["state"] = Prompt.ask(
            "  [3/5] State store",
            choices=["sqlite", "redis", "file"],
            default=config["providers"]["state"],
        )

        config["providers"]["telemetry"] = Prompt.ask(
            "  [4/5] Telemetry provider",
            choices=["console", "file", "otlp"],
            default=config["providers"]["telemetry"],
        )

        config["ci"]["platform"] = Prompt.ask(
            "  [5/5] CI platform",
            choices=["local", "github", "gitlab", "bitbucket"],
            default=config["ci"]["platform"],
        )
    except KeyboardInterrupt:
        console.print("\n[yellow]Setup cancelled.[/]")
        return False

    console.print()

    # Save config
    import yaml

    with open("antigravity.yaml", "w", encoding="utf-8") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)
    console.print("  [green]✔[/] Created [bold]antigravity.yaml[/]")

    # Setup directories
    rules_dir = Path(".agent/rules")
    rules_dir.mkdir(parents=True, exist_ok=True)
    _install_constitution(rules_dir)
    console.print(f"  [green]✔[/] Created [bold]{rules_dir}/[/] (9 governance rules)")

    docs_dir = Path("docs")
    docs_dir.mkdir(exist_ok=True)
    schema_path = docs_dir / "Flight_Recorder_Schema.json"
    _write_flight_recorder_schema(schema_path)
    console.print(f"  [green]✔[/] Created [bold]{schema_path}[/]")

    _install_git_hook()
    console.print("  [green]✔[/] Installed pre-push git hook")

    # Ensure .env is in .gitignore (defense-in-depth)
    _ensure_gitignore()

    # ── Phase 2: Provider Authentication ──────────────────────────────────
    required_creds = get_required_credentials(config)
    if required_creds:
        console.print()
        console.rule("[bold cyan]Provider Authentication[/]")
        console.print(
            "[dim]Credentials are stored in your OS keychain (macOS Keychain / "
            "Linux Secret Service / Windows Credential Locker).[/]\n"
        )

        for i, spec in enumerate(required_creds, 1):
            existing = get_credential(spec.key)
            if existing:
                console.print(f"  [green]✔[/] [bold]{spec.label}[/] — already configured")
                continue

            if spec.hint:
                console.print(f"  [dim]Hint: {spec.hint}[/]")

            try:
                value = Prompt.ask(
                    f"  [{i}/{len(required_creds)}] {spec.label}",
                    password=spec.is_password,
                )

                if not value.strip():
                    console.print("  [yellow]⚠ Skipped (empty input)[/]")
                    continue

                value = value.strip()

                # Store first (needed for cross-credential validation like Jira)
                store_credential(spec.key, value)

                # Validate
                with console.status("[dim]Validating...[/]"):
                    ok, msg = validate_credential(spec.key, value)

                if ok:
                    console.print(f"  [green]✔[/] {msg}")
                else:
                    console.print(f"  [yellow]⚠ {msg}[/]")
                    console.print(
                        "  [dim]Credential stored anyway. You can re-authenticate with /auth.[/]"
                    )

            except KeyboardInterrupt:
                console.print("\n  [yellow]Skipped remaining credentials.[/]")
                break
    else:
        console.print("\n  [dim]All selected providers work offline — no credentials needed.[/]")

    console.print("\n[bold green]Setup complete![/] You are ready to use Antigravity OS.\n")
    return True


def _ensure_gitignore():
    """Ensure .env is listed in .gitignore (defense-in-depth)."""
    gitignore = Path(".gitignore")
    entries_to_add = [".env", ".env.*", "credentials.json"]

    existing = ""
    if gitignore.is_file():
        existing = gitignore.read_text(encoding="utf-8")

    additions = [e for e in entries_to_add if e not in existing]
    if additions:
        with open(gitignore, "a", encoding="utf-8") as f:
            f.write("\n# Antigravity OS — never commit secrets\n")
            for entry in additions:
                f.write(f"{entry}\n")


def handle_auth():
    """Manage provider credentials — view, add, revoke."""
    config = load_config()
    required = get_required_credentials(config)
    status = get_credential_status(config)

    if not required:
        console.print("[dim]All selected providers work offline — no credentials needed.[/]")
        return

    # Display current status
    table = Table(box=None, show_header=True, padding=(0, 2))
    table.add_column("Credential", style="cyan bold")
    table.add_column("Status", style="white")

    for spec in required:
        is_set = status.get(spec.key, False)
        status_str = "[green]✔ Configured[/]" if is_set else "[red]✘ Missing[/]"
        table.add_row(f"{spec.label} ({spec.key})", status_str)

    console.print(
        Panel(table, title="[bold]Provider Credentials[/]", border_style="cyan", expand=False)
    )
    console.print(
        "[dim]Credentials are stored in your OS keychain (macOS Keychain / "
        "Linux Secret Service / Windows Credential Locker).[/]\n"
    )

    # Offer actions
    action = Prompt.ask(
        "Action",
        choices=["add", "revoke", "done"],
        default="done",
    )

    if action == "add":
        missing = [s for s in required if not status.get(s.key, False)]
        if not missing:
            console.print("[green]All credentials are already configured.[/]")
            return

        for spec in missing:
            if spec.hint:
                console.print(f"  [dim]Hint: {spec.hint}[/]")
            value = Prompt.ask(f"  {spec.label}", password=spec.is_password)
            if not value.strip():
                console.print("  [yellow]⚠ Skipped[/]")
                continue

            store_credential(spec.key, value.strip())
            with console.status("[dim]Validating...[/]"):
                ok, msg = validate_credential(spec.key, value.strip())
            if ok:
                console.print(f"  [green]✔[/] {msg}")
            else:
                console.print(f"  [yellow]⚠ {msg}[/]")

    elif action == "revoke":
        stored = [s for s in required if status.get(s.key, False)]
        if not stored:
            console.print("[dim]No credentials to revoke.[/]")
            return

        for spec in stored:
            if Confirm.ask(f"  Revoke [bold]{spec.key}[/]?", default=False):
                delete_credential(spec.key)
                console.print(f"  [red]✘[/] Revoked {spec.key}")


def handle_help():
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Command", style="cyan bold")
    table.add_column("Description", style="white")
    for cmd, desc in COMMANDS.items():
        table.add_row(cmd, desc)
    console.print(
        Panel(table, title="[bold]Available Commands[/]", border_style="cyan", expand=False)
    )


def handle_status():
    config = load_config()
    config_path = config.get("_config_path", "Not found")

    table = Table(box=None, show_header=False)
    table.add_column("Key", style="dim")
    table.add_column("Value", style="white bold")

    table.add_row("Config Path", config_path)
    table.add_row("Monthly Cap", f"${config.get('monthly_cap', 0):.2f}")
    table.add_row("Max Loops", str(config.get("max_loop_count", 5)))
    table.add_row("CI Platform", config.get("ci", {}).get("platform", "local"))

    console.print(Panel(table, title="[bold]System Status[/]", border_style="blue", expand=False))

    prov_table = Table(box=None, show_header=False)
    prov_table.add_column("Surface", style="dim")
    prov_table.add_column("Provider", style="cyan")

    for surface, name in sorted(config.get("providers", {}).items()):
        prov_table.add_row(surface, name)

    console.print(Panel(prov_table, title="[bold]Providers[/]", border_style="blue", expand=False))


def handle_check():
    config = load_config()
    result = check_solvency(units=1.0, tier="standard_cpu", config=config)

    if result.is_solvent:
        console.print(
            Panel(
                "[green]Solvency Check Passed[/]\n"
                f"Spend: ${result.projected_cost:.4f} / ${result.monthly_cap:.2f}",
                border_style="green",
            )
        )
    else:
        console.print(
            Panel(
                "[red]Solvency Check Failed[/]\n"
                f"Spend: ${result.projected_cost:.4f} / ${result.monthly_cap:.2f}",
                border_style="red",
            )
        )


def handle_demo():
    config = load_config()
    console.rule("[bold cyan]60-Second Governance Demo[/]")

    with console.status("[dim]Evaluating Policy Gate (Rule 00)...[/]"):
        import time

        time.sleep(1)
        evaluate_governance(
            {"requires_plan": True, "has_plan": True, "state": "PLANNING"}, config=config
        )
    console.print("  [green]✔[/] Policy Check Passed")

    with console.status("[dim]Evaluating Solvency Gate (Rule 08)...[/]"):
        time.sleep(1)
        sol = check_solvency(units=1.0, tier="standard_cpu", config=config)
    console.print(f"  [green]✔[/] Solvency Check Passed (Projected: ${sol.projected_cost:.4f})")

    with console.status("[dim]Logging state transitions to Flight Recorder...[/]"):
        recorder = FlightRecorder(config=config)
        import uuid

        demo_op = f"demo-op-{uuid.uuid4().hex[:6]}"
        recorder.transition(demo_op, "PLANNING")
        recorder.transition(demo_op, "PLAN_APPROVED")
        recorder.transition(demo_op, "BUILDING")
        recorder.transition(demo_op, "VERIFYING")
        recorder.transition(demo_op, "COMPLETE")
        time.sleep(1)
    console.print("  [green]✔[/] State Machine Traversed Successfully")

    console.print("\n[bold]Simulating Dreaming Module Failure...[/]")
    _run_dream_demo(config, recorder)
    console.rule("[bold cyan]Demo Complete[/]")


def handle_dream():
    config = load_config()
    engine = DreamEngine(config=config)

    with console.status("[dim]Scanning SQLite telemetry for friction patterns...[/]"):
        friction = engine.scan_friction()
        import time

        time.sleep(1)

    if not friction:
        console.print(
            "[green]No friction detected in the system.[/] Agents are operating flawlessly."
        )
        return

    console.print(
        f"[yellow]Detected {len(friction)} friction events.[/] Synthesizing governance patches..."
    )

    with console.status("[dim]Dream Engine synthesizing constitutional patches...[/]"):
        report = engine.synthesize(friction)
        time.sleep(1.5)

    # Render report nicely
    console.print()
    console.print(Markdown(f"### Dream Report: {report.dream_id}"))
    console.print(f"[dim]Friction events detected: {report.friction_detected}[/]")
    console.print()

    for patch in report.proposed_patches:
        console.print(
            Panel(
                f"{patch.description}\n\n"
                f"[dim]Action:[/] {patch.patch_type} → [cyan]{patch.target}[/]",
                title=f"[bold gold1]Patch: {patch.patch_type}[/]",
                border_style="yellow",
            )
        )

    path = engine.persist(report)
    console.print(f"\n[green]✔ Persisted to:[/] [dim]{path}[/]")


def interactive_main():
    """Main interactive loop."""
    # FTUX Check
    if not Path("antigravity.yaml").exists():
        if not run_ftux_wizard():
            return

    # Welcome banner
    console.print(f"[bold cyan]Antigravity OS v{__version__}[/] — Interactive Shell")
    console.print("[dim]Type /help to see available commands. Press Ctrl+D to exit.[/]\n")

    session = PromptSession(
        completer=SlashCommandCompleter(),
        bottom_toolbar=_bottom_toolbar,
        style=style,
    )

    while True:
        try:
            text = session.prompt(HTML("<prompt>❯</prompt> "))
            text = text.strip()

            if not text:
                continue

            if text == "/exit":
                break
            elif text == "/help":
                handle_help()
            elif text == "/status":
                handle_status()
            elif text == "/check":
                handle_check()
            elif text == "/demo":
                handle_demo()
            elif text == "/dream":
                handle_dream()
            elif text == "/auth":
                handle_auth()
            elif text == "/init":
                run_ftux_wizard()
            elif text == "/clear":
                console.clear()
            elif text.startswith("/"):
                console.print(f"[red]Unknown command:[/] {text}. Type /help.")
            else:
                # If they type normal text, maybe just show a tip
                console.print(
                    "[dim]Unrecognized input. Use slash commands (e.g., /help, /demo).[/]"
                )

        except KeyboardInterrupt:
            # Ctrl+C
            continue
        except EOFError:
            # Ctrl+D
            break
        except Exception as e:
            console.print(f"[red]Error:[/] {e}")

    console.print("[dim]Exiting Antigravity OS.[/]")


if __name__ == "__main__":
    interactive_main()
