# Rule 07: Telemetry & Evolution
1. **Friction Logging**: If a task fails validation or enters a loop (count > 2), you MUST append a row to `docs/SDLC_Friction_Log.md`.
2. **Format**: `| Date | Trace ID | Loop Count | Error Summary | Root Cause |`
3. **Evolution**: If a rule causes repeated failures, the Architect must propose a Governance Change Request (GCR).
