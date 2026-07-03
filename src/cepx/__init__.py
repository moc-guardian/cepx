from __future__ import annotations

from importlib.metadata import version

from cepx._core import acep, cep
from cepx._types import Address
from cepx.errors import CepxError, ProviderError
from cepx.providers import get_available_providers

__version__ = version("cepx")

__all__ = (
    "Address",
    "CepxError",
    "ProviderError",
    "acep",
    "cep",
    "get_available_providers",
)
