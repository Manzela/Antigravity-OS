# Antigravity OS V3.2 (The Connected Mind)

### **The Operating System for AI-Native Development**

> *"Stop debugging. Start evolving."*

**Antigravity OS** is not just a framework; it is a **Living System**. It is an autonomous, cloud-connected operating environment designed to enforce governance, ensure solvency, and self-heal using Generative AI. 

In V3.2, we have broken the isolation. The system is no longer a local fortress. It is a **Connected Mind**, tethered to Google Cloud for global observability and powered by Gemini Pro for autonomous code repair.

---

## 🚀 The Vision: "Connected & Conscious"

We built Antigravity OS V3.2 on three non-negotiable pillars:

1.  **Identity is Governance:** No more `.env` file chaos. If you are not `@tngshopper.com`, you do not exist. We use Google Cloud Identity and Secret Manager as the single source of truth.
2.  **Telemetry is Truth:** Errors are not just logged; they are traced globally. We pipe every span directly to **Google Cloud Trace** to visualize the heartbeat of the system across distributed architectures.
3.  **Code is Alive:** When the system breaks, it doesn't just crash. It **Consults the Mind**. Using an integrated Vertex AI (Gemini Pro) connection, the Orchestrator analyzes the failure and proposes the exact code fix required to heal the system.

---

## 🏛 System Architecture (V3.2)

### **1. The Identity Layer (Deep Auth)**
*   **Mechanism:** `gcloud` Application Default Credentials (ADC).
*   **Enforcement:** `install.sh` performs a mandatory organizational check (`@tngshopper.com`).
*   **Secret Hydration:** API Keys (`JIRA_TOKEN`, `GEMINI_KEY`) are fetched dynamically from Google Secret Manager at runtime. Zero hardcoded secrets.

### **2. The Nervous System (Observability)**
*   **The Uplink:** A direct conduit using `opentelemetry-exporter-gcp-trace`. No sidecars, no friction. Traces appear instantly in the GCP Console.
*   **The Sentinel (Governance):** An Open Policy Agent (OPA) container that audits every Git commit against strict `rego` policies before code usually leaves your machine.

### **3. The Generative Brain (Self-Healing)**
*   **The Mind:** Integrated `vertexai` client connected to **Gemini Pro 1.5**.
*   **The Reflex:** Upon a test failure, the `orchestrator.py` captures the stack trace, sanitizes it (PII removal), and sends it to the Mind.
*   **The Cure:** The AI returns a precise Python patch to fix the error, turning downtime into uptime.

---

## ⚡️ Quick Start

**Prerequisites:**
1.  **Docker Desktop** (Running)
2.  **Google Cloud SDK** (`gcloud` installed)
3.  **Identity**: You must have a `@tngshopper.com` Google Account.

### **One-Shot Installation**

We have removed the manual config steps. There is only one command:

```bash
./install.sh
```

**What happens next?**
1.  **Auth Check:** The script verifies your `gcloud` identity.
2.  **Hydration:** It pulls production secrets from the Cloud.
3.  **Boot:** It spins up the **Brain** (Redis) and **Sentinel** (OPA) containers.
4.  **Wiring:** It installs the `pre-push` hook that guards your repo.

---

## 🛠 Development Workflow

### **1. Write Code**
Work as usual. Focus on features, not plumbing.

### **2. Verify Locally**
The system is always watching.
```bash
# Run the verification suite manually if needed
python3 .agent/runtime/orchestrator.py
```

### **3. Push to Deploy**
The magic happens here.
```bash
git push origin feature/my-new-idea
```
The **Global Pre-Push Hook** intercepts the push:
1.  **Governance Check:** OPA validates your changes.
2.  **Build & Test:** The suite runs with OTel instrumentation.
3.  **Trace Export:** Performance data is sent to Google Cloud Trace.
4.  **Generative Heal:** If it fails, Gemini analyzes why and tells you how to fix it.

---

## 📊 Observability

View your system's performance in real-time:
*   [**Google Cloud Trace**](https://console.cloud.google.com/traces) - Distributed Request Tracing
*   [**Secret Manager**](https://console.cloud.google.com/security/secret-manager) - Credential Governance

---

## © License & Credits
**Antigravity OS** is a proprietary system of the TNG Infrastructure Team.
*concept by Manzela | architecture by Antigravity AI*
