"""Tests for the Dream Daemon module."""

import json
from unittest.mock import patch

from ag_os.core.daemon import DreamDaemon, get_daemon_status, uninstall_service


class TestDreamDaemon:
    """Validate daemon initialization and configuration."""

    def test_init_default_interval(self):
        d = DreamDaemon(config={})
        assert d._interval_hours == 6
        assert d._auto_prune is True

    def test_init_custom_interval(self):
        d = DreamDaemon(config={"dreaming": {"schedule_interval_hours": 12, "auto_prune": False}})
        assert d._interval_hours == 12
        assert d._auto_prune is False

    def test_initial_state(self):
        d = DreamDaemon(config={})
        assert d._running is False
        assert d._cycle_count == 0


class TestGetDaemonStatus:
    """Validate daemon health checking."""

    def test_status_when_not_running(self, tmp_path):
        """Status returns running=False when no PID file exists."""
        with (
            patch("ag_os.core.daemon._PID_FILE", tmp_path / "nonexistent.pid"),
            patch("ag_os.core.daemon._HEALTH_FILE", tmp_path / "nonexistent.health"),
        ):
            status = get_daemon_status()

        assert status["running"] is False
        assert status["healthy"] is False
        assert status["pid"] is None

    def test_status_with_stale_pid(self, tmp_path):
        """Status returns running=False when PID file contains dead process."""
        pid_file = tmp_path / "daemon.pid"
        pid_file.write_text("999999999")  # Very unlikely to be a real PID

        with (
            patch("ag_os.core.daemon._PID_FILE", pid_file),
            patch("ag_os.core.daemon._HEALTH_FILE", tmp_path / "nonexistent.health"),
        ):
            status = get_daemon_status()

        assert status["running"] is False

    def test_status_reads_health_file(self, tmp_path):
        """Status reads cycle count from health file."""
        health_file = tmp_path / "daemon.health"
        health_data = {
            "last_tick": "2026-05-08T10:00:00+00:00",
            "cycle_count": 42,
            "pid": 12345,
            "interval_hours": 6,
        }
        health_file.write_text(json.dumps(health_data))

        with (
            patch("ag_os.core.daemon._PID_FILE", tmp_path / "nonexistent.pid"),
            patch("ag_os.core.daemon._HEALTH_FILE", health_file),
        ):
            status = get_daemon_status()

        assert status["cycle_count"] == 42
        assert status["last_tick"] == "2026-05-08T10:00:00+00:00"


class TestUninstallService:
    """Validate service uninstallation."""

    def test_uninstall_when_no_service(self, tmp_path):
        """Returns None when no service files exist."""
        with (
            patch("ag_os.core.daemon._LAUNCHD_PLIST", tmp_path / "nonexistent.plist"),
            patch("ag_os.core.daemon._SYSTEMD_SERVICE", tmp_path / "nonexistent.service"),
        ):
            result = uninstall_service()
        assert result is None

    def test_uninstall_removes_plist(self, tmp_path):
        """Removes launchd plist when it exists."""
        plist = tmp_path / "test.plist"
        plist.write_text("<plist>test</plist>")

        with (
            patch("ag_os.core.daemon._LAUNCHD_PLIST", plist),
            patch("ag_os.core.daemon._SYSTEMD_SERVICE", tmp_path / "nonexistent.service"),
        ):
            result = uninstall_service()

        assert result == str(plist)
        assert not plist.exists()
