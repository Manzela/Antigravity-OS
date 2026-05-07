"""
Dreaming Module — The self-improvement loop for AI agents.

Analyzes Flight Recorder telemetry for friction patterns (loops,
rollbacks, budget failures) and synthesizes Dream Reports with
proposed governance patches. Persists learnings as long-term
memory in ~/.antigravity/dreams/.

This module is model-agnostic and has zero LLM dependencies.
Any AI agent that reads the output gains self-improvement.
"""

import json
import sqlite3
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from ag_os.config import load_config
from ag_os.providers.registry import get_provider

# ──────────────────────────────────────────────────────────────
# Data Structures
# ──────────────────────────────────────────────────────────────

# Friction archetypes — deterministic classifications
LOOP_DETECTED = "LOOP_DETECTED"
BUDGET_EXCEEDED = "BUDGET_EXCEEDED"
ROLLBACK_CYCLE = "ROLLBACK_CYCLE"
BLOCKED_TERMINAL = "BLOCKED_TERMINAL"
EXCESSIVE_TRANSITIONS = "EXCESSIVE_TRANSITIONS"

# Severity levels
SEVERITY_LOW = "LOW"
SEVERITY_MEDIUM = "MEDIUM"
SEVERITY_HIGH = "HIGH"
SEVERITY_CRITICAL = "CRITICAL"


@dataclass
class FrictionEvent:
    """A single detected friction pattern from execution history."""

    operation: str
    archetype: str
    severity: str
    diagnosis: str
    evidence: dict[str, Any] = field(default_factory=dict)


@dataclass
class GovernancePatch:
    """A proposed governance improvement derived from friction analysis."""

    patch_type: str  # NEW_RULE | CONFIG_CHANGE | THRESHOLD_ADJUSTMENT
    target: str  # File path or config key
    description: str
    yaml_content: str = ""


@dataclass
class DreamReport:
    """A complete Dream Report — the output of one dream cycle."""

    dream_id: str
    timestamp: str
    friction_events: list[FrictionEvent] = field(default_factory=list)
    proposed_patches: list[GovernancePatch] = field(default_factory=list)
    summary: str = ""
    operations_analyzed: int = 0
    friction_detected: int = 0


# ──────────────────────────────────────────────────────────────
# Dream Engine
# ──────────────────────────────────────────────────────────────

_DREAMS_DIR = Path.home() / ".antigravity" / "dreams"


