# ADR-003: Provider Registry Plugin Architecture

**Status**: Accepted
**Date**: 2024-03-01
**Decision Makers**: Daniel Manzela

## Context

The system must support multiple backends for issues (Jira, Linear,
GitHub), telemetry (OTLP, console), state (SQLite, Redis), and
secrets (keyring, Vault). Hard-coding these would create tight
coupling and bloated dependencies.

## Decision

All external integrations are accessed through a provider registry.
Each provider category (state, issues, telemetry, secrets, cost,
policy) has a simple interface. Concrete implementations are
registered at startup and selected via `antigravity.yaml`.

## Rationale

- **Decoupling**: Core modules never import provider-specific
  libraries. They call `get_provider("state", name)`.
- **Optional dependencies**: Users only install what they need. The
  default configuration requires zero optional packages.
- **Testability**: Providers can be mocked or replaced for testing
  without modifying core logic.

## Consequences

- New integrations require implementing a provider interface and
  registering it in the registry module.
- Provider discovery is explicit (no auto-discovery or classpath
  scanning) to maintain deterministic behavior.
- The registry pattern adds one level of indirection compared to
  direct imports.
