# ADR-004: Risk-Based Patch Application Gates

**Status**: Accepted
**Date**: 2025-05-08
**Decision Makers**: Daniel Manzela

## Context

The DreamEngine generates governance patches (threshold adjustments,
new rules, config changes). The question is whether these should be
applied automatically or require human review.

## Decision

Patches are classified into three risk tiers:

- **LOW** (THRESHOLD_ADJUSTMENT): Auto-applicable without approval.
- **MEDIUM** (CONFIG_CHANGE): Auto-applicable with notification.
- **HIGH** (NEW_RULE): Mandatory human approval before application.

## Rationale

- **Safety**: New governance rules have the highest blast radius and
  must not be applied without human review.
- **Efficiency**: Low-risk threshold tuning (e.g., adjusting
  `max_loop_count`) is safe to automate and provides immediate value.
- **Auditability**: All patch applications (accepted or rejected) are
  logged to `~/.antigravity/patch_audit.yaml` for governance
  traceability.

## Consequences

- `ag-os dream --apply` only auto-applies LOW-risk patches by default.
- The audit trail grows linearly with patch volume and must be
  periodically reviewed.
- CI/CD pipelines can use `--apply` with `interactive=False` for
  fully automated governance tuning in non-interactive environments.
