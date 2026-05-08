"""Unit tests for the Antigravity OS Dreaming Module.

Tests the full dream cycle: friction scanning, report synthesis,
YAML persistence, and long-term memory recall. Uses isolated
SQLite databases and temporary directories for determinism.
"""

import json
import tempfile
import uuid
from pathlib import Path
from unittest.mock import patch

import yaml

from ag_os.core.dreaming import (
    BLOCKED_TERMINAL,
    BUDGET_EXCEEDED,
    LOOP_DETECTED,
    ROLLBACK_CYCLE,
    DreamEngine,
    DreamReport,
    FrictionEvent,
    GovernancePatch,
    print_dream_report,
)


def _create_engine_with_friction(*, loops=0, rollbacks=0, blocked=False, budget=False):
    """Helper: create a DreamEngine and seed it with known friction patterns."""
    config = {
        "max_loop_count": 5,
        "providers": {"state": "sqlite", "telemetry": "console", "policy": "builtin"},
    }
    engine = DreamEngine(config=config)
    state = engine._get_state_provider()

    op_id = f"test-{uuid.uuid4().hex[:8]}"

    # Seed flight records directly into the state store
    records = []
    timestamp_base = "2026-05-07T20:00:00"

    # Generate loop transitions: PLANNING → PLAN_APPROVED → BUILDING → VERIFYING → ROLLED_BACK
    for i in range(loops):
        cycle_states = [
            ("IDLE" if i == 0 else "ROLLED_BACK", "PLANNING"),
            ("PLANNING", "PLAN_APPROVED"),
            ("PLAN_APPROVED", "BUILDING"),
            ("BUILDING", "VERIFYING"),
            ("VERIFYING", "ROLLED_BACK"),
        ]
        for j, (prev, cur) in enumerate(cycle_states):
            ts = f"{timestamp_base}.{i:02d}{j:02d}00Z"
            record = {
                "trace_id": uuid.uuid4().hex[:12],
                "operation": op_id,
                "state": cur,
                "previous_state": prev if not (i == 0 and j == 0) else "IDLE",
                "timestamp": ts,
                "metadata": {},
                "error": "",
            }
            if cur == "ROLLED_BACK":
                record["error"] = "Test failure"
            records.append((ts, record))

    if blocked:
        ts = f"{timestamp_base}.990000Z"
        record = {
            "trace_id": uuid.uuid4().hex[:12],
            "operation": op_id,
            "state": "BLOCKED",
            "previous_state": "BUILDING",
            "timestamp": ts,
            "metadata": {},
            "error": "Terminal failure",
        }
        records.append((ts, record))

    if budget:
        ts = f"{timestamp_base}.999000Z"
        record = {
            "trace_id": uuid.uuid4().hex[:12],
            "operation": op_id,
            "state": "BLOCKED",
            "previous_state": "PLANNING",
            "timestamp": ts,
            "metadata": {"solvency_failed": True},
            "error": "Budget exceeded: insolvent",
        }
        records.append((ts, record))

    # Write all records to state store
    for ts, record in records:
        key = f"flight:{op_id}:record:{ts}"
        state.set(key, json.dumps(record))

    return engine, op_id


