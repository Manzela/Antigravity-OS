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


def print_policy_report(result: PolicyResult) -> None:
    """Print a human-readable policy evaluation report."""
    status = "ALLOWED" if result.allowed else "BLOCKED"
    indicator = "[OK]" if result.allowed else "[BLOCKED]"

    print(f"\n  {indicator} Governance Gate: {status}")

    if result.violations:
        print(f"  Violations ({len(result.violations)}):")
        for v in result.violations:
            print(f"    - {v}")
    else:
        print("  All governance rules satisfied.")
    print()
