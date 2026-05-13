"""Policy provider interface (The Sentinel)."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class PolicyResult:
    """Result of a policy evaluation."""

    allowed: bool
    violations: list[str] = field(default_factory=list)
    policy_name: str = ""


class PolicyProvider(ABC):
    """Abstract base class for policy evaluation backends."""

    @abstractmethod
    def evaluate(
        self,
        input_data: dict,
        policy_name: str = "governance",
    ) -> PolicyResult:
        """Evaluate input against a policy. Returns allow/deny + violations."""
        ...

    @abstractmethod
    def list_policies(self) -> list[str]:
        """List available policy names."""
        ...
