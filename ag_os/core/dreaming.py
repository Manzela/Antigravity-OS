"""
Dreaming Module — The self-improvement loop for AI agents.

Analyzes Flight Recorder telemetry for friction patterns (loops,
rollbacks, budget failures) and synthesizes Dream Reports with
proposed governance patches. Persists learnings as long-term
memory in ~/.antigravity/dreams/.

This module is model-agnostic and has zero LLM dependencies.
Any AI agent that reads the output gains self-improvement.
"""

import contextlib
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

# Success archetypes — inverse anomaly detection
CLEAN_COMPLETION = "CLEAN_COMPLETION"
FAST_COMPLETION = "FAST_COMPLETION"
FIRST_ATTEMPT_SUCCESS = "FIRST_ATTEMPT_SUCCESS"

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
class SuccessPattern:
    """A detected success pattern from execution history."""

    operation: str
    archetype: str
    diagnosis: str
    evidence: dict[str, Any] = field(default_factory=dict)


@dataclass
class DreamReport:
    """A complete Dream Report — the output of one dream cycle."""

    dream_id: str
    timestamp: str
    friction_events: list[FrictionEvent] = field(default_factory=list)
    proposed_patches: list[GovernancePatch] = field(default_factory=list)
    success_patterns: list[SuccessPattern] = field(default_factory=list)
    summary: str = ""
    operations_analyzed: int = 0
    friction_detected: int = 0
    successes_detected: int = 0


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

        for _key, raw_value in rows:
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
            # Operation has more than 2x max_loop_count transitions
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
                            f"(2x max_loop_count={self._max_loops}). "
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

    def scan_success(self) -> list["SuccessPattern"]:
        """Scan the Flight Recorder for success patterns.

        Identifies operations that completed cleanly, quickly, or on the
        first attempt. Used to extract positive baselines for governance
        tuning — the inverse of friction scanning.
        """
        operations = self._query_all_flight_records()
        successes: list[SuccessPattern] = []

        # Compute median transition count for FAST_COMPLETION detection
        completed_counts = []
        for records in operations.values():
            states = [r.get("state", "") for r in records]
            if "COMPLETE" in states:
                completed_counts.append(len(records))
        if completed_counts:
            median_count = sorted(completed_counts)[len(completed_counts) // 2]
        else:
            median_count = 5

        linear_path = ["PLANNING", "PLAN_APPROVED", "BUILDING", "VERIFYING", "COMPLETE"]

        for op_name, records in operations.items():
            if not records:
                continue

            states = [r.get("state", "") for r in records]
            transition_count = len(records)

            if "COMPLETE" not in states:
                continue

            has_rollback = "ROLLED_BACK" in states
            has_blocked = "BLOCKED" in states

            # CLEAN_COMPLETION: reached COMPLETE with 0 rollbacks, 0 BLOCKED
            if not has_rollback and not has_blocked:
                successes.append(
                    SuccessPattern(
                        operation=op_name,
                        archetype=CLEAN_COMPLETION,
                        diagnosis=(
                            f"Operation '{op_name}' completed cleanly with "
                            f"{transition_count} transitions, zero rollbacks, "
                            f"and zero blocked states."
                        ),
                        evidence={
                            "transition_count": transition_count,
                            "states": states,
                        },
                    )
                )

            # FAST_COMPLETION: transitions <= median across all operations
            if transition_count <= median_count and not has_rollback:
                successes.append(
                    SuccessPattern(
                        operation=op_name,
                        archetype=FAST_COMPLETION,
                        diagnosis=(
                            f"Operation '{op_name}' completed in {transition_count} "
                            f"transitions (median: {median_count}). "
                            f"Below-median execution indicates efficient workflow."
                        ),
                        evidence={
                            "transition_count": transition_count,
                            "median": median_count,
                        },
                    )
                )

            # FIRST_ATTEMPT_SUCCESS: linear path with no backward transitions
            if states == linear_path:
                successes.append(
                    SuccessPattern(
                        operation=op_name,
                        archetype=FIRST_ATTEMPT_SUCCESS,
                        diagnosis=(
                            f"Operation '{op_name}' followed the ideal linear path "
                            f"(PLANNING -> COMPLETE) with no deviations or retries."
                        ),
                        evidence={"states": states},
                    )
                )

        return successes

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

        # ── Scan for success patterns ──
        success_patterns = self.scan_success()

        # ── Build summary ──
        archetype_counts: dict[str, int] = {}
        for e in friction_events:
            archetype_counts[e.archetype] = archetype_counts.get(e.archetype, 0) + 1

        parts = []
        parts.append(f"Dream cycle analyzed {len(operations)} operations.")

        if friction_events:
            archetype_summary = ", ".join(
                f"{count} {archetype.lower().replace('_', ' ')}"
                for archetype, count in sorted(archetype_counts.items())
            )
            parts.append(
                f"Detected {len(friction_events)} friction events: {archetype_summary}. "
                f"Generated {len(patches)} governance patches for self-improvement."
            )

        if success_patterns:
            parts.append(
                f"Identified {len(success_patterns)} success patterns from nominal operations."
            )

        if not friction_events and not success_patterns:
            parts.append(
                "No friction detected — the governance kernel is operating within "
                "nominal parameters. No patches proposed."
            )

        summary = " ".join(parts)

        return DreamReport(
            dream_id=dream_id,
            timestamp=now.isoformat(),
            friction_events=friction_events,
            proposed_patches=patches,
            success_patterns=success_patterns,
            summary=summary,
            operations_analyzed=len(operations),
            friction_detected=len(friction_events),
            successes_detected=len(success_patterns),
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
                with open(path, encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                if data:
                    # Reconstruct nested dataclasses
                    friction = [FrictionEvent(**e) for e in data.get("friction_events", [])]
                    patches = [GovernancePatch(**p) for p in data.get("proposed_patches", [])]
                    success = [SuccessPattern(**s) for s in data.get("success_patterns", [])]
                    report = DreamReport(
                        dream_id=data.get("dream_id", ""),
                        timestamp=data.get("timestamp", ""),
                        friction_events=friction,
                        proposed_patches=patches,
                        success_patterns=success,
                        summary=data.get("summary", ""),
                        operations_analyzed=data.get("operations_analyzed", 0),
                        friction_detected=data.get("friction_detected", 0),
                        successes_detected=data.get("successes_detected", 0),
                    )
                    reports.append(report)
            except (yaml.YAMLError, TypeError, KeyError):
                continue

        return reports

    def prune(self) -> dict:
        """Tiered memory consolidation for the dream archive.

        1. Delete reports older than retention_days.
        2. If still over retention_max_count, delete oldest FIFO.
        3. Before deletion: extract core statistics and append to
           ~/.antigravity/dreams/archive/historical_aggregates.jsonl

        Returns {deleted_count, consolidated_count, remaining_count}.
        """
        dreaming_cfg = self._config.get("dreaming", {})
        retention_days = dreaming_cfg.get("retention_days", 90)
        max_count = dreaming_cfg.get("retention_max_count", 100)

        if not _DREAMS_DIR.is_dir():
            return {"deleted_count": 0, "consolidated_count": 0, "remaining_count": 0}

        files = sorted(_DREAMS_DIR.glob("dream-*.yaml"))
        now = datetime.now(timezone.utc)
        to_delete: list[Path] = []
        consolidated = 0

        archive_dir = _DREAMS_DIR / "archive"
        archive_dir.mkdir(parents=True, exist_ok=True)
        aggregates_path = archive_dir / "historical_aggregates.jsonl"

        # Phase 1: TTL-based expiry
        for path in files:
            try:
                with open(path, encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                ts_str = data.get("timestamp", "") if data else ""
                if ts_str:
                    report_time = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                    age_days = (now - report_time).days
                    if age_days > retention_days:
                        # Rollup before deletion
                        self._write_rollup(aggregates_path, data)
                        to_delete.append(path)
                        consolidated += 1
            except (yaml.YAMLError, ValueError, OSError):
                continue

        # Phase 2: Count-based eviction (oldest first)
        remaining_files = [f for f in files if f not in to_delete]
        if len(remaining_files) > max_count:
            excess = remaining_files[: len(remaining_files) - max_count]
            for path in excess:
                try:
                    with open(path, encoding="utf-8") as f:
                        data = yaml.safe_load(f)
                    if data:
                        self._write_rollup(aggregates_path, data)
                        consolidated += 1
                except (yaml.YAMLError, OSError):
                    pass
                to_delete.append(path)

        # Execute deletions
        for path in to_delete:
            with contextlib.suppress(OSError):
                path.unlink()

        remaining = len(list(_DREAMS_DIR.glob("dream-*.yaml")))
        return {
            "deleted_count": len(to_delete),
            "consolidated_count": consolidated,
            "remaining_count": remaining,
        }

    @staticmethod
    def _write_rollup(path: Path, data: dict) -> None:
        """Append a compact statistical rollup to the aggregates JSONL file."""
        rollup = {
            "dream_id": data.get("dream_id", ""),
            "timestamp": data.get("timestamp", ""),
            "operations_analyzed": data.get("operations_analyzed", 0),
            "friction_detected": data.get("friction_detected", 0),
            "successes_detected": data.get("successes_detected", 0),
            "patch_count": len(data.get("proposed_patches", [])),
            "archetypes": list({e.get("archetype", "") for e in data.get("friction_events", [])}),
        }
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rollup, default=str) + "\n")

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


def format_dream_report(report: DreamReport) -> str:
    """Render a formatted Dream Report as a string.

    Side-effect-free primitive; safe for MCP / log handlers / JSON
    response bodies. The CLI wrapper :func:`print_dream_report` is the
    only thing that should write to stdout.
    """
    lines: list[str] = [
        "",
        "  ╔══════════════════════════════════════════════════════════╗",
        "  ║           ANTIGRAVITY OS — DREAM REPORT                 ║",
        "  ╚══════════════════════════════════════════════════════════╝",
        "",
        f"  Dream ID:   {report.dream_id}",
        f"  Timestamp:  {report.timestamp}",
        f"  Analyzed:   {report.operations_analyzed} operations",
        f"  Friction:   {report.friction_detected} events detected",
        f"  Successes:  {report.successes_detected} patterns identified",
        "",
    ]

    if report.friction_events:
        lines.extend(["  -- Friction Events ------------------------------------------", ""])
        for event in report.friction_events:
            icon = _SEVERITY_ICONS.get(event.severity, "?")
            lines.extend(
                [
                    f"  {icon} [{event.severity}] {event.archetype}",
                    f"    Operation: {event.operation}",
                    f"    Diagnosis: {event.diagnosis}",
                    "",
                ]
            )
    else:
        lines.extend(["  No friction detected. All operations nominal.", ""])

    if report.success_patterns:
        lines.extend(["  -- Success Patterns -----------------------------------------", ""])
        for pattern in report.success_patterns:
            lines.extend(
                [
                    f"  + [{pattern.archetype}]",
                    f"    Operation: {pattern.operation}",
                    f"    Diagnosis: {pattern.diagnosis}",
                    "",
                ]
            )

    if report.proposed_patches:
        lines.extend(["  ── Proposed Governance Patches ──────────────────────────", ""])
        for i, patch in enumerate(report.proposed_patches, 1):
            lines.extend(
                [
                    f"  Patch {i}: [{patch.patch_type}]",
                    f"    Target:      {patch.target}",
                    f"    Description: {patch.description}",
                ]
            )
            if patch.yaml_content:
                lines.append("    Content:")
                lines.extend(f"      {ln}" for ln in patch.yaml_content.strip().splitlines())
            lines.append("")

    lines.extend(["  ── Summary ─────────────────────────────────────────────", ""])
    # Word-wrap the summary using stdlib textwrap rather than the
    # hand-rolled loop that lived here before.
    import textwrap

    wrapped = textwrap.fill(
        report.summary,
        width=70,
        initial_indent="  ",
        subsequent_indent="  ",
    )
    if wrapped:
        lines.append(wrapped)
    lines.extend(["", "  ════════════════════════════════════════════════════════", ""])

    return "\n".join(lines)


def print_dream_report(report: DreamReport) -> None:
    """Print the formatted Dream Report to stdout (CLI use only)."""
    print(format_dream_report(report))