class TestFrictionScan:
    """Tests for DreamEngine.scan_friction() detection heuristics."""

    def test_detects_loop(self):
        """Operations with >2× max_loop_count transitions are LOOP_DETECTED."""
        engine, op_id = _create_engine_with_friction(loops=3)
        friction = engine.scan_friction()

        loop_events = [e for e in friction if e.archetype == LOOP_DETECTED and e.operation == op_id]
        assert len(loop_events) >= 1
        assert loop_events[0].severity == "HIGH"

    def test_detects_rollback_cycle(self):
        """Operations with ≥2 ROLLED_BACK visits are ROLLBACK_CYCLE."""
        engine, op_id = _create_engine_with_friction(rollbacks=0, loops=3)
        friction = engine.scan_friction()

        rollback_events = [
            e for e in friction if e.archetype == ROLLBACK_CYCLE and e.operation == op_id
        ]
        assert len(rollback_events) >= 1
        assert rollback_events[0].severity == "HIGH"

    def test_detects_blocked_terminal(self):
        """Operations ending in BLOCKED are BLOCKED_TERMINAL."""
        engine, op_id = _create_engine_with_friction(blocked=True)
        friction = engine.scan_friction()

        blocked_events = [
            e for e in friction if e.archetype == BLOCKED_TERMINAL and e.operation == op_id
        ]
        assert len(blocked_events) >= 1
        assert blocked_events[0].severity == "MEDIUM"

    def test_detects_budget_exceeded(self):
        """Operations with solvency failure metadata are BUDGET_EXCEEDED."""
        engine, op_id = _create_engine_with_friction(budget=True)
        friction = engine.scan_friction()

        budget_events = [
            e for e in friction if e.archetype == BUDGET_EXCEEDED and e.operation == op_id
        ]
        assert len(budget_events) >= 1
        assert budget_events[0].severity == "CRITICAL"

    def test_no_friction_for_clean_operations(self):
        """Clean operations with few transitions produce no friction."""
        config = {
            "max_loop_count": 5,
            "providers": {"state": "sqlite", "telemetry": "console", "policy": "builtin"},
        }
        engine = DreamEngine(config=config)
        state = engine._get_state_provider()

        op_id = f"clean-{uuid.uuid4().hex[:8]}"
        # A clean 5-transition operation that reaches COMPLETE
        states = ["PLANNING", "PLAN_APPROVED", "BUILDING", "VERIFYING", "COMPLETE"]
        for i, s in enumerate(states):
            ts = f"2026-05-07T21:00:00.{i:06d}Z"
            record = {
                "trace_id": uuid.uuid4().hex[:12],
                "operation": op_id,
                "state": s,
                "previous_state": states[i - 1] if i > 0 else "IDLE",
                "timestamp": ts,
                "metadata": {},
                "error": "",
            }
            state.set(f"flight:{op_id}:record:{ts}", json.dumps(record))

        friction = engine.scan_friction()
        op_friction = [e for e in friction if e.operation == op_id]
        assert len(op_friction) == 0


class TestDreamSynthesis:
    """Tests for DreamEngine.synthesize() report generation."""

    def test_synthesize_produces_report(self):
        """Synthesize returns a valid DreamReport with ID and timestamp."""
        engine, _ = _create_engine_with_friction(loops=3, blocked=True)
        friction = engine.scan_friction()
        report = engine.synthesize(friction)

        assert isinstance(report, DreamReport)
        assert report.dream_id.startswith("dream-")
        assert report.timestamp
        assert report.operations_analyzed >= 0

    def test_synthesize_generates_patches_for_loops(self):
        """Loop friction should generate a THRESHOLD_ADJUSTMENT patch."""
        engine, _ = _create_engine_with_friction(loops=3)
        friction = engine.scan_friction()
        report = engine.synthesize(friction)

        threshold_patches = [
            p for p in report.proposed_patches if p.patch_type == "THRESHOLD_ADJUSTMENT"
        ]
        assert len(threshold_patches) >= 1
        assert "max_loop_count" in threshold_patches[0].target

    def test_synthesize_generates_patches_for_rollbacks(self):
        """Rollback friction should generate a NEW_RULE patch."""
        engine, _ = _create_engine_with_friction(loops=3)
        friction = engine.scan_friction()
        report = engine.synthesize(friction)

        rule_patches = [p for p in report.proposed_patches if p.patch_type == "NEW_RULE"]
        assert len(rule_patches) >= 1

    def test_synthesize_with_no_friction(self):
        """No friction produces a report with empty patches and clean summary."""
        config = {
            "max_loop_count": 5,
            "providers": {"state": "sqlite", "telemetry": "console", "policy": "builtin"},
        }
        engine = DreamEngine(config=config)
        report = engine.synthesize([])

        assert report.friction_detected == 0
        assert len(report.proposed_patches) == 0
        # Summary should mention the analysis — either no friction or success patterns
        assert "operations" in report.summary.lower()

    def test_summary_is_human_readable(self):
        """Summary should be a coherent sentence, not raw data."""
        engine, _ = _create_engine_with_friction(loops=3, budget=True)
        friction = engine.scan_friction()
        report = engine.synthesize(friction)

        assert len(report.summary) > 50
        assert "friction" in report.summary.lower() or "operations" in report.summary.lower()


