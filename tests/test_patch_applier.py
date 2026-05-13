"""Tests for the patch applier module."""

import yaml

from ag_os.core.dreaming import GovernancePatch
from ag_os.core.patch_applier import (
    _merge_patch_content,
    apply_patch,
    audit_patch_application,
    classify_risk,
    preview_patch,
)


class TestClassifyRisk:
    """Validate risk classification mapping."""

    def test_threshold_adjustment_is_low(self):
        assert classify_risk("THRESHOLD_ADJUSTMENT") == "LOW"

    def test_config_change_is_medium(self):
        assert classify_risk("CONFIG_CHANGE") == "MEDIUM"

    def test_new_rule_is_high(self):
        assert classify_risk("NEW_RULE") == "HIGH"

    def test_unknown_defaults_to_high(self):
        assert classify_risk("UNKNOWN_TYPE") == "HIGH"


class TestPreviewPatch:
    """Validate human-readable preview generation."""

    def test_preview_includes_all_fields(self):
        patch = GovernancePatch(
            patch_type="CONFIG_CHANGE",
            target="antigravity.yaml",
            description="Test change",
            yaml_content="key: value",
        )
        output = preview_patch(patch)
        assert "CONFIG_CHANGE" in output
        assert "antigravity.yaml" in output
        assert "MEDIUM" in output
        assert "Test change" in output
        assert "+ key: value" in output


class TestMergePatchContent:
    """Validate YAML content merging."""

    def test_merge_simple_key_value(self):
        data = {"existing_key": "old_value"}
        _merge_patch_content(data, "new_key: new_value")
        assert data["new_key"] == "new_value"
        assert data["existing_key"] == "old_value"

    def test_merge_strips_comments(self):
        data = {}
        _merge_patch_content(data, "# comment\nkey: value\n**bold line**")
        assert data.get("key") == "value"

    def test_merge_handles_empty_content(self):
        data = {"key": "value"}
        _merge_patch_content(data, "")
        assert data == {"key": "value"}

    def test_merge_handles_invalid_yaml(self):
        data = {"key": "value"}
        _merge_patch_content(data, "not: valid: yaml: [[[")
        # Should not crash — fails silently
        assert "key" in data


