"""Built-in policy provider (DEFAULT) -- evaluates Markdown governance rules."""

import re
from pathlib import Path
from typing import List

from ag_os.providers.policy import PolicyProvider, PolicyResult
from ag_os.providers.registry import register

_RULES_DIRS = [
    Path(".agent/rules"),
    Path("ag_os/templates/rules"),
]


@register("policy", "builtin")
class BuiltinPolicyProvider(PolicyProvider):
    """Lightweight Python evaluator that parses Markdown rule files.

    Reads governance rules from `.agent/rules/*.md` (project-level)
    or the bundled templates. No Docker, no OPA required.

    Each rule file is expected to have a title (# Rule Name) and
    keywords that map to enforceable checks (e.g., "plan first",
    "fail closed", "solvency gate").
    """

    def __init__(self, rules_dir: str = "", **kwargs):
        self._rules_dir = Path(rules_dir) if rules_dir else None
        self._rules: dict[str, dict] = {}
        self._load_rules()

    def _find_rules_dir(self) -> Path | None:
        if self._rules_dir and self._rules_dir.is_dir():
            return self._rules_dir
        for candidate in _RULES_DIRS:
            if candidate.is_dir():
                return candidate
        return None

    def _load_rules(self):
        """Parse all Markdown rule files into enforceable rule metadata."""
        self._rules.clear()
        rules_dir = self._find_rules_dir()
        if not rules_dir:
            return

        for md_file in sorted(rules_dir.glob("*.md")):
            rule_id = md_file.stem
            content = md_file.read_text(encoding="utf-8")
            title = ""
            keywords: list[str] = []

            for line in content.splitlines():
                line = line.strip()
                if line.startswith("# ") and not title:
                    title = line[2:].strip()
                # Extract enforceable keywords from bold text
                if "**" in line:
                    for match in re.finditer(r"\*\*(.+?)\*\*", line):
                        keywords.append(match.group(1).lower())

            self._rules[rule_id] = {
                "title": title or rule_id,
                "keywords": keywords,
                "path": str(md_file),
                "content": content,
            }

    def evaluate(
        self,
        input_data: dict,
        policy_name: str = "governance",
    ) -> PolicyResult:
        """Evaluate input data against loaded governance rules.

        Checks:
        - Rule 00: Plan must exist before execution
        - Rule 02: Fail-closed on unknown states
        - Rule 08: Solvency gate (if cost data present)

        Args:
            input_data: Dict with keys like "has_plan", "is_solvent", "state".
            policy_name: Policy set to evaluate against.

        Returns:
            PolicyResult with allowed=True if all rules pass.
        """
        violations: list[str] = []

        # Rule 00: Plan First
        if input_data.get("requires_plan", False) and not input_data.get("has_plan", False):
            violations.append("Rule 00: No approved plan found. Plan first, then build.")

        # Rule 02: Fail Closed
        state = input_data.get("state", "")
        if state and state not in (
            "PLANNING",
            "PLAN_APPROVED",
            "BUILDING",
            "VERIFYING",
            "COMPLETE",
            "BLOCKED",
            "ROLLED_BACK",
        ):
            violations.append(f"Rule 02: Unknown state '{state}'. Fail-closed: blocking execution.")

        # Rule 08: Economic Safety
        if "is_solvent" in input_data and not input_data["is_solvent"]:
            violations.append(
                "Rule 08: Solvency check failed. Projected spend exceeds monthly cap."
            )

        # Rule 07: Loop Detection
        loop_count = input_data.get("loop_count", 0)
        max_loops = input_data.get("max_loop_count", 5)
        if loop_count > max_loops:
            violations.append(
                f"Rule 07: Loop count ({loop_count}) exceeds maximum ({max_loops}). "
                "Escalating to human."
            )

        return PolicyResult(
            allowed=len(violations) == 0,
            violations=violations,
            policy_name=policy_name,
        )

    def list_policies(self) -> List[str]:
        return sorted(self._rules.keys())
