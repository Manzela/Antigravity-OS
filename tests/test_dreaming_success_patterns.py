"""Tests for the DreamEngine success pattern extraction and memory pruning."""

from unittest.mock import patch

from ag_os.core.dreaming import (
    CLEAN_COMPLETION,
    FIRST_ATTEMPT_SUCCESS,
    DreamEngine,
    DreamReport,
    SuccessPattern,
)


class TestScanSuccess:
    """Validate inverse anomaly detection for success patterns."""

    def _make_engine_with_records(self, operations):
        """Create a DreamEngine whose _query_all_flight_records returns operations."""
        engine = DreamEngine(config={"max_loop_count": 5, "dreaming": {}})
        with patch.object(engine, "_query_all_flight_records", return_value=operations):
            yield engine

    def test_clean_completion_detected(self):
        """Operations completing without rollbacks or blocked states are CLEAN."""
        ops = {
            "op-clean": [
                {"state": "PLANNING", "operation": "op-clean"},
                {"state": "BUILDING", "operation": "op-clean"},
                {"state": "COMPLETE", "operation": "op-clean"},
            ]
        }
        engine = DreamEngine(config={"max_loop_count": 5, "dreaming": {}})
        with patch.object(engine, "_query_all_flight_records", return_value=ops):
            results = engine.scan_success()

        archetypes = [s.archetype for s in results]
        assert CLEAN_COMPLETION in archetypes

    def test_first_attempt_success_detected(self):
        """Operations following the exact linear path are FIRST_ATTEMPT_SUCCESS."""
        linear = ["PLANNING", "PLAN_APPROVED", "BUILDING", "VERIFYING", "COMPLETE"]
        ops = {"op-linear": [{"state": s, "operation": "op-linear"} for s in linear]}
        engine = DreamEngine(config={"max_loop_count": 5, "dreaming": {}})
        with patch.object(engine, "_query_all_flight_records", return_value=ops):
            results = engine.scan_success()

        archetypes = [s.archetype for s in results]
        assert FIRST_ATTEMPT_SUCCESS in archetypes

    def test_no_success_for_incomplete_operations(self):
        """Operations that never reach COMPLETE should not produce success patterns."""
        ops = {
            "op-incomplete": [
                {"state": "PLANNING", "operation": "op-incomplete"},
                {"state": "BLOCKED", "operation": "op-incomplete"},
            ]
        }
        engine = DreamEngine(config={"max_loop_count": 5, "dreaming": {}})
        with patch.object(engine, "_query_all_flight_records", return_value=ops):
            results = engine.scan_success()

        assert len(results) == 0

    def test_no_success_for_rollback_operations(self):
        """Operations with rollbacks should not be CLEAN_COMPLETION."""
        ops = {
            "op-rollback": [
                {"state": "PLANNING", "operation": "op-rollback"},
                {"state": "ROLLED_BACK", "operation": "op-rollback"},
                {"state": "BUILDING", "operation": "op-rollback"},
                {"state": "COMPLETE", "operation": "op-rollback"},
            ]
        }
        engine = DreamEngine(config={"max_loop_count": 5, "dreaming": {}})
        with patch.object(engine, "_query_all_flight_records", return_value=ops):
            results = engine.scan_success()

        archetypes = [s.archetype for s in results]
        assert CLEAN_COMPLETION not in archetypes


class TestSuccessPatternDataclass:
    """Validate SuccessPattern dataclass."""

    def test_creation(self):
        sp = SuccessPattern(
            operation="test-op",
            archetype=CLEAN_COMPLETION,
            diagnosis="Clean completion detected.",
        )
        assert sp.operation == "test-op"
        assert sp.archetype == CLEAN_COMPLETION
        assert sp.evidence == {}


class TestDreamReportSuccessFields:
    """Validate DreamReport includes success fields."""

    def test_default_success_fields(self):
        report = DreamReport(dream_id="test", timestamp="2026-01-01")
        assert report.success_patterns == []
        assert report.successes_detected == 0


class TestPrune:
    """Validate tiered memory consolidation."""

    def test_prune_empty_directory(self, tmp_path):
        """Pruning a non-existent directory returns zeros."""
        engine = DreamEngine(
            config={"dreaming": {"retention_days": 90, "retention_max_count": 100}}
        )
        with patch("ag_os.core.dreaming._DREAMS_DIR", tmp_path / "nonexistent"):
            result = engine.prune()

        assert result["deleted_count"] == 0
        assert result["consolidated_count"] == 0
        assert result["remaining_count"] == 0

    def test_prune_respects_max_count(self, tmp_path):
        """When count exceeds max, oldest files are deleted."""
        import yaml

        dreams_dir = tmp_path / "dreams"
        dreams_dir.mkdir()

        # Create 5 reports
        for i in range(5):
            report = {
                "dream_id": f"dream-{i:04d}",
                "timestamp": f"2026-05-0{i + 1}T00:00:00+00:00",
                "operations_analyzed": 10,
                "friction_detected": i,
                "successes_detected": 0,
                "friction_events": [],
                "proposed_patches": [],
                "success_patterns": [],
            }
            path = dreams_dir / f"dream-{i:04d}.yaml"
            with open(path, "w") as f:
                yaml.dump(report, f)

        engine = DreamEngine(
            config={"dreaming": {"retention_days": 9999, "retention_max_count": 3}}
        )
        with patch("ag_os.core.dreaming._DREAMS_DIR", dreams_dir):
            result = engine.prune()

        assert result["deleted_count"] == 2
        assert result["remaining_count"] == 3
        # Check archive was created
        archive = dreams_dir / "archive" / "historical_aggregates.jsonl"
        assert archive.is_file()
