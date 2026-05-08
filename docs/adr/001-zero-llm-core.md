# ADR-001: Zero-LLM Core Architecture

**Status**: Accepted
**Date**: 2024-01-15
**Decision Makers**: Daniel Manzela

## Context

The governance kernel must analyze agent telemetry and produce
actionable recommendations. The question is whether to use LLM
inference for this analysis or pure deterministic heuristics.

## Decision

The core governance kernel has zero LLM dependencies. All analysis
(friction scanning, patch synthesis, success pattern extraction) uses
deterministic heuristic algorithms operating on structured telemetry
data.

## Rationale

- **Determinism**: Governance decisions must be reproducible. LLM
  outputs are inherently non-deterministic.
- **Cost**: Zero inference cost means the system can run continuously
  without budget impact.
- **Portability**: No API keys, no cloud dependencies, no vendor
  lock-in. Works offline and air-gapped.
- **Trust**: Operators can audit every code path that produces a
  governance recommendation.

## Consequences

- The system cannot perform natural language reasoning about novel
  failure modes not covered by its archetype classifiers.
- New friction archetypes require explicit code additions (which is
  intentional — governance changes should be deliberate).
- AI agents that consume Dream Reports can use their own LLM
  capabilities to interpret the structured output.
