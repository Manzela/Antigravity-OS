"""Console issue provider (DEFAULT) — prints to stdout and appends to friction log."""

import json
from datetime import datetime, timezone
from pathlib import Path

from ag_os.providers.issues import IssuePayload, IssueProvider
from ag_os.providers.registry import register

_FRICTION_LOG = Path("docs/SDLC_Friction_Log.md")
_ISSUE_STORE = Path.home() / ".antigravity" / "issues.jsonl"


@register("issues", "console")
class ConsoleIssueProvider(IssueProvider):
    """Prints issues to stdout and appends to a local friction log.

    Zero API keys. Zero cloud accounts. Works immediately.
    """

    def __init__(self, **kwargs):
        _ISSUE_STORE.parent.mkdir(parents=True, exist_ok=True)

    def create_issue(self, payload: IssuePayload) -> str:
        timestamp = datetime.now(timezone.utc).isoformat()
        issue_id = f"LOCAL-{payload.fingerprint[:8]}"

        # Print to stdout
        print(f"\n  [ISSUE] {issue_id}")
        print(f"  Severity:    {payload.severity}")
        print(f"  Summary:     {payload.summary}")
        print(f"  Fingerprint: {payload.fingerprint}")
        if payload.owner_name:
            print(f"  Owner:       {payload.owner_name}")
        print(f"  Time:        {timestamp}")
        print()

        # Persist to local JSONL store
        record = {
            "id": issue_id,
            "timestamp": timestamp,
            "summary": payload.summary,
            "description": payload.description,
            "fingerprint": payload.fingerprint,
            "severity": payload.severity,
        }
        with open(_ISSUE_STORE, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")

        # Append to friction log if it exists
        if _FRICTION_LOG.parent.exists():
            _FRICTION_LOG.parent.mkdir(parents=True, exist_ok=True)
            with open(_FRICTION_LOG, "a", encoding="utf-8") as f:
                f.write(f"\n## {issue_id} — {payload.summary}\n")
                f.write(f"**Severity:** {payload.severity}  \n")
                f.write(f"**Time:** {timestamp}  \n")
                f.write(f"**Fingerprint:** `{payload.fingerprint}`  \n\n")
                if payload.description:
                    f.write(f"{payload.description}\n\n")
                f.write("---\n")

        return issue_id

    def find_duplicate(self, fingerprint: str) -> str | None:
        if not _ISSUE_STORE.is_file():
            return None
        with open(_ISSUE_STORE, encoding="utf-8") as f:
            for line in f:
                try:
                    record = json.loads(line.strip())
                    if record.get("fingerprint") == fingerprint:
                        return record.get("id")
                except json.JSONDecodeError:
                    continue
        return None

    def add_comment(self, issue_id: str, comment: str) -> None:
        timestamp = datetime.now(timezone.utc).isoformat()
        print(f"\n  [COMMENT on {issue_id}] {comment}")
        record = {
            "type": "comment",
            "issue_id": issue_id,
            "timestamp": timestamp,
            "comment": comment,
        }
        with open(_ISSUE_STORE, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
