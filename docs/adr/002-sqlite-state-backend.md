# ADR-002: SQLite as Default State Backend

**Status**: Accepted
**Date**: 2024-02-10
**Decision Makers**: Daniel Manzela

## Context

The governance kernel requires a persistent state store for the Flight
Recorder and Dream Report archives. Options considered: SQLite,
PostgreSQL, Redis, flat-file JSON.

## Decision

SQLite in WAL mode with a 30-second busy_timeout is the default and
only built-in state backend. Other backends are available through the
provider registry plugin system.

## Rationale

- **Zero infrastructure**: No server process, no Docker container, no
  network configuration. A single file on disk.
- **WAL mode**: Enables concurrent readers with a single writer, which
  is sufficient for the daemon + CLI access pattern.
- **Portability**: SQLite ships with Python's standard library. Zero
  additional dependencies.
- **Performance**: Sub-millisecond reads for the telemetry volumes
  expected (thousands of records, not millions).

## Consequences

- Multi-process write contention is handled by SQLite's built-in busy
  handler (30s timeout), not application-level locking.
- Users requiring higher concurrency must configure an external state
  provider (e.g., PostgreSQL via the registry).
- Database file must be backed up manually (no built-in replication).
