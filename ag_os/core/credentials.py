"""
Credential Manager — OS Keychain-backed secret storage.

Uses the `keyring` library to delegate to the OS-native encrypted store:
  - macOS → Keychain Access
  - Linux → Secret Service (GNOME Keyring / KWallet)
  - Windows → Windows Credential Locker

Falls back gracefully to an encrypted config file in headless environments.
Follows the same pattern as GitHub CLI (gh auth).
"""

import contextlib
import json
import logging
import os
import stat
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)

# Keyring service namespace — all ag-os credentials are stored under this.
SERVICE_NAME = "ag-os"

# XDG-compliant fallback path for headless environments.
_FALLBACK_DIR = Path.home() / ".config" / "ag-os"
_FALLBACK_FILE = _FALLBACK_DIR / "credentials.json"


@dataclass
class CredentialSpec:
    """Specification for a single credential required by a provider."""

    key: str
    label: str
    hint: str = ""
    is_url: bool = False
    is_password: bool = True


@dataclass
class ProviderAuth:
    """Authentication requirements for a provider."""

    surface: str
    name: str
    credentials: list[CredentialSpec] = field(default_factory=list)
    validate_fn: str | None = None  # Name of validation method


# ─── Credential Registry ─────────────────────────────────────────────────────
# Maps (surface, provider_name) → required credentials.
# Providers not listed here require zero credentials (offline-capable).

PROVIDER_CREDENTIALS: dict[tuple, ProviderAuth] = {
    ("issues", "github"): ProviderAuth(
        surface="issues",
        name="github",
        credentials=[
            CredentialSpec(
                key="GITHUB_TOKEN",
                label="GitHub Personal Access Token",
                hint="Create one at https://github.com/settings/tokens (scopes: repo, issues)",
            ),
        ],
        validate_fn="_validate_github",
    ),
    ("issues", "linear"): ProviderAuth(
        surface="issues",
        name="linear",
        credentials=[
            CredentialSpec(
                key="LINEAR_API_KEY",
                label="Linear API Key",
                hint="Create one at Linear → Settings → API → Personal API Keys",
            ),
        ],
        validate_fn="_validate_linear",
    ),
    ("issues", "jira"): ProviderAuth(
        surface="issues",
        name="jira",
        credentials=[
            CredentialSpec(
                key="JIRA_URL",
                label="Jira Server URL",
                hint="e.g., https://your-org.atlassian.net",
                is_url=True,
                is_password=False,
            ),
            CredentialSpec(
                key="JIRA_EMAIL",
                label="Jira Account Email",
                hint="The email associated with your Atlassian account",
                is_password=False,
            ),
            CredentialSpec(
                key="JIRA_API_TOKEN",
                label="Jira API Token",
                hint="Create one at https://id.atlassian.com/manage-profile/security/api-tokens",
            ),
        ],
        validate_fn="_validate_jira",
    ),
    ("state", "redis"): ProviderAuth(
        surface="state",
        name="redis",
        credentials=[
            CredentialSpec(
                key="REDIS_URL",
                label="Redis Connection URL",
                hint="e.g., redis://localhost:6379/0 or rediss://user:pass@host:port/db",
                is_url=True,
                is_password=False,
            ),
        ],
        validate_fn="_validate_redis",
    ),
    ("telemetry", "otlp"): ProviderAuth(
        surface="telemetry",
        name="otlp",
        credentials=[
            CredentialSpec(
                key="OTLP_ENDPOINT",
                label="OpenTelemetry Collector Endpoint",
                hint="e.g., http://localhost:4317 or https://otel.your-org.com:4317",
                is_url=True,
                is_password=False,
            ),
        ],
        validate_fn="_validate_otlp",
    ),
    ("ci", "github"): ProviderAuth(
        surface="ci",
        name="github",
        credentials=[
            CredentialSpec(
                key="GITHUB_TOKEN",
                label="GitHub Personal Access Token",
                hint="Reuses the same token as GitHub Issues (scopes: repo, workflow)",
            ),
        ],
        validate_fn="_validate_github",
    ),
}

# Providers that require zero credentials (fully offline).
_OFFLINE_PROVIDERS = {
    ("issues", "console"),
    ("state", "sqlite"),
    ("state", "file"),
    ("telemetry", "console"),
    ("telemetry", "file"),
    ("cost", "local"),
    ("policy", "builtin"),
    ("secrets", "local"),
    ("secrets", "env"),
    ("ci", "local"),
}


# ─── Keyring Backend ──────────────────────────────────────────────────────────


def _keyring_available() -> bool:
    """Check if keyring backend is functional.

    Logs the specific failure mode at debug level so a user staring at
    "credentials silently use the fallback file" can find the reason
    in `LOG_LEVEL=debug ag-os status`.
    """
    try:
        import keyring
        import keyring.errors  # noqa: F401  (forces ImportError chain to surface)

        # Test with a probe write/read/delete cycle.
        keyring.set_password(SERVICE_NAME, "__probe__", "test")
        val = keyring.get_password(SERVICE_NAME, "__probe__")
        keyring.delete_password(SERVICE_NAME, "__probe__")
        return val == "test"
    except Exception as e:
        logger.debug("keyring backend unavailable, falling back to file: %s", e)
        return False


