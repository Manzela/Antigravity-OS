"""Unit tests for the Antigravity OS governance kernel."""

import pytest

from ag_os.config import find_config_file, load_config
from ag_os.core.cost_guard import check_solvency
from ag_os.core.flight_recorder import FlightRecorder
from ag_os.core.rules_engine import evaluate_governance
from ag_os.providers.registry import get_provider, list_providers

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------


class TestConfig:
    """Tests for the configuration system."""

    def test_load_config_returns_defaults(self):
        config = load_config()
        assert config["version"] == "1.0"
        assert isinstance(config["monthly_cap"], int | float)
        assert isinstance(config["providers"], dict)

    def test_find_config_file(self):
        path = find_config_file()
        # May be None in CI without antigravity.yaml
        if path:
            assert path.name in ("antigravity.yaml", "antigravity.yml")

    def test_env_override_monthly_cap(self, monkeypatch):
        monkeypatch.setenv("AG_OS_MONTHLY_CAP", "999.99")
        config = load_config()
        assert config["monthly_cap"] == 999.99

    def test_env_override_max_loops(self, monkeypatch):
        monkeypatch.setenv("AG_OS_MAX_LOOPS", "20")
        config = load_config()
        assert config["max_loop_count"] == 20


# ---------------------------------------------------------------------------
# Provider Registry
# ---------------------------------------------------------------------------


class TestRegistry:
    """Tests for provider registration and discovery."""

    def test_list_providers_returns_all_surfaces(self):
        providers = list_providers()
        expected = {"secrets", "issues", "cost", "state", "telemetry", "policy"}
        assert expected.issubset(set(providers.keys()))

    def test_get_provider_returns_instance(self):
        provider = get_provider("cost", "local")
        assert hasattr(provider, "get_current_spend")
        assert hasattr(provider, "get_tier_rate")
        assert hasattr(provider, "check_solvency")

    def test_get_provider_unknown_raises_valueerror(self):
        with pytest.raises(ValueError, match="Unknown"):
            get_provider("cost", "nonexistent_cloud")

    def test_get_provider_unknown_surface_raises_valueerror(self):
        with pytest.raises(ValueError, match="Unknown"):
            get_provider("nonexistent_surface", "anything")


# ---------------------------------------------------------------------------
# Cost Guard (Rule 08)
# ---------------------------------------------------------------------------


class TestCostGuard:
    """Tests for the solvency gate."""

    def test_solvent_with_default_config(self):
        result = check_solvency(units=1.0, tier="standard_cpu")
        assert result.is_solvent is True
        assert result.margin > 0

    def test_insolvent_with_large_allocation(self):
        config = load_config()
        config["monthly_cap"] = 50.0  # Explicit low cap for deterministic test
        result = check_solvency(units=100, tier="gpu_large", config=config)
        assert result.is_solvent is False
        assert result.margin < 0

    def test_custom_cap_override(self):
        config = load_config()
        config["monthly_cap"] = 1.00
        result = check_solvency(units=1.0, tier="standard_cpu", config=config)
        # 1 unit * $1.00/unit = $1.00, cap is $1.00 => solvent (equal)
        assert result.is_solvent is True

    def test_unknown_tier_raises_valueerror(self):
        with pytest.raises(ValueError, match="Unknown pricing tier"):
            check_solvency(units=1.0, tier="nonexistent_tier")


# ---------------------------------------------------------------------------
# Flight Recorder (Rule 05)
# ---------------------------------------------------------------------------


class TestFlightRecorder:
    """Tests for the deterministic state machine."""

    @pytest.fixture()
    def recorder(self):
        config = load_config()
        config["providers"]["state"] = "sqlite"  # Force sqlite for test isolation
        r = FlightRecorder(config=config)
        yield r
        # Cleanup
        r.reset("test-op")

    def test_initial_state_is_idle(self, recorder):
        assert recorder.get_current_state("test-op") == "IDLE"

    def test_valid_transition_sequence(self, recorder):
        recorder.transition("test-op", "PLANNING")
        assert recorder.get_current_state("test-op") == "PLANNING"
        recorder.transition("test-op", "PLAN_APPROVED")
        assert recorder.get_current_state("test-op") == "PLAN_APPROVED"

    def test_invalid_transition_raises_valueerror(self, recorder):
        with pytest.raises(ValueError, match="Invalid state transition"):
            recorder.transition("test-op", "COMPLETE")

    def test_full_lifecycle(self, recorder):
        states = ["PLANNING", "PLAN_APPROVED", "BUILDING", "VERIFYING", "COMPLETE"]
        for state in states:
            recorder.transition("test-op", state)
        assert recorder.get_current_state("test-op") == "COMPLETE"

    def test_get_history_returns_records(self, recorder):
        recorder.transition("test-op", "PLANNING")
        recorder.transition("test-op", "PLAN_APPROVED")
        history = recorder.get_history("test-op")
        assert len(history) >= 2

    def test_reset_returns_to_idle(self, recorder):
        recorder.transition("test-op", "PLANNING")
        recorder.reset("test-op")
        assert recorder.get_current_state("test-op") == "IDLE"


# ---------------------------------------------------------------------------
# Rules Engine (Policy)
# ---------------------------------------------------------------------------


class TestRulesEngine:
    """Tests for governance policy evaluation."""

    def test_allowed_with_valid_input(self):
        result = evaluate_governance(
            {
                "has_plan": True,
                "is_solvent": True,
                "state": "BUILDING",
            }
        )
        assert result.allowed is True
        assert result.violations == []

    def test_blocked_without_plan(self):
        result = evaluate_governance(
            {
                "requires_plan": True,
                "has_plan": False,
            }
        )
        assert result.allowed is False
        assert len(result.violations) > 0


# ---------------------------------------------------------------------------
# Default Providers (Smoke Tests)
# ---------------------------------------------------------------------------


class TestDefaultProviders:
    """Smoke tests for all default provider implementations."""

    def test_local_secrets_provider(self):
        provider = get_provider("secrets", "local")
        # Should not raise
        secrets = provider.list_secrets()
        assert isinstance(secrets, list)

    def test_env_secrets_provider(self):
        provider = get_provider("secrets", "env")
        # PATH is always in environment
        result = provider.get_secret("PATH")
        assert result is not None

    def test_console_issue_provider(self):
        provider = get_provider("issues", "console")
        assert hasattr(provider, "create_issue")
        assert hasattr(provider, "find_duplicate")

    def test_sqlite_state_provider(self):
        provider = get_provider("state", "sqlite")
        assert provider.ping() is True
        provider.set("test_key", "test_value")
        assert provider.get("test_key") == "test_value"
        provider.delete("test_key")
        assert provider.get("test_key") is None

    def test_console_telemetry_provider(self, capsys):
        provider = get_provider("telemetry", "console")
        provider.emit_trace({"trace_id": "test", "status": "ok"})
        captured = capsys.readouterr()
        assert "TRACE" in captured.out

    def test_builtin_policy_provider(self):
        provider = get_provider("policy", "builtin")
        policies = provider.list_policies()
        assert isinstance(policies, list)
