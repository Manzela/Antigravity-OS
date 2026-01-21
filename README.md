Personal Note: 
I am pleased to announce the official release of Antigravity OS, an infrastructure framework designed to automate and secure the software development lifecycle. My goal is to provide a reliable foundation for autonomous development through integrated governance and advanced observability.

This project focuses on four core architectural areas:

Standardized Observability: I have established a universal telemetry architecture to ensure consistent logging across all platforms. Every system event captures comprehensive metadata to ensure zero data loss, even during critical failures.

Automated Self-Healing: The system includes a flight recorder that automatically captures state and logs during runtime failures. It uses generative analysis to propose fixes and includes smart-rollback capabilities to maintain branch stability.

Infrastructure Security: To protect system integrity, I have implemented a multi-layered locking mechanism. This combines Open Policy Agent governance with AI directives to prevent unauthorized changes to core security policies.

Cost and Compliance Guardrails: Integrated sentinel scripts provide automated security scanning and cost management. These safety gates ensure all architectural changes meet predefined standards before they are deployed.

I invite you to explore the repository and review the design documentation. I look forward to your feedback as I work to set a new standard for self-healing and observable systems.

# Antigravity OS (V3.5 Enterprise)

"Stop debugging. Start evolving."

Antigravity OS is a governance kernel that transforms your integrated development environment into a deterministic software factory. It is an autonomous, cloud-connected operating environment designed to enforce governance, ensure financial solvency, and facilitate self-healing using Generative AI.

In V3.5, the system transitions from a local isolation model to a Connected Mind architecture, tethered to Google Cloud for global observability and powered by Gemini Pro for autonomous code repair.

## Strategic Highlights (V3.5)

*   **The Invariant Solvency Gate (Rule 08):** Automatically blocks build pipelines if projected cloud infrastructure costs exceed the monthly budget cap defined in the Cost Guard configuration.
*   **Self-Healing CI/CD:** The integration-queue workflow automatically reverts unstable commits and consults Vertex AI to propose precise code fixes, reducing downtime.
*   **Jira Bridge Telemetry:** Automated flight recording creates rich tickets in Jira. The system handles deduplication and performs "Smart Assignment" based on `git blame` data.
*   **Identity as Governance:** Eliminates local configuration drift. Secrets and API keys are hydrated dynamically from Google Secret Manager at runtime, ensuring zero hardcoded secrets.

## System Architecture

Antigravity OS operates on three foundational pillars:

| Pillar | Component | Function |
| :--- | :--- | :--- |
| **1. The Sentinel** | Open Policy Agent (OPA) | Audits every commit against strict Rego policies before code leaves the local machine. |
| **2. The Brain** | Redis 7.2 | Maintains state leases, budget locks, and the "Flight Recorder" session data for distributed state management. |
| **3. The Uplink** | OTel + Jira Bridge | Pipes performance spans to Google Cloud Trace and creates friction logs in Jira and Confluence. |

## Directory Structure

The OS injects a standardized directory structure into the repository to enforce separation of concerns:

```plaintext
.
├── .agent/                 # The Kernel (Hidden System Logic)
│   ├── policies/           # Rego governance files (e.g., governance.rego)
│   ├── sentinel/           # Cost Guard and Security logic
│   └── observability/      # Jira Bridge and Telemetry connectors
├── artifacts/              # Mandatory output directories (Plans, Reports)
├── docs/                   # The Constitution (Rules 00-08)
├── templates/              # Standardized patterns for Agents
├── install.sh              # System hydration script
└── docker-compose.yml      # Container orchestration for Brain and Sentinel
```

## Installation and Setup

### Prerequisites

*   **Docker Desktop** (Active/Running)
*   **Google Cloud SDK** (`gcloud` authenticated)
*   **Python 3.10+**
*   **Identity:** Access to an authorized Google Identity (e.g., `@tngshopper.com`) or a valid `GCP_SA_KEY`.

### Quick Start / One-Shot Hydration

To setup or install Antigravity OS in any new or existing Google Antigravity IDE project, execute the following command:

```bash
# One-shot Install via Curl
curl -sSL https://raw.githubusercontent.com/Manzela/Antigravity-OS/main/install.sh | bash
```

*Alternatively, clone the repository and run the local installer:*

```bash
git clone https://github.com/Manzela/Antigravity-OS.git .
chmod +x install.sh
./install.sh
```

### Installation Sequence:

1.  **Authentication Verification:** Verifies the active `gcloud` identity.
2.  **Secret Hydration:** Pulls `GCP_BILLING_ACCOUNT_ID`, `JIRA_API_TOKEN`, and `REDIS_CREDENTIALS` from Google Secret Manager.
3.  **Boot:** Initializes the Brain (Redis) and Sentinel (OPA) containers via Docker Compose.
4.  **Wiring:** Installs the `pre-push` hook that enforces the QA suite on every commit.

## The Constitution (Governance Rules)

Development is strictly governed by the rules located in `.agent/rules/`. Violations result in blocked pushes.

| Rule ID | Name | Enforcement Mechanism |
| :--- | :--- | :--- |
| **Rule 00** | Plan First | Requires a ratified plan in `artifacts/plans/` before code creation. |
| **Rule 02** | Fail Closed | The `pre-push` hook executes `scripts/run_qa.sh` to validate integrity. |
| **Rule 05** | Flight Recorder | Every interaction must log a `trace_id` and `handover_manifest`. |
| **Rule 08** | Economic Safety | The `cost_guard.py` script validates spend against the configured Monthly Cap (Default: $50.00). |

## Operations Manual

### Updating the OS ("The Genetic Update")

Antigravity Rules evolve over time. To synchronize a project with the Master Kernel:

```bash
./scripts/sync_governance.sh
```

**Effect:** Fetches the latest rules from the Master OS repository to ensure compliance with the current Enterprise Standard.

### Emergency Overrides

If the Guardrails block a critical hotfix, the following override protocols exist:

*   **Git Hook:** Execute `git push --no-verify` to bypass local checks.
*   **Cost Guard:** Request a Human Override via Jira.

*Note: All overrides are logged to `docs/SDLC_Friction_Log.md` (Rule 07) for audit purposes.*

## Observability and Debugging

The system runs a Jira Bridge that connects the local environment to the enterprise tracking system.

*   **Automatic Ticket Creation:** Upon build failure, a Jira ticket is created in the designated project (Default: `TNG`).
*   **Deduplication:** The system hashes the error stack trace. If the error repeats, it appends a comment to the existing ticket rather than creating duplicates.
*   **Smart Assignment:** Uses `git blame` to automatically assign the ticket to the developer responsible for the code modification.

### Manual Test Command:
```bash
python3 .agent/observability/jira_bridge.py "Manual Test Alert" "Testing the bridge connection" "TNG"
```

## License and Credits

Antigravity OS is a proprietary system of the TNG Infrastructure Team.

*   **Concept:** Manzela
*   **Architecture:** Manzela
*   **Development:** Antigravity AI