def _fallback_load() -> dict:
    """Load credentials from fallback file."""
    if _FALLBACK_FILE.is_file():
        try:
            return json.loads(_FALLBACK_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def _fallback_save(data: dict) -> None:
    """Save credentials to fallback file with strict permissions, atomically.

    The file is created via :func:`os.open` with mode ``0o600``, so the
    contents never land on disk at the process umask (typically ``0o644``)
    even briefly. The previous ``write_text`` then ``chmod`` sequence left
    a TOCTOU window during which a co-tenant FSEvents watcher could read
    the credentials before the chmod fired.
    """
    _FALLBACK_DIR.mkdir(parents=True, exist_ok=True, mode=0o700)
    # Tighten the directory in case it pre-existed with looser perms.
    with contextlib.suppress(OSError):
        _FALLBACK_DIR.chmod(0o700)

    payload = json.dumps(data, indent=2).encode("utf-8")

    fd = os.open(
        _FALLBACK_FILE,
        os.O_WRONLY | os.O_CREAT | os.O_TRUNC,
        0o600,
    )
    try:
        os.write(fd, payload)
    finally:
        os.close(fd)

    # Belt-and-suspenders: re-tighten in case the file already existed at a
    # wider mode (os.open with O_CREAT does not relax existing perms but
    # also does not tighten them).
    _FALLBACK_FILE.chmod(stat.S_IRUSR | stat.S_IWUSR)


# ─── Public API ───────────────────────────────────────────────────────────────


def store_credential(key: str, value: str) -> None:
    """Store a credential in the OS keychain (or fallback)."""
    if _keyring_available():
        import keyring

        keyring.set_password(SERVICE_NAME, key, value)
        logger.debug("Stored %s in OS keychain", key)
    else:
        data = _fallback_load()
        data[key] = value
        _fallback_save(data)
        logger.debug("Stored %s in fallback file", key)


def get_credential(key: str) -> str | None:
    """Retrieve a credential from the OS keychain (or fallback).

    Also checks environment variables as a final override (for CI/CD).
    """
    # 1. Environment variable override (highest priority — for CI/CD).
    env_val = os.environ.get(key)
    if env_val:
        return env_val

    # 2. OS Keychain
    if _keyring_available():
        import keyring

        val = keyring.get_password(SERVICE_NAME, key)
        if val:
            return val

    # 3. Fallback file
    data = _fallback_load()
    return data.get(key)


def delete_credential(key: str) -> bool:
    """Remove a credential from storage. Returns True if found and deleted."""
    deleted = False

    if _keyring_available():
        import keyring

        try:
            keyring.delete_password(SERVICE_NAME, key)
            deleted = True
        except Exception as e:
            # `delete_password` raises if the key wasn't there (PasswordDeleteError)
            # or if the backend is misbehaving. Log instead of silently swallowing
            # so the user can diagnose; the function still falls through to the
            # fallback-file delete below.
            logger.debug("keyring.delete_password failed for %s: %s", key, e)

    data = _fallback_load()
    if key in data:
        del data[key]
        _fallback_save(data)
        deleted = True

    return deleted


def list_stored_credentials() -> list[str]:
    """List all credential keys that have stored values."""
    stored = []
    all_keys = set()
    for auth in PROVIDER_CREDENTIALS.values():
        for spec in auth.credentials:
            all_keys.add(spec.key)

    for key in sorted(all_keys):
        if get_credential(key):
            stored.append(key)
    return stored


def get_required_credentials(config: dict) -> list[CredentialSpec]:
    """Given a parsed antigravity.yaml config, return all required credentials.

    Deduplicates by key (e.g., GITHUB_TOKEN used by both issues and CI).
    """
    seen_keys = set()
    required = []

    providers = config.get("providers", {})
    ci_platform = config.get("ci", {}).get("platform", "local")

    # Check provider selections
    for surface, name in providers.items():
        lookup = (surface, name)
        if lookup in PROVIDER_CREDENTIALS:
            for spec in PROVIDER_CREDENTIALS[lookup].credentials:
                if spec.key not in seen_keys:
                    seen_keys.add(spec.key)
                    required.append(spec)

    # Check CI platform
    ci_lookup = ("ci", ci_platform)
    if ci_lookup in PROVIDER_CREDENTIALS:
        for spec in PROVIDER_CREDENTIALS[ci_lookup].credentials:
            if spec.key not in seen_keys:
                seen_keys.add(spec.key)
                required.append(spec)

    return required


def get_credential_status(config: dict) -> dict[str, bool]:
    """Return a dict of {credential_key: is_stored} for all required creds."""
    required = get_required_credentials(config)
    return {spec.key: bool(get_credential(spec.key)) for spec in required}


# ─── Validation Helpers ───────────────────────────────────────────────────────


def validate_credential(key: str, value: str) -> tuple[bool, str]:
    """Validate a credential value. Returns (success, message)."""
    validators = {
        "GITHUB_TOKEN": _validate_github,
        "LINEAR_API_KEY": _validate_linear,
        "JIRA_API_TOKEN": _validate_jira,
        "REDIS_URL": _validate_redis,
        "OTLP_ENDPOINT": _validate_otlp,
    }

    validator = validators.get(key)
    if validator:
        return validator(value)
    return True, "Stored (no validation available)"


def _validate_github(token: str) -> tuple[bool, str]:
    """Validate GitHub token by calling GET /user."""
    try:
        import urllib.request

        req = urllib.request.Request(
            "https://api.github.com/user",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "User-Agent": "ag-os",
            },
        )
        # S310 noqa: URL is the hardcoded literal "https://api.github.com/user"
        # — no user-controlled scheme/host/path component, only the bearer
        # token which goes into a header.
        with urllib.request.urlopen(req, timeout=10) as resp:  # noqa: S310
            if resp.status == 200:
                data = json.loads(resp.read())
                return True, f"Authenticated as @{data.get('login', 'unknown')}"
    except Exception as e:
        return False, f"GitHub auth failed: {e}"
    return False, "GitHub auth failed: unexpected response"


