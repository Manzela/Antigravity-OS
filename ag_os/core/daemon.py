"""
Dream Daemon — Background process for continuous self-improvement.

Runs the DreamEngine on a configurable schedule, persisting learnings
and optionally pruning old reports. Designed for foreground execution
under OS-native process managers (launchd on macOS, systemd on Linux).

Usage:
    ag-os daemon start          # Run in foreground (attach to terminal)
    ag-os daemon install        # Install as OS service
    ag-os daemon uninstall      # Remove OS service
    ag-os daemon status         # Check daemon health
"""

import json
import logging
import os
import signal
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

logger = logging.getLogger("ag_os.daemon")

_AG_DIR = Path.home() / ".antigravity"
_PID_FILE = _AG_DIR / "daemon.pid"
_HEALTH_FILE = _AG_DIR / "daemon.health"
_LOG_FILE = _AG_DIR / "daemon.log"

# Service identifiers
_LAUNCHD_LABEL = "dev.antigravity-os.daemon"
_LAUNCHD_PLIST = Path.home() / "Library" / "LaunchAgents" / f"{_LAUNCHD_LABEL}.plist"
_SYSTEMD_SERVICE = Path.home() / ".config" / "systemd" / "user" / "antigravity-daemon.service"


class DreamDaemon:
    """Background scheduler for the DreamEngine.

    Executes dream cycles at a configurable interval, writes health
    files for liveness monitoring, and handles graceful shutdown via
    SIGTERM/SIGINT.
    """

    def __init__(self, config: dict):
        self._config = config
        dreaming_cfg = config.get("dreaming", {})
        self._interval_hours = dreaming_cfg.get("schedule_interval_hours", 6)
        self._auto_prune = dreaming_cfg.get("auto_prune", True)
        self._running = False
        self._cycle_count = 0

    def run_forever(self) -> None:
        """Main loop — run dream cycles at the configured interval.

        Blocks until SIGTERM/SIGINT is received. Writes PID and health
        files for external monitoring.
        """
        self._setup_logging()
        self._register_signals()
        self._write_pid()
        self._running = True

        interval_seconds = max(self._interval_hours * 3600, 60)
        logger.info(
            "Dream Daemon started (PID %d, interval=%dh)",
            os.getpid(),
            self._interval_hours,
        )

        try:
            while self._running:
                self._tick()
                self._write_health()

                # Sleep in small increments for responsive shutdown
                elapsed = 0
                while elapsed < interval_seconds and self._running:
                    time.sleep(min(10, interval_seconds - elapsed))
                    elapsed += 10
        finally:
            self._cleanup()
            logger.info("Dream Daemon stopped gracefully.")

    def _tick(self) -> None:
        """Execute one dream cycle."""
        from ag_os.core.dreaming import DreamEngine

        self._cycle_count += 1
        logger.info("Dream cycle %d starting...", self._cycle_count)

        try:
            engine = DreamEngine(config=self._config)
            report = engine.dream()
            logger.info(
                "Dream cycle %d complete: %d friction, %d successes, %d patches",
                self._cycle_count,
                report.friction_detected,
                report.successes_detected,
                len(report.proposed_patches),
            )

            if self._auto_prune:
                result = engine.prune()
                if result["deleted_count"] > 0:
                    logger.info(
                        "Pruned %d old reports (%d consolidated)",
                        result["deleted_count"],
                        result["consolidated_count"],
                    )

        except Exception:
            logger.exception("Dream cycle %d failed", self._cycle_count)

    def _setup_logging(self) -> None:
        """Configure structured logging for daemon mode."""
        _AG_DIR.mkdir(parents=True, exist_ok=True)

        handler = logging.FileHandler(_LOG_FILE, encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
        root = logging.getLogger("ag_os")
        root.setLevel(logging.INFO)
        root.addHandler(handler)

        # Also log to stderr for service manager capture
        stderr_handler = logging.StreamHandler(sys.stderr)
        stderr_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        root.addHandler(stderr_handler)

    def _register_signals(self) -> None:
        """Register signal handlers for graceful shutdown."""
        signal.signal(signal.SIGTERM, self._handle_signal)
        signal.signal(signal.SIGINT, self._handle_signal)

    def _handle_signal(self, signum, frame) -> None:
        """Signal handler — set running flag to False for clean exit."""
        sig_name = signal.Signals(signum).name
        logger.info("Received %s, shutting down...", sig_name)
        self._running = False

    def _write_pid(self) -> None:
        """Write PID file."""
        _AG_DIR.mkdir(parents=True, exist_ok=True)
        _PID_FILE.write_text(str(os.getpid()), encoding="utf-8")

    def _write_health(self) -> None:
        """Write health file with last-tick timestamp for liveness checks."""
        health = {
            "last_tick": datetime.now(timezone.utc).isoformat(),
            "cycle_count": self._cycle_count,
            "pid": os.getpid(),
            "interval_hours": self._interval_hours,
        }
        _HEALTH_FILE.write_text(json.dumps(health, indent=2), encoding="utf-8")

    def _cleanup(self) -> None:
        """Remove PID file on shutdown."""
        try:
            _PID_FILE.unlink(missing_ok=True)
        except OSError:
            pass


def get_daemon_status() -> dict:
    """Check whether the daemon is running and healthy.

    Returns a dict with keys: running, healthy, pid, last_tick,
    cycle_count, age_seconds.
    """
    result = {
        "running": False,
        "healthy": False,
        "pid": None,
        "last_tick": None,
        "cycle_count": 0,
        "age_seconds": None,
    }

    # Check PID
    if _PID_FILE.is_file():
        try:
            pid = int(_PID_FILE.read_text().strip())
            os.kill(pid, 0)  # Check if process exists
            result["running"] = True
            result["pid"] = pid
        except (ValueError, ProcessLookupError, PermissionError):
            pass

    # Check health file
    if _HEALTH_FILE.is_file():
        try:
            health = json.loads(_HEALTH_FILE.read_text(encoding="utf-8"))
            result["last_tick"] = health.get("last_tick")
            result["cycle_count"] = health.get("cycle_count", 0)

            if result["last_tick"]:
                last = datetime.fromisoformat(result["last_tick"])
                age = (datetime.now(timezone.utc) - last).total_seconds()
                result["age_seconds"] = age

                # Healthy if last tick within 2x expected interval
                interval = health.get("interval_hours", 6) * 3600
                result["healthy"] = result["running"] and age < (interval * 2)
        except (json.JSONDecodeError, ValueError, OSError):
            pass

    return result


def install_service(config: dict) -> str:
    """Install the daemon as an OS-native service.

    macOS: ~/Library/LaunchAgents/ plist
    Linux: ~/.config/systemd/user/ service unit

    Returns the path to the installed service file.
    """
    import shutil

    ag_os_bin = shutil.which("ag-os")
    if not ag_os_bin:
        # Try venv
        venv_bin = Path(sys.prefix) / "bin" / "ag-os"
        if venv_bin.exists():
            ag_os_bin = str(venv_bin)
        else:
            raise FileNotFoundError("ag-os binary not found. Install with: pip install ag-os")

    if sys.platform == "darwin":
        return _install_launchd(ag_os_bin, config)
    else:
        return _install_systemd(ag_os_bin, config)


def _install_launchd(ag_os_bin: str, config: dict) -> str:
    """Generate and install a macOS LaunchAgent plist."""
    plist = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{_LAUNCHD_LABEL}</string>
    <key>ProgramArguments</key>
    <array>
        <string>{ag_os_bin}</string>
        <string>daemon</string>
        <string>start</string>
    </array>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>{_LOG_FILE}</string>
    <key>StandardErrorPath</key>
    <string>{_LOG_FILE}</string>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>
"""
    _LAUNCHD_PLIST.parent.mkdir(parents=True, exist_ok=True)
    _LAUNCHD_PLIST.write_text(plist, encoding="utf-8")
    return str(_LAUNCHD_PLIST)


def _install_systemd(ag_os_bin: str, config: dict) -> str:
    """Generate and install a systemd user service unit."""
    unit = f"""[Unit]
Description=Antigravity OS Dream Daemon
After=default.target

[Service]
Type=simple
ExecStart={ag_os_bin} daemon start
Restart=on-failure
RestartSec=60

[Install]
WantedBy=default.target
"""
    _SYSTEMD_SERVICE.parent.mkdir(parents=True, exist_ok=True)
    _SYSTEMD_SERVICE.write_text(unit, encoding="utf-8")
    return str(_SYSTEMD_SERVICE)


def uninstall_service() -> Optional[str]:
    """Remove the installed OS service. Returns the path removed, or None."""
    if _LAUNCHD_PLIST.is_file():
        _LAUNCHD_PLIST.unlink()
        return str(_LAUNCHD_PLIST)
    if _SYSTEMD_SERVICE.is_file():
        _SYSTEMD_SERVICE.unlink()
        return str(_SYSTEMD_SERVICE)
    return None
