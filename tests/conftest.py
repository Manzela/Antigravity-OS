"""Shared test fixtures for the Antigravity OS test suite."""

import pytest

from ag_os.config import load_config


@pytest.fixture()
def default_config():
    """Return the default configuration dict."""
    return load_config()


@pytest.fixture()
def dream_engine(default_config):
    """Return a pre-configured DreamEngine instance."""
    from ag_os.core.dreaming import DreamEngine

    return DreamEngine(config=default_config)


@pytest.fixture()
def flight_recorder(default_config):
    """Return a pre-configured FlightRecorder instance."""
    from ag_os.core.flight_recorder import FlightRecorder

    return FlightRecorder(config=default_config)


@pytest.fixture()
def dreams_dir(tmp_path):
    """Return a temporary dreams directory with standard structure."""
    d = tmp_path / "dreams"
    d.mkdir()
    archive = d / "archive"
    archive.mkdir()
    return d
