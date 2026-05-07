"""Telemetry provider interface."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class TelemetryProvider(ABC):
    """Abstract base class for observability/telemetry backends."""

    @abstractmethod
    def emit_trace(self, trace_payload: Dict[str, Any]) -> Optional[str]:
        """Emit a trace/span. Returns trace URL if available."""
        ...

    @abstractmethod
    def emit_metric(
        self,
        name: str,
        value: float,
        tags: Dict[str, str] | None = None,
    ) -> None:
        """Emit a metric (e.g., cost, loop_count, duration)."""
        ...