class DreamEngine:
    """The analytical engine that powers the self-improvement loop.

    Connects to the Flight Recorder's SQLite state store, scans for
    friction patterns, synthesizes Dream Reports with proposed
    governance patches, and persists them as long-term memory.

    Usage:
        engine = DreamEngine()
        report = engine.dream()  # Full cycle: scan → synthesize → persist
        print(report.summary)

        # Or recall past learnings
        memories = engine.recall(n=5)
    """

    def __init__(self, config: dict | None = None):
        self._config = config or load_config()
        self._max_loops = self._config.get("max_loop_count", 5)

    def _get_state_provider(self):
        """Get the configured state provider."""
        provider_name = self._config.get("providers", {}).get("state", "sqlite")
        try:
            return get_provider("state", provider_name)
        except ValueError:
            return get_provider("state", "sqlite")

    def _query_all_flight_records(self) -> dict[str, list[dict]]:
        """Query the SQLite state store for all flight records.

        Returns a dict mapping operation names to their list of
        state transition records, ordered chronologically.
        """
        state = self._get_state_provider()
        operations: dict[str, list[dict]] = {}

        if not hasattr(state, "_connect"):
            return operations

        try:
            with state._connect() as conn:
                rows = conn.execute(
                    "SELECT key, value FROM state WHERE key LIKE 'flight:%:record:%' "
                    "ORDER BY key ASC"
                ).fetchall()
        except sqlite3.Error:
            return operations

        for key, raw_value in rows:
            try:
                record = json.loads(raw_value)
                op_name = record.get("operation", "")
                if op_name:
                    operations.setdefault(op_name, []).append(record)
            except (json.JSONDecodeError, TypeError):
                continue

        return operations

    def scan_friction(self) -> list[FrictionEvent]:
        """Scan the Flight Recorder for friction patterns.

        Analyzes all operations and classifies friction into
        deterministic archetypes based on state transition patterns.
        """
        operations = self._query_all_flight_records()
        friction: list[FrictionEvent] = []

        for op_name, records in operations.items():
            if not records:
                continue

            states = [r.get("state", "") for r in records]
            transition_count = len(records)
            last_state = states[-1] if states else ""

            # ── LOOP_DETECTED ──
            # Operation has more than 2× max_loop_count transitions
            loop_threshold = self._max_loops * 2
            if transition_count > loop_threshold:
                friction.append(
                    FrictionEvent(
                        operation=op_name,
                        archetype=LOOP_DETECTED,
                        severity=SEVERITY_HIGH,
                        diagnosis=(
                            f"Operation '{op_name}' executed {transition_count} transitions, "
                            f"exceeding the loop threshold of {loop_threshold} "
                            f"(2× max_loop_count={self._max_loops}). "
                            f"This indicates the agent was stuck in a retry loop."
                        ),
                        evidence={
                            "transition_count": transition_count,
                            "max_loop_count": self._max_loops,
                            "threshold": loop_threshold,
                            "states_visited": states,
                        },
                    )
                )

            # ── ROLLBACK_CYCLE ──
            # Operation visited ROLLED_BACK state 2+ times
            rollback_count = states.count("ROLLED_BACK")
            if rollback_count >= 2:
                friction.append(
                    FrictionEvent(
                        operation=op_name,
                        archetype=ROLLBACK_CYCLE,
                        severity=SEVERITY_HIGH,
                        diagnosis=(
                            f"Operation '{op_name}' was rolled back {rollback_count} times. "
                            f"Repeated rollbacks indicate a systemic issue — the agent "
                            f"keeps attempting the same failing approach."
                        ),
                        evidence={
                            "rollback_count": rollback_count,
                            "states_visited": states,
                        },
                    )
                )

            # ── BLOCKED_TERMINAL ──
            # Operation ended in BLOCKED state (terminal failure)
            if last_state == "BLOCKED":
                friction.append(
                    FrictionEvent(
                        operation=op_name,
                        archetype=BLOCKED_TERMINAL,
                        severity=SEVERITY_MEDIUM,
                        diagnosis=(
                            f"Operation '{op_name}' terminated in BLOCKED state "
                            f"after {transition_count} transitions. The agent was "
                            f"unable to resolve the blocking condition."
                        ),
                        evidence={
                            "final_state": last_state,
                            "transition_count": transition_count,
                            "states_visited": states,
                        },
                    )
                )

            # ── EXCESSIVE_TRANSITIONS ──
            # Operation has >10 transitions without reaching COMPLETE
            if transition_count > 10 and "COMPLETE" not in states:
                friction.append(
                    FrictionEvent(
                        operation=op_name,
                        archetype=EXCESSIVE_TRANSITIONS,
                        severity=SEVERITY_MEDIUM,
                        diagnosis=(
                            f"Operation '{op_name}' accumulated {transition_count} "
                            f"state transitions without ever reaching COMPLETE. "
                            f"This suggests the operation was abandoned or is pathological."
                        ),
                        evidence={
                            "transition_count": transition_count,
                            "reached_complete": False,
                            "states_visited": states,
                        },
                    )
                )

            # ── BUDGET_EXCEEDED ──
            # Check metadata for solvency failure markers
            for record in records:
                metadata = record.get("metadata", {})
                error = record.get("error", "")
                if (
                    metadata.get("solvency_failed")
                    or "budget" in error.lower()
                    or "solvency" in error.lower()
                    or "insolvent" in error.lower()
                ):
                    friction.append(
                        FrictionEvent(
                            operation=op_name,
                            archetype=BUDGET_EXCEEDED,
                            severity=SEVERITY_CRITICAL,
                            diagnosis=(
                                f"Operation '{op_name}' triggered a budget/solvency "
                                f"failure. The agent attempted to allocate resources "
                                f"beyond the monthly cap."
                            ),
                            evidence={
                                "error": error,
                                "metadata": metadata,
                            },
                        )
                    )
                    break  # One budget event per operation

        return friction

    def synthesize(self, friction_events: list[FrictionEvent]) -> DreamReport:
        """Synthesize friction events into a structured Dream Report.

        Generates root-cause diagnoses, proposed governance patches,
        and an executive summary. Pure deterministic logic — no LLM.
        """
        now = datetime.now(timezone.utc)
        dream_id = f"dream-{now.strftime('%Y%m%d-%H%M%S')}"

        operations = self._query_all_flight_records()
        patches: list[GovernancePatch] = []

        # ── Generate patches based on friction archetypes ──

        loop_events = [e for e in friction_events if e.archetype == LOOP_DETECTED]
        if loop_events:
            avg_transitions = sum(e.evidence.get("transition_count", 0) for e in loop_events) / len(
                loop_events
            )
            suggested_max = max(3, int(avg_transitions / 3))

            patches.append(
                GovernancePatch(
                    patch_type="THRESHOLD_ADJUSTMENT",
                    target="antigravity.yaml → max_loop_count",
                    description=(
                        f"Reduce max_loop_count from {self._max_loops} to "
                        f"{suggested_max}. Analysis shows loops averaging "
                        f"{avg_transitions:.0f} transitions — earlier intervention "
                        f"would save compute and prevent agent drift."
                    ),
                    yaml_content=f"max_loop_count: {suggested_max}",
                )
            )

        rollback_events = [e for e in friction_events if e.archetype == ROLLBACK_CYCLE]
        if rollback_events:
            patches.append(
                GovernancePatch(
                    patch_type="NEW_RULE",
                    target=".agent/rules/09-rollback-circuit-breaker.md",
                    description=(
                        "Add a rollback circuit breaker rule. After 2 rollbacks "
                        "on the same operation, halt execution and require human "
                        "review before retrying."
                    ),
                    yaml_content=(
                        "# Rule 09: Rollback Circuit Breaker\n\n"
                        "If an operation is rolled back more than once, the system\n"
                        "halts and escalates. Repeated rollbacks indicate a systemic\n"
                        "issue that retry alone cannot resolve.\n\n"
                        "**max_rollbacks_per_operation: 2**\n"
                    ),
                )
            )

        budget_events = [e for e in friction_events if e.archetype == BUDGET_EXCEEDED]
        if budget_events:
            patches.append(
                GovernancePatch(
                    patch_type="CONFIG_CHANGE",
                    target="antigravity.yaml → monthly_cap / pre-flight checks",
                    description=(
                        "Budget exceeded events detected. Consider adding a "
                        "pre-flight solvency check before every state transition "
                        "to catch overruns earlier in the execution cycle."
                    ),
                    yaml_content=(
                        "# Add to antigravity.yaml:\n"
                        "pre_flight_solvency_check: true  # Check budget before every transition\n"
                    ),
                )
            )

        blocked_events = [e for e in friction_events if e.archetype == BLOCKED_TERMINAL]
        if blocked_events:
            patches.append(
                GovernancePatch(
                    patch_type="NEW_RULE",
                    target=".agent/rules/10-blocked-escalation.md",
                    description=(
                        "Add an automatic escalation rule for terminally blocked "
                        "operations. When an operation reaches BLOCKED and stays "
                        "there, auto-create an issue for human review."
                    ),
                    yaml_content=(
                        "# Rule 10: Blocked State Escalation\n\n"
                        "When an operation enters the BLOCKED state and no further\n"
                        "transitions occur, automatically escalate by creating a\n"
                        "governance issue for human review.\n\n"
                        "**auto_escalate_blocked: true**\n"
                    ),
                )
            )

        # ── Build summary ──
        archetype_counts = {}
        for e in friction_events:
            archetype_counts[e.archetype] = archetype_counts.get(e.archetype, 0) + 1

        if friction_events:
            archetype_summary = ", ".join(
                f"{count} {archetype.lower().replace('_', ' ')}"
                for archetype, count in sorted(archetype_counts.items())
            )
            summary = (
                f"Dream cycle analyzed {len(operations)} operations and detected "
                f"{len(friction_events)} friction events: {archetype_summary}. "
                f"Generated {len(patches)} governance patches for self-improvement. "
                f"Apply the proposed patches to prevent recurrence in the next "
                f"execution cycle."
            )
        else:
            summary = (
                f"Dream cycle analyzed {len(operations)} operations. "
                f"No friction detected — the governance kernel is operating within "
                f"nominal parameters. No patches proposed."
            )

        return DreamReport(
            dream_id=dream_id,
            timestamp=now.isoformat(),
            friction_events=friction_events,
            proposed_patches=patches,
            summary=summary,
            operations_analyzed=len(operations),
            friction_detected=len(friction_events),
        )

    def persist(self, report: DreamReport) -> Path:
        """Persist a Dream Report to long-term memory.

        Writes the report as a YAML file to ~/.antigravity/dreams/.
        """
        _DREAMS_DIR.mkdir(parents=True, exist_ok=True)
        path = _DREAMS_DIR / f"{report.dream_id}.yaml"

        # Convert to serializable dict
        data = asdict(report)
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False, width=120)

        return path

    def recall(self, n: int = 5) -> list[DreamReport]:
        """Recall the N most recent Dream Reports from long-term memory.

        Reads YAML files from ~/.antigravity/dreams/ and returns them
        in reverse chronological order (newest first).
        """
        if not _DREAMS_DIR.is_dir():
            return []

        reports: list[DreamReport] = []
        files = sorted(_DREAMS_DIR.glob("dream-*.yaml"), reverse=True)

        for path in files[:n]:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                if data:
                    # Reconstruct nested dataclasses
                    friction = [FrictionEvent(**e) for e in data.get("friction_events", [])]
                    patches = [GovernancePatch(**p) for p in data.get("proposed_patches", [])]
                    report = DreamReport(
                        dream_id=data.get("dream_id", ""),
                        timestamp=data.get("timestamp", ""),
                        friction_events=friction,
                        proposed_patches=patches,
                        summary=data.get("summary", ""),
                        operations_analyzed=data.get("operations_analyzed", 0),
                        friction_detected=data.get("friction_detected", 0),
                    )
                    reports.append(report)
            except (yaml.YAMLError, TypeError, KeyError):
                continue

        return reports

    def dream(self) -> DreamReport:
        """Full dream cycle: scan → synthesize → persist → return.

        This is the primary API. Call this to run the complete
        self-improvement loop.
        """
        friction = self.scan_friction()
        report = self.synthesize(friction)
        self.persist(report)
        return report


