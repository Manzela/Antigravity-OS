"""Issue provider interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class IssuePayload:
    """Standard payload for creating governance issues."""

    summary: str
    description: str
    fingerprint: str  # MD5 hash for deduplication
    severity: str = "high"
    owner_name: str = ""
    owner_email: str = ""
    trace_id: str = ""
    log_content: str = ""
    labels: list[str] = field(default_factory=list)


class IssueProvider(ABC):
    """Abstract base class for issue tracking backends."""

    @abstractmethod
    def create_issue(self, payload: IssuePayload) -> str:
        """Create an issue. Returns issue ID or URL."""
        ...

    @abstractmethod
    def find_duplicate(self, fingerprint: str) -> Optional[str]:
        """Find existing issue by fingerprint. Returns ID or None."""
        ...

    @abstractmethod
    def add_comment(self, issue_id: str, comment: str) -> None:
        """Append a comment to an existing issue."""
        ...
