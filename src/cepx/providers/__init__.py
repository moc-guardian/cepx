from __future__ import annotations

import importlib
import pkgutil

from cepx.providers.base import (
    _REGISTRY,
    DEFAULT_TIMEOUT,
    HttpProvider,
    Provider,
)

# Autodiscover providers
for _name in sorted(module.name for module in pkgutil.iter_modules(__path__)):
    if _name != "base":
        importlib.import_module(f"{__name__}.{_name}")


def get_available_providers() -> dict[str, Provider]:
    return {name: cls() for name, cls in _REGISTRY.items()}


DEFAULT_PROVIDER_NAMES = tuple(
    name for name, cls in _REGISTRY.items() if cls.in_default_set
)


__all__ = (
    "DEFAULT_PROVIDER_NAMES",
    "DEFAULT_TIMEOUT",
    "HttpProvider",
    "Provider",
    "get_available_providers",
)
