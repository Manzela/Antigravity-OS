"""Cost provider interface (The Solvency Gate)."""

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class SolvencyResult:
    """Result of a solvency check against the monthly budget cap."""

    is_solvent: bool
    current_spend: float
    projected_cost: float
    monthly_cap: float
    margin: float
    lease_token: str = ""


class CostProvider(ABC):
    """Abstract base class for cost/billing backends.

    The `check_solvency()` method is shared across all providers.
    Subclasses only need to implement `get_current_spend()` and `get_tier_rate()`.
    """

    @abstractmethod
    def get_current_spend(self) -> float:
        """Fetch current month-to-date spend in USD."""
        ...

    @abstractmethod
    def get_tier_rate(self, tier: str) -> float:
        """Get the per-unit cost for a hardware/resource tier."""
        ...

    def check_solvency(
        self,
        units: float,
        tier: str,
        config: dict | None = None,
    ) -> SolvencyResult:
        """Core solvency logic -- shared across all providers.

        This is the governance kernel's economic safety gate (Rule 08).
        The logic is invariant: providers supply data, this method enforces policy.

        Args:
            units: Number of resource units to allocate.
            tier: Resource pricing tier name.
            config: Parsed antigravity.yaml config dict. Falls back to env var.

        Returns:
            SolvencyResult with is_solvent=True if within budget.
        """
        current = self.get_current_spend()
        rate = self.get_tier_rate(tier)
        projected = units * rate
        cap = float(
            (config or {}).get(
                "monthly_cap",
                os.getenv("AG_OS_MONTHLY_CAP", "50.00"),
            )
        )
        total = current + projected
        margin = cap - total

        return SolvencyResult(
            is_solvent=(total <= cap),
            current_spend=current,
            projected_cost=projected,
            monthly_cap=cap,
            margin=margin,
        )
