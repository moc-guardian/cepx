from __future__ import annotations

import re

from cepx.errors import CepxError, ProviderError
from cepx.providers import (
    DEFAULT_PROVIDER_NAMES,
    Provider,
    get_available_providers,
)

CEP_SIZE = 8
_NON_DIGITS = re.compile(r"\D+")


def prepare(
    cep_raw: str | int,
    providers: list[str] | None,
) -> tuple[str, list[Provider]]:
    _validate_input_type(cep_raw)

    resolved = _resolve_providers(providers)
    cleaned = _NON_DIGITS.sub("", str(cep_raw))

    _validate_length(cleaned)

    return cleaned.zfill(CEP_SIZE), resolved


def _validate_input_type(cep_raw: object) -> None:
    if isinstance(cep_raw, bool) or not isinstance(cep_raw, (str, int)):
        raise CepxError(
            "Failed to initialize cepx.",
            "validation_error",
            [
                ProviderError(
                    "You must call cepx with a string or an integer.",
                    "cep_validation",
                )
            ],
        )


def _resolve_providers(providers: list[str] | None) -> list[Provider]:
    available = get_available_providers()

    if providers is None or providers == []:
        return [available[name] for name in DEFAULT_PROVIDER_NAMES]

    if not isinstance(providers, list):
        raise CepxError(
            "Failed to initialize cepx.",
            "validation_error",
            [
                ProviderError(
                    "The providers parameter must be a list.",
                    "providers_validation",
                )
            ],
        )

    names = '", "'.join(available)
    resolved: list[Provider] = []

    for provider in providers:
        if provider not in available:
            raise CepxError(
                "Failed to initialize cepx.",
                "validation_error",
                [
                    ProviderError(
                        f'The provider "{provider}" is invalid. Available '
                        f'providers are: ["{names}"].',
                        "providers_validation",
                    )
                ],
            )

        resolved.append(available[provider])

    return resolved


def _validate_length(cleaned: str) -> None:
    if len(cleaned) <= CEP_SIZE:
        return

    raise CepxError(
        f"CEP must contain exactly {CEP_SIZE} characters.",
        "validation_error",
        [
            ProviderError(
                f"The provided CEP has more than {CEP_SIZE} characters.",
                "cep_validation",
            )
        ],
    )