class TestDreamPersistence:
    """Tests for DreamEngine.persist() and recall()."""

    def test_persist_writes_yaml_file(self):
        """persist() should write a valid YAML file to the dreams directory."""
        engine, _ = _create_engine_with_friction(loops=3)
        friction = engine.scan_friction()
        report = engine.synthesize(friction)

        with tempfile.TemporaryDirectory() as tmpdir:
            dreams_dir = Path(tmpdir) / "dreams"
            with patch("ag_os.core.dreaming._DREAMS_DIR", dreams_dir):
                path = engine.persist(report)

            assert path.exists()
            assert path.suffix == ".yaml"

            # Verify it's valid YAML
            with open(path) as f:
                data = yaml.safe_load(f)
            assert data["dream_id"] == report.dream_id
            assert data["friction_detected"] == report.friction_detected

    def test_recall_returns_persisted_reports(self):
        """recall() should return previously persisted reports."""
        engine, _ = _create_engine_with_friction(loops=3)
        friction = engine.scan_friction()
        report = engine.synthesize(friction)

        with tempfile.TemporaryDirectory() as tmpdir:
            dreams_dir = Path(tmpdir) / "dreams"
            with patch("ag_os.core.dreaming._DREAMS_DIR", dreams_dir):
                engine.persist(report)
                recalled = engine.recall(n=5)

            assert len(recalled) >= 1
            assert recalled[0].dream_id == report.dream_id

    def test_recall_returns_empty_for_no_reports(self):
        """recall() returns empty list when no dreams directory exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            nonexistent = Path(tmpdir) / "nonexistent"
            with patch("ag_os.core.dreaming._DREAMS_DIR", nonexistent):
                engine = DreamEngine()
                recalled = engine.recall(n=5)

            assert recalled == []


class TestFullDreamCycle:
    """End-to-end tests for the complete dream() pipeline."""

    def test_full_dream_cycle(self):
        """dream() should scan, synthesize, persist, and return a report."""
        engine, _ = _create_engine_with_friction(loops=3, blocked=True)

        with tempfile.TemporaryDirectory() as tmpdir:
            dreams_dir = Path(tmpdir) / "dreams"
            with patch("ag_os.core.dreaming._DREAMS_DIR", dreams_dir):
                report = engine.dream()

            assert isinstance(report, DreamReport)
            assert report.friction_detected > 0
            assert len(report.proposed_patches) > 0

            # Verify file was persisted
            files = list(dreams_dir.glob("dream-*.yaml"))
            assert len(files) == 1

    def test_dream_report_print_does_not_crash(self, capsys):
        """print_dream_report should produce output without exceptions."""
        engine, _ = _create_engine_with_friction(loops=3, budget=True, blocked=True)

        with tempfile.TemporaryDirectory() as tmpdir:
            dreams_dir = Path(tmpdir) / "dreams"
            with patch("ag_os.core.dreaming._DREAMS_DIR", dreams_dir):
                report = engine.dream()

        print_dream_report(report)
        captured = capsys.readouterr()
        assert "DREAM REPORT" in captured.out
        assert report.dream_id in captured.out


class TestMCPDreamTools:
    """Tests for the dream and recall_dreams MCP tools."""

    def test_mcp_dream_tool(self):
        """The dream MCP tool should return a valid dict."""
        from ag_os.mcp.server import dream as mcp_dream

        with tempfile.TemporaryDirectory() as tmpdir:
            dreams_dir = Path(tmpdir) / "dreams"
            with patch("ag_os.core.dreaming._DREAMS_DIR", dreams_dir):
                result = mcp_dream(dry_run=True)

        assert isinstance(result, dict)
        assert "dream_id" in result
        assert "summary" in result
        assert "friction_events" in result
        assert "proposed_patches" in result

    def test_mcp_recall_dreams_tool(self):
        """The recall_dreams MCP tool should return a valid dict."""
        from ag_os.mcp.server import recall_dreams as mcp_recall

        with tempfile.TemporaryDirectory() as tmpdir:
            dreams_dir = Path(tmpdir) / "dreams"
            with patch("ag_os.core.dreaming._DREAMS_DIR", dreams_dir):
                result = mcp_recall(n=5)

        assert isinstance(result, dict)
        assert "count" in result
        assert "reports" in result
        assert result["count"] == 0  # No dreams persisted yet


class TestDataclasses:
    """Tests for the Dreaming Module dataclasses."""

    def test_friction_event_creation(self):
        event = FrictionEvent(
            operation="test-op",
            archetype=LOOP_DETECTED,
            severity="HIGH",
            diagnosis="Test diagnosis",
            evidence={"key": "value"},
        )
        assert event.operation == "test-op"
        assert event.archetype == LOOP_DETECTED

    def test_governance_patch_creation(self):
        patch = GovernancePatch(
            patch_type="NEW_RULE",
            target=".agent/rules/test.md",
            description="Test patch",
            yaml_content="test: true",
        )
        assert patch.patch_type == "NEW_RULE"
        assert patch.yaml_content == "test: true"

    def test_dream_report_defaults(self):
        report = DreamReport(
            dream_id="test-001",
            timestamp="2026-05-07T00:00:00Z",
        )
        assert report.friction_events == []
        assert report.proposed_patches == []
        assert report.summary == ""
        assert report.operations_analyzed == 0
