"""Tests for the cross-repo aggregation module."""

import yaml

from ag_os.core.aggregator import (
    AggregatedDreamReport,
    SystemicPattern,
    merge_dream_dirs,
)


class TestMergeDreamDirs:
    """Validate cross-repo dream report aggregation."""

    def test_merge_empty_dirs(self, tmp_path):
        """Merging directories with no dreams returns empty report."""
        report = merge_dream_dirs([tmp_path])
        assert report.repos_analyzed == 0
        assert "No dream archives" in report.summary

    def test_merge_single_repo(self, tmp_path):
        """Single repo with dreams produces a valid report."""
        dreams_dir = tmp_path / "repo1" / ".antigravity" / "dreams"
        dreams_dir.mkdir(parents=True)

        report_data = {
            "dream_id": "dream-001",
            "timestamp": "2026-05-01T00:00:00+00:00",
            "operations_analyzed": 5,
            "friction_detected": 2,
            "successes_detected": 1,
            "friction_events": [
                {
                    "archetype": "LOOP_DETECTED",
                    "operation": "op1",
                    "severity": "HIGH",
                    "diagnosis": "Loop detected.",
                },
            ],
            "proposed_patches": [],
            "success_patterns": [],
        }
        with open(dreams_dir / "dream-001.yaml", "w") as f:
            yaml.dump(report_data, f)

        report = merge_dream_dirs([tmp_path / "repo1"])
        assert report.repos_analyzed == 1
        assert report.total_dreams_scanned == 1

    def test_systemic_pattern_detection(self, tmp_path):
        """Archetypes in >= 50% of repos are flagged as systemic."""
        for repo_name in ["repo1", "repo2", "repo3"]:
            dreams_dir = tmp_path / repo_name / ".antigravity" / "dreams"
            dreams_dir.mkdir(parents=True)

            # All repos have LOOP_DETECTED
            report_data = {
                "dream_id": f"dream-{repo_name}",
                "timestamp": "2026-05-01T00:00:00+00:00",
                "operations_analyzed": 5,
                "friction_detected": 1,
                "successes_detected": 0,
                "friction_events": [
                    {
                        "archetype": "LOOP_DETECTED",
                        "operation": "op1",
                        "severity": "HIGH",
                        "diagnosis": "Loop.",
                    },
                ],
                "proposed_patches": [],
                "success_patterns": [],
            }
            with open(dreams_dir / f"dream-{repo_name}.yaml", "w") as f:
                yaml.dump(report_data, f)

        dirs = [tmp_path / name for name in ["repo1", "repo2", "repo3"]]
        report = merge_dream_dirs(dirs)
        assert report.repos_analyzed == 3
        assert len(report.systemic_patterns) >= 1
        archetypes = [p.archetype for p in report.systemic_patterns]
        assert "LOOP_DETECTED" in archetypes


class TestDataclasses:
    """Validate aggregation dataclasses."""

    def test_systemic_pattern_creation(self):
        sp = SystemicPattern(
            archetype="LOOP_DETECTED",
            repo_count=3,
            total_repos=4,
            frequency=0.75,
        )
        assert sp.frequency == 0.75
        assert sp.affected_repos == []

    def test_aggregated_report_defaults(self):
        report = AggregatedDreamReport(report_id="test", timestamp="2026-01-01")
        assert report.repos_analyzed == 0
        assert report.systemic_patterns == []
