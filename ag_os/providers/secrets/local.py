"""Local .env file secrets provider (DEFAULT)."""

from pathlib import Path

from ag_os.providers.registry import register
from ag_os.providers.secrets import SecretsProvider


@register("secrets", "local")
class LocalSecretsProvider(SecretsProvider):
    """Reads secrets from a `.env` file in the project root.

    Format: KEY=value (one per line, # comments supported).
    No external dependencies required.
    """

    def __init__(self, env_path: str = ".env", **kwargs):
        self._path = Path(env_path)
        self._cache: dict[str, str] = {}
        self._load()

    def _load(self):
        """Parse the .env file into the cache."""
        self._cache.clear()
        if not self._path.is_file():
            return
        with open(self._path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    continue
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip().strip("\"'")
                if key:
                    self._cache[key] = value

    def get_secret(self, name: str) -> str | None:
        return self._cache.get(name)

    def list_secrets(self) -> list[str]:
        return sorted(self._cache.keys())
