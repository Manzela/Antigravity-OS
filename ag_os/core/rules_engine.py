"""
Rules Engine — Evaluates governance policies using the configured policy provider.

Orchestrates policy checks across the Constitution (Rules 00-08).
"""

from ag_os.config import load_config
from ag_os.providers.policy import PolicyResult
from ag_os.providers.registry import get_provider


def evaluate_governance(
    input_data: dict,
    config: dict | None = None,
) -> PolicyResult:
    """Evaluate input data against the governance Constitution.

    Args:
        input_data: Context dict with keys like "has_plan", "is_solvent", "state".
        config: Optional pre-loaded config. Auto-loads if None.

    Returns:
        PolicyResult with allowed=True if all rules pass, violations list otherwise.
    """
    if config is None:
        config = load_config()

    # Inject config values into input data for policy evaluation
    input_data.setdefault("max_loop_count", config.get("max_loop_count", 5))

    provider_name = config.get("providers", {}).get("policy", "builtin")
    provider = get_provider("policy", provider_name)

    return provider.evaluate(input_data)


def format_policy_report(result: PolicyResult) -> str:
    """Render a human-readable policy evaluation report as a string.

    Side-effect-free primitive; safe for MCP / log handlers.
    """
    status = "ALLOWED" if result.allowed else "BLOCKED"
    indicator = "[OK]" if result.allowed else "[BLOCKED]"

    lines = ["", f"  {indicator} Governance Gate: {status}"]

    if result.violations:
        lines.append(f"  Violations ({len(result.violations)}):")
        lines.extend(f"    - {v}" for v in result.violations)
    else:
        lines.append("  All governance rules satisfied.")

    lines.append("")
    return "\n".join(lines)


def print_policy_report(result: PolicyResult) -> None:
    """Print the formatted policy report to stdout (CLI use only)."""
    print(format_policy_report(result))
