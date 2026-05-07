# Agent Handover Contracts: Interface Definition Language (IDL)

This document defines the required output metadata for all Agent-to-Agent
(A2A) handoffs, enforcing Rule 06.

## I. Planner -> Cost Guard (PLAN_APPROVED)

Required Manifest:

- `plan_md_path`: Path to the approved plan.
- `cost_estimate_usd`: Estimated infrastructure cost.

## II. Cost Guard -> Builder (COST_VALIDATED)

Invariant Solvency Gate (Rule 08).

Required Manifest:

- `solvency_token`: Approval hash from the Cost Guard.
- `solvency_result`: SolvencyResult dataclass (margin, cap, projected).

## III. Builder -> QC (BUILD_COMPLETE)

Required Manifest:

- `build_digest`: SHA256 of the build artifact.
- `service_endpoint_url`: Localhost or staging URL.
- `flight_record_state`: Current Flight Recorder state (must be BUILDING).

## IV. QC -> Hub (READY_FOR_MERGE)

Required Manifest:

- `validation_report_path`: Path to the QC report.
- `verdict`: PASS or FAIL.
- `test_coverage_pct`: Percentage of lines covered.
