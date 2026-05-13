"""Shared test fixtures for the Antigravity OS test suite."""

import pytest

from ag_os.config import load_config


@pytest.fixture()
def default_config():
    """Return the default configuration dict."""
    return load_config()


@pytest.fixture()
def dreams_dir(tmp_path):
    """Return a temporary dreams directory with standard structure."""
    d = tmp_path / "dreams"
    d.mkdir()
    archive = d / "archive"
    archive.mkdir()
    return d
