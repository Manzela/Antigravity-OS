"""
Configuration loader for Antigravity OS.

Reads `antigravity.yaml` from the current directory or specified path.
Falls back to environment variables and sensible defaults.
"""

import os
from pathlib import Path
from typing import Any, Optional

import yaml

_DEFAULT_CONFIG = {
    "version": "1.0",
    "monthly_cap": 50.00,
    "max_loop_count": 5,
    "providers": {
        "secrets": "local",
        "issues": "console",
        "cost": "local",
        "state": "sqlite",
        "telemetry": "console",
        "policy": "builtin",
    },
    "ci": {
        "platform": "local",
        "self_healing": True,
    },
    "dreaming": {
        "schedule_interval_hours": 6,
        "auto_apply": False,
        "auto_prune": True,
        "retention_days": 90,
        "retention_max_count": 100,
    },
}

_CONFIG_FILENAMES = ["antigravity.yaml", "antigravity.yml"]


def find_config_file(start_dir: Optional[Path] = None) -> Optional[Path]:
    """Walk up from `start_dir` looking for an antigravity config file."""
    current = start_dir or Path.cwd()
    for _ in range(20):  # Safety bound: do not walk more than 20 levels
        for name in _CONFIG_FILENAMES:
            candidate = current / name
            if candidate.is_file():
                return candidate
        parent = current.parent
        if parent == current:
            break
        current = parent
    return None


def load_config(path: Optional[Path] = None) -> dict[str, Any]:
    """Load and validate the Antigravity OS configuration.

    Resolution order:
        1. Explicit `path` argument
        2. Auto-discovered `antigravity.yaml` in CWD or parent directories
        3. Built-in defaults (zero-config mode)

    Environment variable overrides:
        AG_OS_MONTHLY_CAP   -> monthly_cap
        AG_OS_MAX_LOOPS     -> max_loop_count
    """
    config = dict(_DEFAULT_CONFIG)

    config_path = path or find_config_file()

    if config_path and config_path.is_file():
        with open(config_path, "r", encoding="utf-8") as f:
            user_config = yaml.safe_load(f) or {}
        config = _deep_merge(config, user_config)
        config["_config_path"] = str(config_path)
    else:
        config["_config_path"] = None

    # Environment variable overrides (highest precedence)
    env_cap = os.getenv("AG_OS_MONTHLY_CAP")
    if env_cap is not None:
        config["monthly_cap"] = float(env_cap)

    env_loops = os.getenv("AG_OS_MAX_LOOPS")
    if env_loops is not None:
        config["max_loop_count"] = int(env_loops)

    return config


def _deep_merge(base: dict, override: dict) -> dict:
    """Recursively merge `override` into `base`, preferring override values."""
    merged = dict(base)
    for key, value in override.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged
