"""
Patch Applier — Risk-based GitOps engine for governance patches.

Applies DreamEngine-generated GovernancePatch objects to configuration
and rule files on disk. Uses ruamel.yaml for comment-preserving YAML
round-trips when available, falling back to PyYAML.

Risk classification:
    LOW    → Auto-applicable (THRESHOLD_ADJUSTMENT)
    MEDIUM → Auto-applicable with notification (CONFIG_CHANGE)
    HIGH   → Mandatory human approval (NEW_RULE)
"""

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

_AUDIT_PATH = Path.home() / ".antigravity" / "patch_audit.yaml"

# Risk classification for patch types
_RISK_MAP = {
    "THRESHOLD_ADJUSTMENT": "LOW",
    "CONFIG_CHANGE": "MEDIUM",
    "NEW_RULE": "HIGH",
}


def classify_risk(patch_type: str) -> str:
    """Classify the risk level of a patch by its type."""
    return _RISK_MAP.get(patch_type, "HIGH")


def preview_patch(patch) -> str:
    """Generate a human-readable diff preview of a governance patch.

    Args:
        patch: A GovernancePatch dataclass instance.

    Returns:
        A formatted string showing what will be changed.
    """
    lines = []
    lines.append(f"  Patch Type:  {patch.patch_type}")
    lines.append(f"  Target:      {patch.target}")
    lines.append(f"  Risk:        {classify_risk(patch.patch_type)}")
    lines.append(f"  Description: {patch.description}")
    if patch.yaml_content:
        lines.append("  Content:")
        for line in patch.yaml_content.strip().splitlines():
            lines.append(f"    + {line}")
    return "\n".join(lines)


def apply_patch(
    patch,
    config_path: Optional[Path] = None,
    interactive: bool = True,
) -> bool:
    """Apply a governance patch to disk.

    For THRESHOLD_ADJUSTMENT and CONFIG_CHANGE patches targeting
    antigravity.yaml, modifies the YAML file in place. For NEW_RULE
    patches, writes the rule file to .agent/rules/.

    Args:
        patch: A GovernancePatch dataclass instance.
        config_path: Path to antigravity.yaml (auto-discovered if None).
        interactive: If True, prompt for confirmation on HIGH risk patches.

    Returns:
        True if the patch was applied, False if skipped or rejected.
    """
    risk = classify_risk(patch.patch_type)

    # HIGH/CRITICAL risk requires explicit human approval
    if risk in ("HIGH", "CRITICAL") and interactive:
        print()
        print(preview_patch(patch))
        print()
        try:
            answer = input(f"  Apply this {risk}-risk patch? [y/N]: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            answer = "n"
        if answer != "y":
            logger.info("Patch rejected by user: %s", patch.target)
            audit_patch_application(patch, applied=False, reason="rejected_by_user")
            return False

    applied = False

    if patch.patch_type == "NEW_RULE":
        applied = _apply_new_rule(patch)
    elif patch.patch_type in ("THRESHOLD_ADJUSTMENT", "CONFIG_CHANGE"):
        applied = _apply_config_change(patch, config_path)
    else:
        logger.warning("Unknown patch type: %s", patch.patch_type)

    audit_patch_application(patch, applied=applied)
    return applied


def _apply_new_rule(patch) -> bool:
    """Write a new rule file to .agent/rules/."""
    # Extract filename from target (e.g. ".agent/rules/09-rollback-circuit-breaker.md")
    target = Path(patch.target)
    if not target.parts:
        return False

    # Ensure directory exists
    target.parent.mkdir(parents=True, exist_ok=True)

    if target.exists():
        logger.info("Rule file already exists, skipping: %s", target)
        return False

    target.write_text(patch.yaml_content, encoding="utf-8")
    logger.info("Created rule file: %s", target)
    return True


def _apply_config_change(patch, config_path: Optional[Path] = None) -> bool:
    """Apply a config/threshold change to antigravity.yaml."""
    if config_path is None:
        config_path = Path("antigravity.yaml")

    if not config_path.is_file():
        logger.warning("Config file not found: %s", config_path)
        return False

    try:
        # Try ruamel.yaml for comment-preserving round-trip
        from ruamel.yaml import YAML

        ryaml = YAML()
        ryaml.preserve_quotes = True

        with open(config_path, "r", encoding="utf-8") as f:
            data = ryaml.load(f)

        _merge_patch_content(data, patch.yaml_content)

        with open(config_path, "w", encoding="utf-8") as f:
            ryaml.dump(data, f)

        logger.info("Applied config change (ruamel.yaml): %s", patch.target)
        return True

    except ImportError:
        # Fallback to PyYAML (loses comments)
        import yaml

        with open(config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        _merge_patch_content(data, patch.yaml_content)

        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

        logger.info("Applied config change (PyYAML fallback): %s", patch.target)
        return True

    except Exception as e:
        logger.error("Failed to apply config change: %s", e)
        return False


def _merge_patch_content(data: dict, yaml_content: str) -> None:
    """Parse yaml_content from a patch and merge key-value pairs into data."""
    import yaml

    # Strip markdown-style comments
    clean_lines = []
    for line in yaml_content.strip().splitlines():
        stripped = line.strip()
        if stripped.startswith("#") or stripped.startswith("**"):
            continue
        clean_lines.append(line)

    if not clean_lines:
        return

    try:
        patch_data = yaml.safe_load("\n".join(clean_lines))
        if isinstance(patch_data, dict):
            data.update(patch_data)
    except yaml.YAMLError:
        pass


def audit_patch_application(
    patch,
    applied: bool = True,
    reason: str = "",
) -> None:
    """Append a patch application record to the audit trail.

    Writes to ~/.antigravity/patch_audit.yaml for governance traceability.
    """
    import yaml

    _AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)

    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "patch_type": patch.patch_type,
        "target": patch.target,
        "risk": classify_risk(patch.patch_type),
        "applied": applied,
        "reason": reason or ("applied" if applied else "skipped"),
        "description": patch.description,
    }

    # Append to audit log
    existing = []
    if _AUDIT_PATH.is_file():
        try:
            with open(_AUDIT_PATH, "r", encoding="utf-8") as f:
                existing = yaml.safe_load(f) or []
        except (yaml.YAMLError, OSError):
            existing = []

    if not isinstance(existing, list):
        existing = []

    existing.append(record)

    with open(_AUDIT_PATH, "w", encoding="utf-8") as f:
        yaml.dump(existing, f, default_flow_style=False, sort_keys=False, width=120)
