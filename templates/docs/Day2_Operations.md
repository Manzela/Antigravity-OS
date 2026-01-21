# Antigravity OS: Day 2 Operations Manual
# How to Distribute, Propagate, and Enforce Governance

## 1. Creating New Projects ("The Golden Template")
This repository is the **Master Kernel**. To start a new Antigravity project:
1.  Go to the GitHub page of this repository.
2.  Click **"Use this template"**.
3.  Clone your new repository.
4.  Run `./install.sh` to hydrate the environment.
    *   *Effect*: Your new project immediately inherits the V3.4.5 Schema, Gates, and Workflows.

## 2. Updating Existing Projects ("The Genetic Update")
Antigravity Rules evolve. To sync your project with the Master Kernel:
1.  Run `./scripts/sync_governance.sh`.
    *   *Effect*: Fetches the latest `rules/*.md` from the Master OS repository.
2.  Commit the changes.
    *   *Why*: This ensures your "Constitution" (Rule 00-08) is always up to date with the Enterprise Standard.

## 3. Local Enforcement ("The Invisible Guardrails")
To prevent bad code from leaving your machine:
1.  Run `./scripts/setup_hooks.sh`.
    *   *Effect*: Installs a `pre-push` Git hook.
    *   *Behavior*: Runs `scripts/run_qa.sh` (ShellCheck + Unit Tests) before every push.
    *   *Block*: If QA fails, the push is rejected.

## 4. Emergency Overrides
If the Guardrails are blocking a critical hotfix:
*   **Git Hook**: Run `git push --no-verify`.
*   **Cost Guard**: Use the `/authorize-overage` command (Manual Human Protocol).
*   **Strict Note**: Every override is logged to `docs/SDLC_Friction_Log.md` (Rule 07).
