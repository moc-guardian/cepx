from __future__ import annotations

from abc import ABC, abstractmethod

from cepx._types import Address, RequestSpec
from cepx.errors import ProviderError

DEFAULT_TIMEOUT = 30.0


class Provider(ABC):
    name: str
    connection_error_message: str

    @abstractmethod
    def build_request(self, cep: str) -> RequestSpec: ...

    @abstractmethod
    def parse(self, status_code: int, body: str) -> Address: ...

    def build_address(
        self,
        *,
        cep: str | None,
        state: str | None,
        city: str | None,
        neighborhood: str | None,
        street: str | None,
    ) -> Address:
        for value in (cep, state, city):
            if value is None or not str(value).strip():
                raise ProviderError(
                    f"Incomplete response from the {self.name} provider.",
                    self.name,
                )

        return Address(
            cep=str(cep).strip().replace("-", ""),
            state=str(state).strip(),
            city=str(city).strip(),
            neighborhood=str(neighborhood or "").strip(),
            street=str(street or "").strip(),
            provider=self.name,
        )