class TestApplyPatch:
    """Validate patch application logic."""

    def test_apply_new_rule_creates_file(self, tmp_path, monkeypatch):
        # Run from a clean tmp dir so .agent/rules is anchored under tmp_path.
        monkeypatch.chdir(tmp_path)
        target_rel = ".agent/rules/test-rule.md"
        patch = GovernancePatch(
            patch_type="NEW_RULE",
            target=target_rel,
            description="Test rule",
            yaml_content="# Rule: test\nDo the thing.",
        )
        result = apply_patch(patch, interactive=False)
        assert result is True
        assert (tmp_path / target_rel).is_file()
        assert "Do the thing" in (tmp_path / target_rel).read_text()

    def test_apply_new_rule_skips_existing(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        target_rel = ".agent/rules/existing-rule.md"
        existing = tmp_path / target_rel
        existing.parent.mkdir(parents=True)
        existing.write_text("existing content")

        patch = GovernancePatch(
            patch_type="NEW_RULE",
            target=target_rel,
            description="Test",
            yaml_content="new content",
        )
        result = apply_patch(patch, interactive=False)
        assert result is False
        assert existing.read_text() == "existing content"

    def test_apply_config_change(self, tmp_path):
        config_file = tmp_path / "antigravity.yaml"
        config_file.write_text("max_loop_count: 5\n")
        patch = GovernancePatch(
            patch_type="THRESHOLD_ADJUSTMENT",
            target="max_loop_count",
            description="Reduce loops",
            yaml_content="max_loop_count: 3",
        )
        result = apply_patch(patch, config_path=config_file, interactive=False)
        assert result is True
        with open(config_file) as f:
            data = yaml.safe_load(f)
        assert data["max_loop_count"] == 3


class TestApplyNewRuleTraversal:
    """Path-traversal regression tests for _apply_new_rule (P0-2)."""

    def test_rejects_absolute_posix_path(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        sentinel = tmp_path / "sentinel.md"
        patch = GovernancePatch(
            patch_type="NEW_RULE",
            target=str(sentinel),  # absolute path
            description="Should be rejected",
            yaml_content="# pwn\n",
        )
        result = apply_patch(patch, interactive=False)
        assert result is False
        assert not sentinel.exists()

    def test_rejects_home_relative_path(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        patch = GovernancePatch(
            patch_type="NEW_RULE",
            target="~/.ssh/authorized_keys",
            description="Home-relative attack",
            yaml_content="ssh-rsa AAAA...",
        )
        result = apply_patch(patch, interactive=False)
        assert result is False

    def test_rejects_parent_traversal(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        patch = GovernancePatch(
            patch_type="NEW_RULE",
            target=".agent/rules/../../escape.md",
            description="Parent traversal",
            yaml_content="# escape\n",
        )
        result = apply_patch(patch, interactive=False)
        assert result is False
        assert not (tmp_path / "escape.md").exists()

    def test_rejects_path_outside_rules_dir(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        # Relative path with no traversal but lands outside .agent/rules
        patch = GovernancePatch(
            patch_type="NEW_RULE",
            target=".agent/wrong/escape.md",
            description="Sibling-dir attack",
            yaml_content="# escape\n",
        )
        result = apply_patch(patch, interactive=False)
        assert result is False
        assert not (tmp_path / ".agent" / "wrong" / "escape.md").exists()

    def test_rejects_null_byte_injection(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        patch = GovernancePatch(
            patch_type="NEW_RULE",
            target=".agent/rules/legit.md\x00/etc/passwd",
            description="Null-byte truncation attack",
            yaml_content="# pwn\n",
        )
        result = apply_patch(patch, interactive=False)
        assert result is False

    def test_accepts_valid_relative_rule_path(self, tmp_path, monkeypatch):
        # Mirrors the engine's own emitted target shape (dreaming.py:424).
        monkeypatch.chdir(tmp_path)
        target_rel = ".agent/rules/09-rollback-circuit-breaker.md"
        patch = GovernancePatch(
            patch_type="NEW_RULE",
            target=target_rel,
            description="Engine-emitted shape",
            yaml_content="# Rule\n",
        )
        result = apply_patch(patch, interactive=False)
        assert result is True
        assert (tmp_path / target_rel).is_file()


class TestApplyConfigChangeAutoDiscovery:
    """Regression tests for the CWD-relative config write (P1-1)."""

    def test_refuses_when_no_config_discovered(self, tmp_path, monkeypatch):
        # Empty tmp dir — no antigravity.yaml anywhere upward (we walk up
        # at most 20 levels from cwd, but tmp_path isolates this).
        monkeypatch.chdir(tmp_path)
        patch = GovernancePatch(
            patch_type="THRESHOLD_ADJUSTMENT",
            target="max_loop_count",
            description="Should refuse — no config",
            yaml_content="max_loop_count: 7",
        )
        result = apply_patch(patch, interactive=False)
        # Refused: no config to write to and no explicit path.
        assert result is False
        # Crucially: no antigravity.yaml was created in CWD.
        assert not (tmp_path / "antigravity.yaml").exists()

    def test_writes_to_explicit_config_path_regardless_of_cwd(self, tmp_path, monkeypatch):
        explicit = tmp_path / "configs" / "antigravity.yaml"
        explicit.parent.mkdir()
        explicit.write_text("max_loop_count: 5\n")

        # Drop into a sibling dir to prove the patch does NOT chase CWD.
        sibling = tmp_path / "elsewhere"
        sibling.mkdir()
        monkeypatch.chdir(sibling)

        patch = GovernancePatch(
            patch_type="THRESHOLD_ADJUSTMENT",
            target="max_loop_count",
            description="Explicit path wins",
            yaml_content="max_loop_count: 3",
        )
        result = apply_patch(patch, config_path=explicit, interactive=False)
        assert result is True
        with open(explicit) as f:
            data = yaml.safe_load(f)
        assert data["max_loop_count"] == 3
        # Sibling dir was not touched.
        assert not (sibling / "antigravity.yaml").exists()


class TestAuditTrail:
    """Validate audit trail persistence."""

    def test_audit_appends_record(self, tmp_path):
        import ag_os.core.patch_applier as pa

        original_path = pa._AUDIT_PATH
        pa._AUDIT_PATH = tmp_path / "audit.yaml"
        try:
            patch = GovernancePatch(
                patch_type="CONFIG_CHANGE",
                target="test",
                description="Audit test",
            )
            audit_patch_application(patch, applied=True, reason="test")

            with open(pa._AUDIT_PATH) as f:
                records = yaml.safe_load(f)
            assert len(records) == 1
            assert records[0]["applied"] is True
            assert records[0]["reason"] == "test"
        finally:
            pa._AUDIT_PATH = original_path
