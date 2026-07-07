from __future__ import annotations

from cepx.providers.base import DEFAULT_TIMEOUT, HttpProvider, Provider
from cepx.providers.brasilapi import BrasilAPI
from cepx.providers.correios import Correios
from cepx.providers.correios_alt import CorreiosAlt
from cepx.providers.local import LocalProvider
from cepx.providers.viacep import ViaCep
from cepx.providers.widenet import WideNet

# Providers queried by default when the caller does not restrict them.
# "local" is intentionally excluded: it only answers when a database is
# present, so it is opt-in via providers=["local"].
DEFAULT_PROVIDER_NAMES = (
    "correios",
    "correios-alt",
    "viacep",
    "widenet",
    "brasilapi",
)


def get_available_providers() -> dict[str, Provider]:
    return {
        "correios": Correios(),
        "correios-alt": CorreiosAlt(),
        "viacep": ViaCep(),
        "widenet": WideNet(),
        "brasilapi": BrasilAPI(),
        "local": LocalProvider(),
    }


__all__ = (
    "DEFAULT_PROVIDER_NAMES",
    "DEFAULT_TIMEOUT",
    "BrasilAPI",
    "Correios",
    "CorreiosAlt",
    "HttpProvider",
    "LocalProvider",
    "Provider",
    "ViaCep",
    "WideNet",
    "get_available_providers",
)
