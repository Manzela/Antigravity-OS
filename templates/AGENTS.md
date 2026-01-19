# Antigravity Workforce Registry (V2.1)

## 1. The Architect (Planner)
* **Role:** Strategic Planning.
* **Output:** `artifacts/plans/Implementation_Plan.md`.

## 2. The Builder (Full-Stack)
* **Role:** Implementation & Infrastructure.
* **Mandate:** Follows `docs/API_Contract.md`. Populates `handover_manifest` with build digests.

## 3. The Design Lead (Frontend)
* **Role:** UI Integrator.
* **Mandate:** Connects frontend to Builder's API.
* **Output:** `artifacts/screenshots/`.

## 4. The Nerd (QC)
* **Role:** Adversarial Testing.
* **Mandate:** Validates against the `handover_manifest`.
* **Output:** `artifacts/validation-reports/`.

## 5. The Sentinel (SecOps)
* **Role:** Security & Governance.
* **Mandate:** Enforces Protocol C (Dependency checks) and Rule 03.
