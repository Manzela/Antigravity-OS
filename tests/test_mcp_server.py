"""Unit tests for the Antigravity OS MCP server tools.

Tests each MCP tool function directly (without the MCP transport layer)
to verify they correctly delegate to the governance kernel.
"""

from ag_os.mcp.server import (
    check_solvency,
    evaluate_policy,
    get_history,
    get_status,
    transition_state,
)


class TestCheckSolvency:
    """Tests for the check_solvency MCP tool."""

    def test_solvent_with_defaults(self):
        result = check_solvency(units=1.0, tier="standard_cpu")
        assert result["is_solvent"] is True
        assert result["current_spend"] >= 0
        assert result["projected_cost"] > 0
        assert result["monthly_cap"] > 0
        assert result["remaining_budget"] >= 0

    def test_insolvent_with_excessive_units(self):
        result = check_solvency(units=10000.0, tier="gpu_large")
        assert result["is_solvent"] is False

    def test_returns_dict_with_required_keys(self):
        result = check_solvency()
        assert isinstance(result, dict)
        required_keys = {
            "is_solvent",
            "current_spend",
            "projected_cost",
            "monthly_cap",
            "remaining_budget",
        }
        assert required_keys <= set(result.keys())


class TestTransitionState:
    """Tests for the transition_state MCP tool."""

    def test_valid_transition(self):
        import uuid

        op = f"mcp-test-{uuid.uuid4().hex[:8]}"
        result = transition_state(
            operation=op,
            target_state="PLANNING",
        )
        assert result["status"] == "ok"
        assert result["current_state"] == "PLANNING"

    def test_invalid_transition_returns_error(self):
        import uuid

        op = f"mcp-test-{uuid.uuid4().hex[:8]}"
        result = transition_state(
            operation=op,
            target_state="COMPLETE",
        )
        assert result["status"] == "error"
        assert "error" in result

    def test_transition_with_metadata(self):
        import uuid

        op = f"mcp-test-{uuid.uuid4().hex[:8]}"
        result = transition_state(
            operation=op,
            target_state="PLANNING",
            metadata={"author": "test"},
        )
        assert result["status"] == "ok"


class TestEvaluatePolicy:
    """Tests for the evaluate_policy MCP tool."""

    def test_allowed_with_plan(self):
        result = evaluate_policy(
            requires_plan=True,
            has_plan=True,
            state="PLANNING",
        )
        assert result["allowed"] is True
        assert result["policy_name"] == "governance"
        assert len(result["violations"]) == 0

    def test_blocked_without_plan(self):
        result = evaluate_policy(
            requires_plan=True,
            has_plan=False,
            state="IDLE",
        )
        assert result["allowed"] is False
        assert len(result["violations"]) > 0

    def test_violations_are_strings(self):
        result = evaluate_policy(
            requires_plan=True,
            has_plan=False,
            state="IDLE",
        )
        for v in result["violations"]:
            assert isinstance(v, str)


class TestGetStatus:
    """Tests for the get_status MCP tool."""

    def test_returns_config_keys(self):
        result = get_status()
        assert "monthly_cap" in result
        assert "max_loop_count" in result
        assert "providers" in result
        assert "ci_platform" in result

    def test_providers_is_dict(self):
        result = get_status()
        assert isinstance(result["providers"], dict)


class TestGetHistory:
    """Tests for the get_history MCP tool."""

    def test_empty_history_for_unknown_operation(self):
        result = get_history(operation="nonexistent-op")
        assert result["record_count"] == 0
        assert result["records"] == []

    def test_history_after_transitions(self):
        import uuid

        op = f"mcp-hist-{uuid.uuid4().hex[:8]}"
        transition_state(operation=op, target_state="PLANNING")
        result = get_history(operation=op)
        assert result["record_count"] >= 1
        assert result["records"][0]["state"] == "PLANNING"
