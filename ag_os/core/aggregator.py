"""
Cross-Repo Dream Aggregator — Enterprise-grade friction correlation.

Merges Dream Reports from multiple project directories to identify
systemic patterns that appear across repositories. Follows the
OpenTelemetry collector pattern: each repo is a source, the merge
command is the collector.

Usage:
    ag-os dream merge /path/to/repo1 /path/to/repo2
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


@dataclass
class SystemicPattern:
    """A friction archetype detected across multiple repositories."""

    archetype: str
    repo_count: int
    total_repos: int
    frequency: float  # repo_count / total_repos
    affected_repos: list[str] = field(default_factory=list)
    diagnosis: str = ""


@dataclass
class AggregatedDreamReport:
    """Merged analysis across multiple project dream archives."""

    report_id: str
    timestamp: str
    repos_analyzed: int = 0
    total_dreams_scanned: int = 0
    systemic_patterns: list[SystemicPattern] = field(default_factory=list)
    per_repo_summary: dict[str, dict[str, Any]] = field(default_factory=dict)
    summary: str = ""


def merge_dream_dirs(dirs: list[str | Path]) -> AggregatedDreamReport:
    """Merge dream archives from multiple directories.

    Scans each directory for ~/.antigravity/dreams/ YAML files,
    aggregates friction archetypes, and flags systemic patterns
    (archetypes appearing in >= 50% of repos).

    Args:
        dirs: List of project root directories to scan.

    Returns:
        An AggregatedDreamReport with systemic patterns and per-repo stats.
    """
    now = datetime.now(timezone.utc)
    report_id = f"aggregate-{now.strftime('%Y%m%d-%H%M%S')}"

    # archetype -> set of repo names that exhibited it
    archetype_repos: dict[str, set[str]] = {}
    per_repo: dict[str, dict[str, Any]] = {}
    total_dreams = 0

    for dir_path in dirs:
        dir_path = Path(dir_path)
        repo_name = dir_path.name
        dreams_dir = dir_path / ".antigravity" / "dreams"

        if not dreams_dir.is_dir():
            # Try the directory itself as a dreams directory
            dreams_dir = dir_path
            if not list(dreams_dir.glob("dream-*.yaml")):
                continue

        files = sorted(dreams_dir.glob("dream-*.yaml"))
        repo_friction_count = 0
        repo_success_count = 0
        repo_archetypes: dict[str, int] = {}

        for path in files:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                if not data:
                    continue

                total_dreams += 1
                repo_friction_count += data.get("friction_detected", 0)
                repo_success_count += data.get("successes_detected", 0)

                for event in data.get("friction_events", []):
                    archetype = event.get("archetype", "")
                    if archetype:
                        archetype_repos.setdefault(archetype, set()).add(repo_name)
                        repo_archetypes[archetype] = repo_archetypes.get(archetype, 0) + 1

            except (yaml.YAMLError, OSError):
                continue

        per_repo[repo_name] = {
            "dreams_scanned": len(files),
            "friction_count": repo_friction_count,
            "success_count": repo_success_count,
            "archetypes": repo_archetypes,
        }

    total_repos = len(per_repo)
    if total_repos == 0:
        return AggregatedDreamReport(
            report_id=report_id,
            timestamp=now.isoformat(),
            summary="No dream archives found in the specified directories.",
        )

    # Identify systemic patterns (>= 50% repos)
    systemic: list[SystemicPattern] = []
    threshold = max(1, total_repos * 0.5)

    for archetype, repos in sorted(archetype_repos.items()):
        if len(repos) >= threshold:
            freq = len(repos) / total_repos
            systemic.append(
                SystemicPattern(
                    archetype=archetype,
                    repo_count=len(repos),
                    total_repos=total_repos,
                    frequency=freq,
                    affected_repos=sorted(repos),
                    diagnosis=(
                        f"'{archetype}' detected in {len(repos)}/{total_repos} repos "
                        f"({freq:.0%}). This is a systemic issue requiring "
                        f"organization-wide governance adjustment."
                    ),
                )
            )

    # Build summary
    if systemic:
        pattern_names = ", ".join(p.archetype.lower().replace("_", " ") for p in systemic)
        summary = (
            f"Aggregated {total_dreams} dream reports across {total_repos} repos. "
            f"Identified {len(systemic)} systemic patterns: {pattern_names}. "
            f"These friction archetypes appear in the majority of repositories "
            f"and require cross-project governance review."
        )
    else:
        summary = (
            f"Aggregated {total_dreams} dream reports across {total_repos} repos. "
            f"No systemic patterns detected — friction is localized to individual projects."
        )

    return AggregatedDreamReport(
        report_id=report_id,
        timestamp=now.isoformat(),
        repos_analyzed=total_repos,
        total_dreams_scanned=total_dreams,
        systemic_patterns=systemic,
        per_repo_summary=per_repo,
        summary=summary,
    )


def print_aggregated_report(report: AggregatedDreamReport) -> None:
    """Print a formatted aggregated dream report."""
    print()
    print("  ================================================")
    print("  ANTIGRAVITY OS -- AGGREGATED DREAM REPORT")
    print("  ================================================")
    print()
    print(f"  Report ID:    {report.report_id}")
    print(f"  Timestamp:    {report.timestamp}")
    print(f"  Repos:        {report.repos_analyzed}")
    print(f"  Dreams:       {report.total_dreams_scanned}")
    print(f"  Systemic:     {len(report.systemic_patterns)} patterns")
    print()

    if report.systemic_patterns:
        print("  -- Systemic Patterns ----------------------------------------")
        print()
        for pattern in report.systemic_patterns:
            print(f"  [{pattern.archetype}] ({pattern.frequency:.0%} of repos)")
            print(f"    Repos: {', '.join(pattern.affected_repos)}")
            print(f"    {pattern.diagnosis}")
            print()

    if report.per_repo_summary:
        print("  -- Per-Repo Summary -----------------------------------------")
        print()
        for repo, stats in sorted(report.per_repo_summary.items()):
            print(f"  {repo}:")
            print(
                f"    Dreams: {stats['dreams_scanned']}, "
                f"Friction: {stats['friction_count']}, "
                f"Success: {stats['success_count']}"
            )
            print()

    print(f"  {report.summary}")
    print()
    print("  ================================================")
    print()
