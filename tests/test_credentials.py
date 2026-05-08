"""Tests for the credential management system."""

import os
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
