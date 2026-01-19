# Agent Handover Contracts: Interface Definition Language (IDL)

This document strictly defines the required output metadata for all Agent-to-Agent (A2A) handoffs, enforcing Rule 06.

## I. Planner -> Builder (PLAN_APPROVED)
* **Required Manifest:**
  * `plan_md_path`: Path to the approved plan.
  * `api_contract_version`: Version of the contract used.

## II. Builder -> QC (BUILD_COMPLETE)
* **Required Manifest:**
  * `build_image_digest`: SHA256 of the Docker image.
  * `service_endpoint_url`: Localhost or staging URL.

## III. QC -> Hub (READY_FOR_MERGE)
* **Required Manifest:**
  * `validation_report_path`: Path to the Nerd's report.
  * `verdict`: PASS or FAIL.
