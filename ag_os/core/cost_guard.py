"""
Cost Guard — The economic safety gate for Antigravity OS.

Orchestrates solvency checks using the configured cost provider.
Implements Rule 08 of the Constitution.
"""

from ag_os.config import load_config
from ag_os.providers.cost import SolvencyResult
from ag_os.providers.registry import get_provider


def check_solvency(
    units: float = 1.0,
    tier: str = "standard_cpu",
    config: dict | None = None,
) -> SolvencyResult:
    """Run a solvency check against the configured cost provider.

    This is the primary public API for Cost Guard. It loads the config,
    instantiates the configured cost provider, and runs the solvency check.

    Args:
        units: Number of resource units to allocate.
        tier: Resource pricing tier name.
        config: Optional pre-loaded config dict. Auto-loads if None.

    Returns:
        SolvencyResult with is_solvent, margin, and projected cost.
    """
    if config is None:
        config = load_config()

    provider_name = config.get("providers", {}).get("cost", "local")
    provider = get_provider("cost", provider_name)

    return provider.check_solvency(units=units, tier=tier, config=config)


def print_solvency_report(result: SolvencyResult) -> None:
    """Print a human-readable solvency report to stdout."""
    status = "SOLVENT" if result.is_solvent else "INSOLVENT"
    indicator = "[OK]" if result.is_solvent else "[BLOCKED]"

    print(f"\n  {indicator} Solvency Gate: {status}")
    print(f"  Current spend:  ${result.current_spend:.2f}")
    print(f"  Projected cost: ${result.projected_cost:.2f}")
    print(f"  Monthly cap:    ${result.monthly_cap:.2f}")
    print(f"  Remaining:      ${result.margin:.2f}")

    if not result.is_solvent:
        overage = abs(result.margin)
        print(f"\n  Budget exceeded by ${overage:.2f}. Execution blocked.")
        print("  Increase monthly_cap in antigravity.yaml or reduce resource usage.")
    print()
