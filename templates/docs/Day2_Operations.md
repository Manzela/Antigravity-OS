# Antigravity OS: Day 2 Operations Manual

## 1. Creating New Projects

This repository is the governance kernel. To start a new Antigravity project:

1. Clone or fork this repository.
2. Run `ag-os init` to configure the governance layer.
3. Your new project immediately inherits the Constitution (Rules 00-08),
   Flight Recorder state machine, and Cost Guard solvency gate.

## 2. Updating Governance Rules

Antigravity rules evolve. To sync your project with the latest release:

1. Run `./templates/scripts/sync_governance.sh`.
2. Commit the updated rules.
3. Your Constitution is now aligned with the latest enterprise standard.

## 3. Local Enforcement

Antigravity OS installs a `pre-push` Git hook during `ag-os init`.

- **Behavior:** Runs `ag-os check` before every push.
- **Block:** If the solvency gate fails, the push is rejected.
- **Override:** Run `git push --no-verify` for emergency hotfixes.
- Every override is logged to `docs/SDLC_Friction_Log.md` (Rule 07).

## 4. Emergency Overrides

If governance gates are blocking a critical hotfix:

- **Git Hook:** `git push --no-verify`
- **Cost Guard:** Increase `monthly_cap` in `antigravity.yaml` or set
  `AG_OS_MONTHLY_CAP` environment variable.
- **Policy Gate:** All overrides are recorded by the Flight Recorder.
