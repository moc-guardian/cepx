from __future__ import annotations

from cepx.providers.base import DEFAULT_TIMEOUT, Provider
from cepx.providers.brasilapi import BrasilAPI
from cepx.providers.correios import Correios
from cepx.providers.correios_alt import CorreiosAlt
from cepx.providers.viacep import ViaCep
from cepx.providers.widenet import WideNet


def get_available_providers() -> dict[str, Provider]:
    return {
        "correios": Correios(),
        "correios-alt": CorreiosAlt(),
        "viacep": ViaCep(),
        "widenet": WideNet(),
        "brasilapi": BrasilAPI(),
    }


__all__ = (
    "DEFAULT_TIMEOUT",
    "BrasilAPI",
    "Correios",
    "CorreiosAlt",
    "Provider",
    "ViaCep",
    "WideNet",
    "get_available_providers",
)
