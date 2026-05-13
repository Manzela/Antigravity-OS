"""Format-helper tests (P0-7).

The MCP stdio transport speaks JSON-RPC on stdout. Any module that the
MCP server imports must avoid writing to stdout as a side-effect.
``format_*_report`` are the safe primitives — pure functions that return
strings — and these tests pin both the contract (returns a non-empty
str) and the absence of stdout side-effects.
"""

from __future__ import annotations


def _make_solvency_result(*, is_solvent: bool):
    from ag_os.providers.cost import SolvencyResult

    return SolvencyResult(
        is_solvent=is_solvent,
        current_spend=4.0,
        projected_cost=1.5,
        monthly_cap=15.0,
        margin=10.0 if is_solvent else -5.0,
    )


def _make_policy_result(*, allowed: bool):
    from ag_os.providers.policy import PolicyResult

    return PolicyResult(
        allowed=allowed,
        violations=[] if allowed else ["Rule 00: missing plan"],
        policy_name="builtin",
    )


class TestFormatSolvencyReport:
    """cost_guard.format_solvency_report (P0-7)."""

    def test_returns_str_no_stdout(self, capsys):
        from ag_os.core.cost_guard import format_solvency_report

        result = _make_solvency_result(is_solvent=True)
        out = format_solvency_report(result)
        captured = capsys.readouterr()
        assert isinstance(out, str)
        assert out.strip(), "format helper must return non-empty content"
        assert captured.out == "", "format helper must not write to stdout"
        assert captured.err == "", "format helper must not write to stderr"

    def test_solvent_label(self):
        from ag_os.core.cost_guard import format_solvency_report

        out = format_solvency_report(_make_solvency_result(is_solvent=True))
        assert "SOLVENT" in out
        assert "[OK]" in out

    def test_insolvent_includes_overage(self):
        from ag_os.core.cost_guard import format_solvency_report

        out = format_solvency_report(_make_solvency_result(is_solvent=False))
        assert "INSOLVENT" in out
        assert "[BLOCKED]" in out
        assert "Budget exceeded" in out


class TestFormatPolicyReport:
    """rules_engine.format_policy_report (P0-7)."""

    def test_returns_str_no_stdout(self, capsys):
        from ag_os.core.rules_engine import format_policy_report

        out = format_policy_report(_make_policy_result(allowed=True))
        captured = capsys.readouterr()
        assert isinstance(out, str)
        assert out.strip()
        assert captured.out == ""
        assert captured.err == ""

    def test_violations_listed(self):
        from ag_os.core.rules_engine import format_policy_report

        out = format_policy_report(_make_policy_result(allowed=False))
        assert "BLOCKED" in out
        assert "Rule 00: missing plan" in out


class TestFormatDreamReport:
    """dreaming.format_dream_report (P0-7)."""

    def test_returns_str_no_stdout(self, capsys):
        from ag_os.core.dreaming import DreamReport, format_dream_report

        report = DreamReport(
            dream_id="dream-test-1",
            timestamp="2026-05-12T12:00:00Z",
            operations_analyzed=10,
            friction_detected=0,
            successes_detected=0,
            friction_events=[],
            success_patterns=[],
            proposed_patches=[],
            summary="Nominal cycle, no friction.",
        )
        out = format_dream_report(report)
        captured = capsys.readouterr()
        assert isinstance(out, str)
        assert "DREAM REPORT" in out
        assert "dream-test-1" in out
        assert captured.out == ""
        assert captured.err == ""


class TestFormatAggregatedReport:
    """aggregator.format_aggregated_report (P0-7)."""

    def test_returns_str_no_stdout(self, capsys):
        from ag_os.core.aggregator import AggregatedDreamReport, format_aggregated_report

        report = AggregatedDreamReport(
            report_id="agg-test-1",
            timestamp="2026-05-12T12:00:00Z",
            repos_analyzed=3,
            total_dreams_scanned=12,
            systemic_patterns=[],
            per_repo_summary={},
            summary="No systemic patterns across the fleet.",
        )
        out = format_aggregated_report(report)
        captured = capsys.readouterr()
        assert isinstance(out, str)
        assert "AGGREGATED DREAM REPORT" in out
        assert "agg-test-1" in out
        assert captured.out == ""
        assert captured.err == ""


class TestPrintWrappersStillWork:
    """Backward compat: the print_*_report wrappers still write to stdout."""

    def test_print_solvency_report_writes_stdout(self, capsys):
        from ag_os.core.cost_guard import print_solvency_report

        print_solvency_report(_make_solvency_result(is_solvent=True))
        captured = capsys.readouterr()
        assert "SOLVENT" in captured.out

    def test_print_policy_report_writes_stdout(self, capsys):
        from ag_os.core.rules_engine import print_policy_report

        print_policy_report(_make_policy_result(allowed=True))
        captured = capsys.readouterr()
        assert "ALLOWED" in captured.out
