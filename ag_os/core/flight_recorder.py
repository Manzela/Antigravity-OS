"""
Flight Recorder — Deterministic state machine and trace builder.

Tracks the lifecycle of every agent operation through defined states.
Implements Rule 05 of the Constitution.
"""

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict

from ag_os.config import load_config
from ag_os.providers.registry import get_provider

# Valid state transitions (deterministic state machine)
_VALID_TRANSITIONS = {
    "IDLE": ["PLANNING"],
    "PLANNING": ["PLAN_APPROVED", "BLOCKED"],
    "PLAN_APPROVED": ["BUILDING"],
    "BUILDING": ["VERIFYING", "BLOCKED", "ROLLED_BACK"],
    "VERIFYING": ["COMPLETE", "BUILDING", "BLOCKED", "ROLLED_BACK"],
    "BLOCKED": ["PLANNING", "IDLE"],
    "ROLLED_BACK": ["PLANNING", "IDLE"],
    "COMPLETE": ["IDLE"],
}


@dataclass
class FlightRecord:
    """A single flight recorder entry capturing agent state."""

    trace_id: str
    operation: str
    state: str
    timestamp: str = ""
    previous_state: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()
        if not self.trace_id:
            raw = f"{self.operation}-{self.timestamp}"
            self.trace_id = hashlib.md5(raw.encode()).hexdigest()[:12]


class FlightRecorder:
    """Tracks agent operations through a deterministic state machine.

    Usage:
        recorder = FlightRecorder()
        recorder.transition("deploy-api", "PLANNING")
        recorder.transition("deploy-api", "PLAN_APPROVED")
        recorder.transition("deploy-api", "BUILDING", metadata={"branch": "main"})
    """

    def __init__(self, config: dict | None = None):
        self._config = config or load_config()
        provider_name = self._config.get("providers", {}).get("state", "sqlite")
        self._state = get_provider("state", provider_name)

        telemetry_name = self._config.get("providers", {}).get("telemetry", "console")
        self._telemetry = get_provider("telemetry", telemetry_name)

    def get_current_state(self, operation: str) -> str:
        """Get the current state for an operation."""
        stored = self._state.get(f"flight:{operation}:state")
        return stored or "IDLE"

    def transition(
        self,
        operation: str,
        new_state: str,
        metadata: Dict[str, Any] | None = None,
        error: str = "",
    ) -> FlightRecord:
        """Transition an operation to a new state.

        Enforces the deterministic state machine. Invalid transitions
        are blocked (Rule 02: Fail Closed).

        Args:
            operation: Name of the operation being tracked.
            new_state: Target state to transition to.
            metadata: Optional metadata to attach to the record.
            error: Optional error message if transitioning to BLOCKED.

        Raises:
            ValueError: If the transition is not allowed by the state machine.

        Returns:
            The recorded FlightRecord.
        """
        current = self.get_current_state(operation)

        # Validate transition
        allowed = _VALID_TRANSITIONS.get(current, [])
        if new_state not in allowed:
            raise ValueError(
                f"Invalid state transition: {current} -> {new_state}. "
                f"Allowed transitions from {current}: {allowed}. "
                f"Rule 02: Fail Closed."
            )

        # Create the record
        record = FlightRecord(
            trace_id="",
            operation=operation,
            state=new_state,
            previous_state=current,
            metadata=metadata or {},
            error=error,
        )

        # Persist the new state
        self._state.set(f"flight:{operation}:state", new_state)
        self._state.set(
            f"flight:{operation}:record:{record.timestamp}",
            json.dumps(asdict(record)),
        )

        # Emit telemetry
        self._telemetry.emit_trace(
            {
                "trace_id": record.trace_id,
                "operation": operation,
                "status": new_state,
                "previous_state": current,
                **record.metadata,
            }
        )

        return record

    def get_history(self, operation: str) -> list[FlightRecord]:
        """Retrieve the full state history for an operation.

        Scans the state store for all persisted flight records matching
        the operation prefix and returns them in chronological order.
        """
        records: list[FlightRecord] = []

        # Use the state provider's underlying storage to scan for records.
        # The key pattern is: flight:{operation}:record:{timestamp}
        prefix = f"flight:{operation}:record:"

        # For providers that expose a scan/list method, use it.
        # For SQLite, we query directly via the provider's connection.
        if hasattr(self._state, "_connect"):
            import sqlite3

            try:
                with self._state._connect() as conn:
                    rows = conn.execute(
                        "SELECT value FROM state WHERE key LIKE ? ORDER BY key ASC",
                        (f"{prefix}%",),
                    ).fetchall()
                for (raw_value,) in rows:
                    try:
                        data = json.loads(raw_value)
                        records.append(FlightRecord(**data))
                    except (json.JSONDecodeError, TypeError):
                        continue
            except sqlite3.Error:
                pass

        return records

    def reset(self, operation: str) -> None:
        """Reset an operation back to IDLE state."""
        self._state.delete(f"flight:{operation}:state")