# ──────────────────────────────────────────────────────────────
# Formatting (human-readable output)
# ──────────────────────────────────────────────────────────────

_SEVERITY_ICONS = {
    SEVERITY_LOW: "○",
    SEVERITY_MEDIUM: "◑",
    SEVERITY_HIGH: "●",
    SEVERITY_CRITICAL: "◉",
}


def print_dream_report(report: DreamReport) -> None:
    """Print a formatted Dream Report to stdout."""
    print()
    print("  ╔══════════════════════════════════════════════════════════╗")
    print("  ║           ANTIGRAVITY OS — DREAM REPORT                 ║")
    print("  ╚══════════════════════════════════════════════════════════╝")
    print()
    print(f"  Dream ID:   {report.dream_id}")
    print(f"  Timestamp:  {report.timestamp}")
    print(f"  Analyzed:   {report.operations_analyzed} operations")
    print(f"  Friction:   {report.friction_detected} events detected")
    print()

    if report.friction_events:
        print("  ── Friction Events ──────────────────────────────────────")
        print()
        for i, event in enumerate(report.friction_events, 1):
            icon = _SEVERITY_ICONS.get(event.severity, "?")
            print(f"  {icon} [{event.severity}] {event.archetype}")
            print(f"    Operation: {event.operation}")
            print(f"    Diagnosis: {event.diagnosis}")
            print()
    else:
        print("  ✓ No friction detected. All operations nominal.")
        print()

    if report.proposed_patches:
        print("  ── Proposed Governance Patches ──────────────────────────")
        print()
        for i, patch in enumerate(report.proposed_patches, 1):
            print(f"  Patch {i}: [{patch.patch_type}]")
            print(f"    Target:      {patch.target}")
            print(f"    Description: {patch.description}")
            if patch.yaml_content:
                print("    Content:")
                for line in patch.yaml_content.strip().splitlines():
                    print(f"      {line}")
            print()

    print("  ── Summary ─────────────────────────────────────────────")
    print()
    # Word-wrap the summary at ~60 chars
    words = report.summary.split()
    line = "  "
    for word in words:
        if len(line) + len(word) + 1 > 70:
            print(line)
            line = "  " + word
        else:
            line += " " + word if line.strip() else "  " + word
    if line.strip():
        print(line)
    print()
    print("  ════════════════════════════════════════════════════════")
    print()
