from __future__ import annotations


class ProviderError(Exception):
    def __init__(self, message: str, provider: str) -> None:
        super().__init__(message)

        self.name = "ProviderError"
        self.message = message
        self.provider = provider

    def __repr__(self) -> str:
        return (
            f"ProviderError(message={self.message!r}, "
            f"provider={self.provider!r})"
        )


class CepxError(Exception):
    def __init__(
        self,
        message: str,
        type: str,
        errors: list[ProviderError],
    ) -> None:
        super().__init__(message)

        self.name = "CepxError"
        self.message = message
        self.type = type
        self.errors = errors

    def __repr__(self) -> str:
        return (
            f"CepxError(message={self.message!r}, "
            f"type={self.type!r}, errors={self.errors!r})"
        )
