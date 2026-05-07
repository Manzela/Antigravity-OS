"""Console telemetry provider (DEFAULT) -- pretty-prints traces and metrics."""

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from ag_os.providers.registry import register
from ag_os.providers.telemetry import TelemetryProvider


@register("telemetry", "console")
class ConsoleTelemetryProvider(TelemetryProvider):
    """Prints human-readable trace and metric output to stdout.

    Useful for local development and debugging. Upgrade to OTLP,
    GCP Trace, or Datadog for production observability.
    """

    def __init__(self, **kwargs):
        pass

    def emit_trace(self, trace_payload: Dict[str, Any]) -> Optional[str]:
        timestamp = datetime.now(timezone.utc).strftime("%H:%M:%S.%f")[:-3]
        trace_id = trace_payload.get("trace_id", "unknown")
        status = trace_payload.get("status", "unknown")
        operation = trace_payload.get("operation", "")

        print(f"  [{timestamp}] TRACE {trace_id}")
        if operation:
            print(f"             Operation: {operation}")
        print(f"             Status:    {status}")

        for key, value in trace_payload.items():
            if key not in ("trace_id", "status", "operation", "timestamp"):
                print(f"             {key}: {value}")
        print()

        return None  # Console provider has no trace URL

    def emit_metric(
        self,
        name: str,
        value: float,
        tags: Dict[str, str] | None = None,
    ) -> None:
        timestamp = datetime.now(timezone.utc).strftime("%H:%M:%S.%f")[:-3]
        tag_str = ""
        if tags:
            tag_str = " " + " ".join(f"{k}={v}" for k, v in sorted(tags.items()))
        print(f"  [{timestamp}] METRIC {name}={value:.4f}{tag_str}")
