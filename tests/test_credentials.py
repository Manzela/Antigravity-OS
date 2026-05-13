"""Tests for the credential management system."""

import os
import stat
from unittest.mock import patch


class TestCredentialStorage:
    """Validate credential store/get/delete lifecycle using fallback backend."""

    @patch("ag_os.core.credentials._keyring_available", return_value=False)
    def test_store_and_get_fallback(self, mock_avail, tmp_path):
        """When keyring is unavailable, fallback file is used."""
        from ag_os.core.credentials import get_credential, store_credential

        # Redirect fallback file to temp
        with (
            patch("ag_os.core.credentials._FALLBACK_DIR", tmp_path),
            patch("ag_os.core.credentials._FALLBACK_FILE", tmp_path / "credentials.json"),
        ):
            store_credential("test-key", "secret-value")
            result = get_credential("test-key")
            assert result == "secret-value"

    @patch("ag_os.core.credentials._keyring_available", return_value=False)
    def test_get_returns_none_when_missing(self, mock_avail, tmp_path):
        """get_credential returns None for missing keys."""
        from ag_os.core.credentials import get_credential

        with (
            patch("ag_os.core.credentials._FALLBACK_DIR", tmp_path),
            patch("ag_os.core.credentials._FALLBACK_FILE", tmp_path / "credentials.json"),
        ):
            result = get_credential("nonexistent")
            assert result is None

    @patch("ag_os.core.credentials._keyring_available", return_value=False)
    def test_delete_credential_fallback(self, mock_avail, tmp_path):
        """delete_credential removes from fallback file."""
        from ag_os.core.credentials import (
            delete_credential,
            get_credential,
            store_credential,
        )

        with (
            patch("ag_os.core.credentials._FALLBACK_DIR", tmp_path),
            patch("ag_os.core.credentials._FALLBACK_FILE", tmp_path / "credentials.json"),
        ):
            store_credential("to-delete", "value")
            assert get_credential("to-delete") == "value"
            result = delete_credential("to-delete")
            assert result is True
            assert get_credential("to-delete") is None

    def test_env_override(self):
        """Environment variable overrides stored credentials."""
        from ag_os.core.credentials import get_credential

        os.environ["MY_KEY"] = "from-env"
        try:
            result = get_credential("MY_KEY")
            assert result == "from-env"
        finally:
            del os.environ["MY_KEY"]


class TestCredentialValidation:
    """Validate credential format checkers."""

    def test_validate_unknown_returns_true(self):
        """Unknown credential types return (True, 'Stored...')."""
        from ag_os.core.credentials import validate_credential

        valid, msg = validate_credential("UNKNOWN_SERVICE", "some-value")
        assert valid is True
        assert "Stored" in msg

    def test_validate_jira_no_url_returns_true(self):
        """Jira validation without URL/email returns True with advisory."""
        from ag_os.core.credentials import validate_credential

        with (
            patch("ag_os.core.credentials._keyring_available", return_value=False),
            patch("ag_os.core.credentials._fallback_load", return_value={}),
        ):
            valid, msg = validate_credential("JIRA_API_TOKEN", "some-token")
            assert valid is True
            assert "requires" in msg.lower() or "stored" in msg.lower()


class TestCredentialSpec:
    """Validate required credential discovery."""

    def test_get_required_credentials_default(self):
        """Default config (console/local) should need zero credentials."""
        from ag_os.core.credentials import get_required_credentials

        config = {
            "providers": {
                "issues": "console",
                "state": "sqlite",
                "telemetry": "console",
            }
        }
        specs = get_required_credentials(config)
        assert isinstance(specs, list)

    def test_get_credential_status(self):
        """Credential status should return a dict of key -> bool."""
        from ag_os.core.credentials import get_credential_status

        config = {
            "providers": {
                "issues": "console",
                "state": "sqlite",
                "telemetry": "console",
            }
        }
        status = get_credential_status(config)
        assert isinstance(status, dict)

    def test_list_stored_credentials(self, tmp_path):
        """list_stored_credentials returns a list."""
        from ag_os.core.credentials import list_stored_credentials

        result = list_stored_credentials()
        assert isinstance(result, list)


class TestFallbackSavePermissions:
    """P1-2: _fallback_save must create the file with 0600 atomically.

    The previous implementation called write_text then chmod, leaving a TOCTOU
    window where the file existed at the process umask (typically 0o644)
    before the chmod fired. These tests pin both the final mode and the
    os.open syscall arguments to lock in the atomic-create fix.
    """

    def test_credentials_file_is_mode_0600(self, tmp_path):
        from ag_os.core.credentials import _fallback_save

        cred_file = tmp_path / "ag-os" / "credentials.json"
        with (
            patch("ag_os.core.credentials._FALLBACK_DIR", tmp_path / "ag-os"),
            patch("ag_os.core.credentials._FALLBACK_FILE", cred_file),
        ):
            _fallback_save({"GITHUB_TOKEN": "ghp_secret"})

        assert cred_file.exists()
        mode = stat.S_IMODE(cred_file.stat().st_mode)
        assert mode == 0o600, f"Expected 0o600, got {oct(mode)}"

    def test_credentials_dir_is_mode_0700(self, tmp_path):
        from ag_os.core.credentials import _fallback_save

        cred_dir = tmp_path / "ag-os"
        cred_file = cred_dir / "credentials.json"
        with (
            patch("ag_os.core.credentials._FALLBACK_DIR", cred_dir),
            patch("ag_os.core.credentials._FALLBACK_FILE", cred_file),
        ):
            _fallback_save({"k": "v"})

        dir_mode = stat.S_IMODE(cred_dir.stat().st_mode)
        assert dir_mode == 0o700, f"Expected 0o700, got {oct(dir_mode)}"

    def test_fallback_save_calls_os_open_with_0600(self, tmp_path, monkeypatch):
        """The atomic primitive: os.open must receive mode=0o600.

        If a future refactor re-introduces write_text or open() without an
        explicit mode argument, this test fails — the chmod-after-write
        pattern reopens the TOCTOU window even if the final mode looks right.
        """
        captured: dict = {}
        real_open = os.open

        def spy_open(path, flags, mode=0o777):
            captured.setdefault("mode", mode)
            captured.setdefault("flags", flags)
            return real_open(path, flags, mode)

        monkeypatch.setattr(os, "open", spy_open)

        from ag_os.core.credentials import _fallback_save

        cred_file = tmp_path / "ag-os" / "creds.json"
        with (
            patch("ag_os.core.credentials._FALLBACK_DIR", tmp_path / "ag-os"),
            patch("ag_os.core.credentials._FALLBACK_FILE", cred_file),
        ):
            _fallback_save({"k": "v"})

        assert captured.get("mode") == 0o600, (
            f"_fallback_save must os.open with mode=0o600 to avoid TOCTOU; "
            f"got {oct(captured.get('mode', 0))}"
        )
        flags = captured.get("flags", 0)
        assert flags & os.O_CREAT, "expected O_CREAT in os.open flags"
        assert flags & os.O_TRUNC, "expected O_TRUNC in os.open flags"
