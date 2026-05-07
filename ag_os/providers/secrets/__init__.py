"""Secrets provider interface."""

from abc import ABC, abstractmethod
from typing import Optional


class SecretsProvider(ABC):
    """Abstract base class for secret/credential retrieval."""

    @abstractmethod
    def get_secret(self, name: str) -> Optional[str]:
        """Retrieve a secret value by name.

        Returns:
            The secret value, or None if not found.
        """
        ...

    @abstractmethod
    def list_secrets(self) -> list[str]:
        """List available secret names.

        Returns:
            A list of secret key names.
        """
        ...
