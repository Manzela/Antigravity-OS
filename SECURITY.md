# Security Policy

## Supported Versions

The latest minor release on PyPI receives security fixes. Older minor
releases are not supported — please upgrade.

| Version | Supported |
|:---|:---|
| 1.4.x | Yes |
| < 1.4 | No  |

## Reporting a Vulnerability

**Do not open a public issue for security vulnerabilities.**

Use GitHub's private vulnerability reporting to send the report
directly to the maintainer with no public visibility:

**[Report a vulnerability](https://github.com/Manzela/Antigravity-OS/security/advisories/new)**

Include:

- A description of the vulnerability.
- Steps to reproduce.
- The potential impact.
- Any suggested fixes (optional).

We aim to acknowledge receipt within 48 hours and provide a detailed
response within 7 business days. We will work with you to understand
the issue and coordinate a fix before any public disclosure.

## Scope

The following areas are in scope:

- The `ag_os` Python package and its providers.
- The `ag-os` CLI tool and MCP server.
- The Dream Daemon background process and service installation.
- Configuration parsing (YAML injection, path traversal).
- Credential storage (OS Keychain via `keyring`, fallback file).
- Patch application and audit trail integrity.
- Secret handling in the secrets provider surface.
- State store integrity (SQLite, Redis).

The following are **out of scope**:

- Third-party cloud provider APIs (report to the respective vendor).
- Vulnerabilities in dependencies (report upstream; we will update pinned versions).

## Disclosure Policy

We follow coordinated disclosure. We request a 90-day disclosure window
from the initial report to allow time for a fix to be developed and released.

## Credit

We credit security researchers who report valid vulnerabilities in our
CHANGELOG and release notes (with permission).
