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

    def test_apply_new_rule_creates_file(self, tmp_path):
        target = tmp_path / ".agent" / "rules" / "test-rule.md"
        patch = GovernancePatch(
            patch_type="NEW_RULE",
            target=str(target),
            description="Test rule",
            yaml_content="# Rule: test\nDo the thing.",
        )
        result = apply_patch(patch, interactive=False)
        assert result is True
        assert target.is_file()
        assert "Do the thing" in target.read_text()

    def test_apply_new_rule_skips_existing(self, tmp_path):
        target = tmp_path / "existing-rule.md"
        target.write_text("existing content")
        patch = GovernancePatch(
            patch_type="NEW_RULE",
            target=str(target),
            description="Test",
            yaml_content="new content",
        )
        result = apply_patch(patch, interactive=False)
        assert result is False
        assert target.read_text() == "existing content"

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
