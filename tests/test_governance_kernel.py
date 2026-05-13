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
    """Tests for governance policy evaluation (P1-8 — expanded coverage)."""

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
        assert any("Rule 00" in v for v in result.violations)

    def test_plan_not_required_passes_with_no_plan(self):
        """If requires_plan is false, missing plan is fine.

        Rule 00 only fires when requires_plan is True.
        """
        result = evaluate_governance({"requires_plan": False, "has_plan": False})
        assert result.allowed is True

    def test_blocked_on_unknown_state(self):
        """Rule 02: Fail Closed — any state not in the FlightRecorder enum blocks."""
        result = evaluate_governance({"state": "FROBNICATING"})
        assert result.allowed is False
        assert any("Rule 02" in v for v in result.violations)

    def test_blocked_on_insolvent(self):
        """Rule 08: explicit is_solvent=False blocks."""
        result = evaluate_governance({"is_solvent": False})
        assert result.allowed is False
        assert any("Rule 08" in v for v in result.violations)

    def test_solvency_omitted_does_not_block(self):
        """Rule 08 only fires when is_solvent is *present* and false (no key = no claim made)."""
        result = evaluate_governance({})
        # No violations from Rule 08 when key is absent.
        assert not any("Rule 08" in v for v in result.violations)

    def test_blocked_on_loop_excess(self):
        """Rule 07: loop_count > max_loop_count blocks."""
        result = evaluate_governance({"loop_count": 99, "max_loop_count": 5})
        assert result.allowed is False
        assert any("Rule 07" in v for v in result.violations)

    def test_loop_excess_uses_default_max_when_unset(self):
        """When config doesn't specify max_loop_count, default is 5; loop_count 6 should block."""
        # evaluate_governance auto-injects max_loop_count from config.get(..., 5).
        result = evaluate_governance({"loop_count": 6})
        assert result.allowed is False
        assert any("Rule 07" in v for v in result.violations)

    def test_combined_violations_listed(self):
        """Multiple rules can fail simultaneously; each violation is reported."""
        result = evaluate_governance(
            {
                "requires_plan": True,
                "has_plan": False,
                "state": "WHATEVER",
                "is_solvent": False,
                "loop_count": 99,
                "max_loop_count": 5,
            }
        )
        assert result.allowed is False
        assert len(result.violations) >= 4
        assert any("Rule 00" in v for v in result.violations)
        assert any("Rule 02" in v for v in result.violations)
        assert any("Rule 07" in v for v in result.violations)
        assert any("Rule 08" in v for v in result.violations)

    def test_known_states_pass(self):
        """All states in the Flight Recorder enum are accepted by Rule 02."""
        for state in (
            "PLANNING",
            "PLAN_APPROVED",
            "BUILDING",
            "VERIFYING",
            "COMPLETE",
            "BLOCKED",
            "ROLLED_BACK",
        ):
            result = evaluate_governance({"state": state})
            assert not any("Rule 02" in v for v in result.violations), (
                f"State {state!r} should not trigger Rule 02"
            )

    def test_empty_state_passes_rule_02(self):
        """Empty/missing state means 'no state claim' — Rule 02 doesn't fire on absence."""
        result = evaluate_governance({"state": ""})
        assert not any("Rule 02" in v for v in result.violations)

    def test_policy_name_in_result(self):
        """PolicyResult exposes the policy_name that was evaluated."""
        result = evaluate_governance({"has_plan": True})
        assert result.policy_name in ("governance", "")  # builtin default


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

    def test_console_issue_provider(self, tmp_path, monkeypatch, capsys):
        """Behavior test (P1-9): create_issue persists to JSONL and find_duplicate hits it."""
        # Redirect the issue store to a temp file so the test is hermetic.
        import ag_os.providers.issues.console as console_mod

        store = tmp_path / "issues.jsonl"
        monkeypatch.setattr(console_mod, "_ISSUE_STORE", store)
        monkeypatch.setattr(
            console_mod, "_FRICTION_LOG", tmp_path / "docs" / "SDLC_Friction_Log.md"
        )

        from ag_os.providers.issues import IssuePayload

        provider = console_mod.ConsoleIssueProvider()
        payload = IssuePayload(
            summary="Disk usage > 90%",
            description="Filesystem health check",
            fingerprint="abcd1234ef567890",
            severity="high",
        )
        issue_id = provider.create_issue(payload)

        # Returned ID is non-empty and stable for a fingerprint
        assert issue_id, "create_issue must return a non-empty ID"
        assert "abcd1234" in issue_id

        # Persisted to JSONL
        assert store.is_file()
        import json as _json

        records = [_json.loads(ln) for ln in store.read_text().splitlines() if ln.strip()]
        assert any(r.get("fingerprint") == "abcd1234ef567890" for r in records)

        # Dedup: same fingerprint resolves to the existing ID
        dup = provider.find_duplicate("abcd1234ef567890")
        assert dup == issue_id

        # Stdout receives the human-readable banner
        out = capsys.readouterr().out
        assert issue_id in out
        assert "Disk usage" in out

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

    def test_builtin_policy_provider_lists_loaded_policies(self, tmp_path, monkeypatch):
        """Behavior test (P1-9): list_policies reflects loaded .agent/rules files."""
        rules_dir = tmp_path / ".agent" / "rules"
        rules_dir.mkdir(parents=True)
        (rules_dir / "00-test-rule.md").write_text(
            "# Rule 00: Plan First\n\n**Plan first** before building.\n"
        )
        (rules_dir / "08-test-economic.md").write_text(
            "# Rule 08: Economic Safety\n\n**Solvency gate**.\n"
        )

        from ag_os.providers.policy.builtin import BuiltinPolicyProvider

        provider = BuiltinPolicyProvider(rules_dir=str(rules_dir))
        policies = provider.list_policies()
        assert "00-test-rule" in policies
        assert "08-test-economic" in policies

    def test_builtin_policy_provider_evaluates_real_rules(self):
        """Behavior test (P1-9): evaluate enforces Rule 00 / 02 / 08 / 07."""
        from ag_os.providers.policy.builtin import BuiltinPolicyProvider

        provider = BuiltinPolicyProvider()

        # Rule 00 — plan required and absent => deny
        r = provider.evaluate({"requires_plan": True, "has_plan": False})
        assert r.allowed is False
        assert any("Rule 00" in v for v in r.violations)

        # Rule 02 — unknown state => deny (fail closed)
        r = provider.evaluate({"state": "FROBNICATING"})
        assert r.allowed is False
        assert any("Rule 02" in v for v in r.violations)

        # Rule 08 — insolvent => deny
        r = provider.evaluate({"is_solvent": False})
        assert r.allowed is False
        assert any("Rule 08" in v for v in r.violations)

        # Rule 07 — loop_count > max => deny
        r = provider.evaluate({"loop_count": 99, "max_loop_count": 5})
        assert r.allowed is False
        assert any("Rule 07" in v for v in r.violations)

        # Clean state — allow
        r = provider.evaluate(
            {
                "requires_plan": True,
                "has_plan": True,
                "state": "BUILDING",
                "is_solvent": True,
                "loop_count": 1,
                "max_loop_count": 5,
            }
        )
        assert r.allowed is True
        assert r.violations == []
