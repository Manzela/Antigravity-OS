# Security Policy

## Supported Versions

| Version | Supported |
|:---|:---|
| 1.3.x | Yes |
| 1.2.x | Yes |
| 1.1.x | Yes |
| 1.0.x | Yes |

## Reporting a Vulnerability

**Do not open a public issue for security vulnerabilities.**

Instead, please report security issues by emailing:

**security@antigravity-os.dev**

Include:

- A description of the vulnerability.
- Steps to reproduce.
- The potential impact.
- Any suggested fixes (optional).

We will acknowledge receipt within 48 hours and provide a detailed response
within 7 business days. We will work with you to understand the issue and
coordinate a fix before any public disclosure.

## Scope

The following areas are in scope:

- The `ag_os` Python package and its providers.
- The `ag-os` CLI tool.
- Configuration parsing (YAML injection, path traversal).
- Credential storage (OS Keychain via `keyring`, fallback file).
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