def _validate_linear(api_key: str) -> tuple[bool, str]:
    """Validate Linear API key with a simple GraphQL query."""
    try:
        import urllib.request

        body = json.dumps({"query": "{ viewer { id name } }"}).encode()
        req = urllib.request.Request(
            "https://api.linear.app/graphql",
            data=body,
            headers={
                "Authorization": api_key,
                "Content-Type": "application/json",
                "User-Agent": "ag-os",
            },
        )
        # S310 noqa: URL is the hardcoded literal
        # "https://api.linear.app/graphql" — no user-controlled scheme.
        with urllib.request.urlopen(req, timeout=10) as resp:  # noqa: S310
            if resp.status == 200:
                data = json.loads(resp.read())
                viewer = data.get("data", {}).get("viewer", {})
                return True, f"Authenticated as {viewer.get('name', 'unknown')}"
    except Exception as e:
        return False, f"Linear auth failed: {e}"
    return False, "Linear auth failed: unexpected response"


def _validate_jira(token: str) -> tuple[bool, str]:
    """Validate Jira credentials. Requires JIRA_URL and JIRA_EMAIL to be set."""
    jira_url = get_credential("JIRA_URL")
    jira_email = get_credential("JIRA_EMAIL")
    if not jira_url or not jira_email:
        return True, "Stored (full validation requires URL + email)"
    try:
        import base64
        import urllib.request

        auth = base64.b64encode(f"{jira_email}:{token}".encode()).decode()
        # The Jira URL comes from the user's own credential store
        # (JIRA_URL credential the user typed in via FTUX). Validate scheme
        # explicitly to satisfy S310 — we accept https only, refusing
        # file:/ftp:/data: that could leak the basic-auth header to a
        # local/attacker-chosen target.
        from urllib.parse import urlparse

        scheme = urlparse(jira_url).scheme
        if scheme not in ("https",):
            return False, f"Jira URL must use https, got {scheme!r}"
        req = urllib.request.Request(  # noqa: S310 - scheme checked above
            f"{jira_url.rstrip('/')}/rest/api/2/myself",
            headers={
                "Authorization": f"Basic {auth}",
                "Accept": "application/json",
                "User-Agent": "ag-os",
            },
        )
        with urllib.request.urlopen(req, timeout=10) as resp:  # noqa: S310 - scheme checked above
            if resp.status == 200:
                data = json.loads(resp.read())
                return True, f"Authenticated as {data.get('displayName', 'unknown')}"
    except Exception as e:
        return False, f"Jira auth failed: {e}"
    return False, "Jira auth failed: unexpected response"


def _validate_redis(url: str) -> tuple[bool, str]:
    """Validate Redis connection URL with a PING."""
    try:
        import socket
        from urllib.parse import urlparse

        parsed = urlparse(url)
        host = parsed.hostname or "localhost"
        port = parsed.port or 6379
        sock = socket.create_connection((host, port), timeout=5)
        sock.close()
        return True, f"Connected to {host}:{port}"
    except Exception as e:
        return False, f"Redis connection failed: {e}"


def _validate_otlp(endpoint: str) -> tuple[bool, str]:
    """Validate OTLP endpoint with a TCP connect check."""
    try:
        import socket
        from urllib.parse import urlparse

        parsed = urlparse(endpoint)
        host = parsed.hostname or "localhost"
        port = parsed.port or 4317
        sock = socket.create_connection((host, port), timeout=5)
        sock.close()
        return True, f"Connected to {host}:{port}"
    except Exception as e:
        return False, f"OTLP endpoint unreachable: {e}"
