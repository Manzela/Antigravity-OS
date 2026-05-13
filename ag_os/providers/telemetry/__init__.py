"""Telemetry provider interface."""

from abc import ABC, abstractmethod
from typing import Any


class TelemetryProvider(ABC):
    """Abstract base class for observability/telemetry backends."""

    @abstractmethod
    def emit_trace(self, trace_payload: dict[str, Any]) -> str | None:
        """Emit a trace/span. Returns trace URL if available."""
        ...

    @abstractmethod
    def emit_metric(
        self,
        name: str,
        value: float,
        tags: dict[str, str] | None = None,
    ) -> None:
        """Emit a metric (e.g., cost, loop_count, duration)."""
        ...
