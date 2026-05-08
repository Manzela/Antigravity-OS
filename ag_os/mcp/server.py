"""Antigravity OS MCP Server.

Exposes the governance kernel as MCP tools for AI agents:
  - check_solvency: Run the Cost Guard solvency gate.
  - transition_state: Advance the Flight Recorder state machine.
  - evaluate_policy: Execute the Rules Engine against governance rules.
  - get_status: Return current configuration and provider setup.
  - get_history: Retrieve the Flight Recorder audit trail.
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from ag_os.config import load_config
from ag_os.core.cost_guard import check_solvency as _check_solvency
from ag_os.core.flight_recorder import FlightRecorder
from ag_os.core.rules_engine import evaluate_governance

mcp = FastMCP(
    "antigravity-os",
    instructions=(
        "Governance kernel for AI agents. "
        "Cost enforcement, policy-as-code, and deterministic state tracking."
    ),
)


@mcp.tool()
def check_solvency(
    units: float = 1.0,
    tier: str = "standard_cpu",
) -> dict:
    """Check whether the projected cost is within the monthly budget cap.

    Returns a solvency report with is_solvent, current_spend, projected_cost,
    monthly_cap, and remaining_budget.

    Args:
        units: Number of resource units to project.
        tier: Pricing tier (standard_cpu, standard_gpu, gpu_large).
    """
    config = load_config()
    result = _check_solvency(units=units, tier=tier, config=config)
    return {
        "is_solvent": result.is_solvent,
        "current_spend": result.current_spend,
        "projected_cost": result.projected_cost,
        "monthly_cap": result.monthly_cap,
        "remaining_budget": result.margin,
    }


@mcp.tool()
def transition_state(
    operation: str,
    target_state: str,
    metadata: dict | None = None,
) -> dict:
    """Advance the Flight Recorder state machine for an operation.

    Valid states: IDLE, PLANNING, PLAN_APPROVED, BUILDING, VERIFYING,
    COMPLETE, BLOCKED, ROLLED_BACK.

    Args:
        operation: Identifier for the current operation (e.g. task ID).
        target_state: The state to transition to.
        metadata: Optional key-value metadata to attach to the transition.
    """
    config = load_config()
    recorder = FlightRecorder(config=config)
    try:
        recorder.transition(operation, target_state, metadata=metadata)
        current = recorder.get_current_state(operation)
        return {
            "status": "ok",
            "operation": operation,
            "current_state": current,
        }
    except ValueError as e:
        return {
            "status": "error",
            "operation": operation,
            "error": str(e),
        }


@mcp.tool()
def evaluate_policy(
    requires_plan: bool = True,
    has_plan: bool = False,
    state: str = "IDLE",
) -> dict:
    """Evaluate governance rules against the current operation context.

    Returns the policy evaluation result: allowed (bool) and a list of
    individual rule results.

    Args:
        requires_plan: Whether the operation requires a plan.
        has_plan: Whether a plan exists and has been approved.
        state: Current Flight Recorder state of the operation.
    """
    config = load_config()
    context = {
        "requires_plan": requires_plan,
        "has_plan": has_plan,
        "state": state,
    }
    result = evaluate_governance(context, config=config)
    return {
        "allowed": result.allowed,
        "policy_name": result.policy_name,
        "violations": result.violations,
    }


@mcp.tool()
def get_status() -> dict:
    """Return the current Antigravity OS configuration and provider setup."""
    config = load_config()
    return {
        "config_path": config.get("_config_path", "Not found"),
        "monthly_cap": config.get("monthly_cap", 0),
        "max_loop_count": config.get("max_loop_count", 5),
        "providers": config.get("providers", {}),
        "ci_platform": config.get("ci", {}).get("platform", "local"),
    }


@mcp.tool()
def get_history(operation: str) -> dict:
    """Retrieve the Flight Recorder audit trail for an operation.

    Args:
        operation: The operation identifier to look up.
    """
    config = load_config()
    recorder = FlightRecorder(config=config)
    history = recorder.get_history(operation)
    return {
        "operation": operation,
        "record_count": len(history),
        "records": [
            {
                "trace_id": h.trace_id,
                "state": h.state,
                "previous_state": h.previous_state,
                "timestamp": h.timestamp,
                "metadata": h.metadata,
                "error": h.error,
            }
            for h in history
        ],
    }


@mcp.tool()
def dream(dry_run: bool = False) -> dict:
    """Run the Dreaming Module self-improvement cycle.

    Analyzes the Flight Recorder for friction patterns (loops, rollbacks,
    budget failures), generates a Dream Report with proposed governance
    patches, and persists the report to long-term memory.

    Args:
        dry_run: If True, analyze friction but don't persist the report.
    """
    from ag_os.core.dreaming import DreamEngine

    config = load_config()
    engine = DreamEngine(config=config)

    friction = engine.scan_friction()
    report = engine.synthesize(friction)

    if not dry_run:
        path = engine.persist(report)
        persisted_to = str(path)
    else:
        persisted_to = None

    return {
        "dream_id": report.dream_id,
        "timestamp": report.timestamp,
        "operations_analyzed": report.operations_analyzed,
        "friction_detected": report.friction_detected,
        "summary": report.summary,
        "persisted_to": persisted_to,
        "friction_events": [
            {
                "operation": e.operation,
                "archetype": e.archetype,
                "severity": e.severity,
                "diagnosis": e.diagnosis,
            }
            for e in report.friction_events
        ],
        "proposed_patches": [
            {
                "patch_type": p.patch_type,
                "target": p.target,
                "description": p.description,
                "yaml_content": p.yaml_content,
            }
            for p in report.proposed_patches
        ],
    }


@mcp.tool()
def recall_dreams(n: int = 5) -> dict:
    """Retrieve recent Dream Reports from long-term memory.

    Returns the N most recent Dream Reports stored in
    ~/.antigravity/dreams/, ordered newest first.

    Args:
        n: Number of recent dream reports to retrieve.
    """
    from ag_os.core.dreaming import DreamEngine

    config = load_config()
    engine = DreamEngine(config=config)
    reports = engine.recall(n=n)

    return {
        "count": len(reports),
        "reports": [
            {
                "dream_id": r.dream_id,
                "timestamp": r.timestamp,
                "operations_analyzed": r.operations_analyzed,
                "friction_detected": r.friction_detected,
                "summary": r.summary,
                "friction_events": [
                    {
                        "operation": e.operation,
                        "archetype": e.archetype,
                        "severity": e.severity,
                        "diagnosis": e.diagnosis,
                    }
                    for e in r.friction_events
                ],
                "proposed_patches": [
                    {
                        "patch_type": p.patch_type,
                        "target": p.target,
                        "description": p.description,
                    }
                    for p in r.proposed_patches
                ],
            }
            for r in reports
        ],
    }


def run_server():
    """Entry point for the MCP server."""
    mcp.run(transport="stdio")
