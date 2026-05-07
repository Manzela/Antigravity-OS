"""
Provider Registry — The core extension mechanism of Antigravity OS.

Every integration surface (secrets, issues, cost, state, telemetry, policy)
registers its implementations here. The registry uses a decorator pattern
for registration and a factory function for instantiation.

Usage:
    from ag_os.providers.registry import register, get_provider

    @register("secrets", "local")
    class LocalSecretsProvider(SecretsProvider):
        ...

    provider = get_provider("secrets", "local", config=config)
"""

from typing import Any, Dict, Type

_REGISTRY: Dict[str, Dict[str, Type]] = {}


def register(surface: str, name: str):
    """Decorator to register a provider implementation.

    Args:
        surface: The integration surface (e.g., "secrets", "issues", "cost").
        name: The provider name as it appears in antigravity.yaml.

    Returns:
        The original class, unmodified.
    """

    def decorator(cls):
        _REGISTRY.setdefault(surface, {})[name] = cls
        return cls

    return decorator


def get_provider(surface: str, name: str, **kwargs) -> Any:
    """Factory: instantiate a provider by surface and name.

    Args:
        surface: The integration surface.
        name: The provider name from config.
        **kwargs: Passed to the provider constructor.

    Raises:
        ValueError: If the provider name is not registered for the surface.

    Returns:
        An instance of the requested provider.
    """
    providers = _REGISTRY.get(surface, {})
    if name not in providers:
        available = sorted(providers.keys()) if providers else []
        raise ValueError(
            f"Unknown {surface} provider '{name}'. "
            f"Available: {available}. "
            f"Check your antigravity.yaml configuration."
        )
    return providers[name](**kwargs)


def list_providers(surface: str = "") -> Dict[str, list[str]]:
    """List all registered providers, optionally filtered by surface.

    Returns:
        A dict mapping surface names to lists of provider names.
    """
    if surface:
        return {surface: sorted(_REGISTRY.get(surface, {}).keys())}
    return {s: sorted(p.keys()) for s, p in sorted(_REGISTRY.items())}


def _discover_builtins():
    """Import all built-in provider modules to trigger @register decorators."""
    # Each import triggers the @register decorator at module load time.
    # This is the only place where provider modules are explicitly imported.
    import ag_os.providers.cost.local  # noqa: F401
    import ag_os.providers.issues.console  # noqa: F401
    import ag_os.providers.policy.builtin  # noqa: F401
    import ag_os.providers.secrets.env  # noqa: F401
    import ag_os.providers.secrets.local  # noqa: F401
    import ag_os.providers.state.sqlite  # noqa: F401
    import ag_os.providers.telemetry.console  # noqa: F401


# Auto-discover on import
_discover_builtins()
