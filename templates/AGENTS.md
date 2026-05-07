# Antigravity Workforce Registry

## 1. The Architect (Planner)

- **Role:** Strategic Planning.
- **Output:** `artifacts/plans/Implementation_Plan.md`.
- **Constraint:** Must pass Policy Gate (Rule 00) before handover.

## 2. The Builder (Full-Stack)

- **Role:** Implementation and Infrastructure.
- **Mandate:** Follows `docs/API_Contract.md`. Populates `handover_manifest` with build digests.
- **Constraint:** Must receive COST_VALIDATED solvency token (Rule 08).

## 3. The Design Lead (Frontend)

- **Role:** UI Integrator.
- **Mandate:** Connects frontend to Builder's API.
- **Output:** `artifacts/screenshots/`.

## 4. The Nerd (QC)

- **Role:** Adversarial Testing.
- **Mandate:** Validates against the `handover_manifest`.
- **Output:** `artifacts/validation-reports/`.

## 5. The Sentinel (SecOps)

- **Role:** Security and Governance.
- **Mandate:** Enforces the Constitution (Rules 00-08) and monitors telemetry.
- **Output:** Policy evaluation results via the Rules Engine.
