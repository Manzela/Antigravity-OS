# Agent Handover Contracts: Interface Definition Language (IDL)

This document strictly defines the required output metadata for all Agent-to-Agent (A2A) handoffs, enforcing Rule 06.

## I. Planner -> Cost Guard (PLAN_APPROVED)
* **Required Manifest:**
  * `plan_md_path`: Path to the approved plan.
  * `cost_estimate_usd`: Estimated infrastructure cost.

## II. Cost Guard -> Builder (COST_VALIDATED)
* **Invariant Solvency Gate (Rule 08)**
* **Required Manifest:**
  * `solvency_token`: Redis Lease ID or Approval Hash.

## III. Builder -> QC (BUILD_COMPLETE)
* **Required Manifest:**
  * `build_image_digest`: SHA256 of the Docker image.
  * `service_endpoint_url`: Localhost or staging URL.

## IV. QC -> Hub (READY_FOR_MERGE)
* **Required Manifest:**
  * `validation_report_path`: Path to the Nerd's report.
  * `verdict`: PASS or FAIL.
