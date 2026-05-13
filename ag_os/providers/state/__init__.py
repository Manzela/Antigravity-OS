"""State provider interface (The Brain)."""

from abc import ABC, abstractmethod


class StateProvider(ABC):
    """Abstract base class for state persistence backends.

    Used by Flight Recorder, budget leases, and deduplication fingerprints.
    """

    @abstractmethod
    def set(self, key: str, value: str, ttl_seconds: int = 0) -> None:
        """Store a key-value pair with optional TTL.

        Args:
            key: The state key.
            value: The value to store (always serialized as string).
            ttl_seconds: Time-to-live in seconds. 0 means no expiration.
        """
        ...

    @abstractmethod
    def get(self, key: str) -> str | None:
        """Retrieve a value by key. Returns None if not found or expired."""
        ...

    @abstractmethod
    def delete(self, key: str) -> None:
        """Delete a key from the state store."""
        ...

    @abstractmethod
    def ping(self) -> bool:
        """Health check. Returns True if the backend is reachable."""
        ...
