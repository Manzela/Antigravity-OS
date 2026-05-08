# Governance

This document describes the governance model for Antigravity OS.

## Roles

### Maintainers

Maintainers are the core team responsible for the project's technical
direction, release management, and community stewardship. They have
write access to the repository and final say on architectural decisions.

Current maintainers are listed in [MAINTAINERS.md](MAINTAINERS.md).

### Contributors

Contributors submit changes via pull requests. All contributions are
reviewed by at least one maintainer before merging.

### Users

Users interact with the project through issues, discussions, and the
CLI/MCP interfaces. Their feedback drives the roadmap.

## Decision Making

- **Lazy consensus**: Proposals are accepted if no maintainer objects
  within 72 hours of the PR being marked as ready for review.
- **Formal vote**: Architectural changes (new core modules, breaking API
  changes, new dependencies) require explicit approval from at least
  two maintainers.
- **ADRs**: All significant decisions are recorded as Architecture
  Decision Records in `docs/adr/`.

## Releases

- Releases follow [Semantic Versioning 2.0.0](https://semver.org/).
- Release candidates are tagged from `main` and tested for at least
  48 hours before promotion to stable.
- Security patches are released out-of-band as needed.

## Conflict Resolution

If consensus cannot be reached, the project lead (listed first in
MAINTAINERS.md) has final decision authority. This authority is
exercised rarely and only after good-faith discussion.

## Code of Conduct

All participants are bound by the project's
[Code of Conduct](CODE_OF_CONDUCT.md).
