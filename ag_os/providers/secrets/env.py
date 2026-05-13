"""Environment variable secrets provider."""

import os

from ag_os.providers.registry import register
from ag_os.providers.secrets import SecretsProvider


@register("secrets", "env")
class EnvSecretsProvider(SecretsProvider):
    """Reads secrets directly from os.environ.

    Optionally filters by a prefix (e.g., AG_OS_).
    """

    def __init__(self, prefix: str = "", **kwargs):
        self._prefix = prefix

    def get_secret(self, name: str) -> str | None:
        return os.environ.get(f"{self._prefix}{name}")

    def list_secrets(self) -> list[str]:
        if self._prefix:
            return sorted(k[len(self._prefix) :] for k in os.environ if k.startswith(self._prefix))
        return sorted(os.environ.keys())
