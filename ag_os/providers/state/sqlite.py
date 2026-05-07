"""SQLite state provider (DEFAULT) -- zero infrastructure required."""

import sqlite3
import time
from pathlib import Path
from typing import Optional

from ag_os.providers.registry import register
from ag_os.providers.state import StateProvider

_DB_PATH = Path.home() / ".antigravity" / "state.db"


@register("state", "sqlite")
class SQLiteStateProvider(StateProvider):
    """Persists state in a local SQLite database.

    This is the #1 architectural decision that removes Docker as a
    hard requirement. A solo developer cloning the repo on a laptop
    should not need Docker running.

    Database location: ~/.antigravity/state.db
    """

    def __init__(self, db_path: str = "", **kwargs):
        path = Path(db_path) if db_path else _DB_PATH
        path.parent.mkdir(parents=True, exist_ok=True)
        self._db_path = str(path)
        self._init_db()

    def _init_db(self):
        with self._connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS state (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    expires_at REAL DEFAULT 0
                )
            """)

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self._db_path)

    def set(self, key: str, value: str, ttl_seconds: int = 0) -> None:
        expires_at = (time.time() + ttl_seconds) if ttl_seconds > 0 else 0
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO state (key, value, expires_at) VALUES (?, ?, ?)",
                (key, value, expires_at),
            )

    def get(self, key: str) -> Optional[str]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT value, expires_at FROM state WHERE key = ?",
                (key,),
            ).fetchone()
        if row is None:
            return None
        value, expires_at = row
        if expires_at > 0 and time.time() > expires_at:
            self.delete(key)
            return None
        return value

    def delete(self, key: str) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM state WHERE key = ?", (key,))

    def ping(self) -> bool:
        try:
            with self._connect() as conn:
                conn.execute("SELECT 1")
            return True
        except sqlite3.Error:
            return False
