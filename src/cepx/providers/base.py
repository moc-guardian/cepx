from __future__ import annotations

from abc import ABC, abstractmethod

import httpx

from cepx._types import Address, RequestSpec
from cepx.errors import ProviderError

DEFAULT_TIMEOUT = 30.0


class Provider(ABC):
    name: str
    connection_error_message: str

    @abstractmethod
    def resolve_sync(
        self,
        cep: str,
        client: httpx.Client | None,
        timeout: float,
    ) -> Address: ...

    @abstractmethod
    async def resolve_async(
        self,
        cep: str,
        client: httpx.AsyncClient | None,
        timeout: float,
    ) -> Address: ...

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


class HttpProvider(Provider):
    """A provider backed by an HTTP request/response pair.

    Subclasses describe the call with `build_request` and turn the response
    into an :class:`Address` with `parse`; this base drives the transport for
    both the sync and async code paths.
    """

    @abstractmethod
    def build_request(self, cep: str) -> RequestSpec: ...

    @abstractmethod
    def parse(self, status_code: int, body: str) -> Address: ...

    def resolve_sync(
        self,
        cep: str,
        client: httpx.Client | None,
        timeout: float,
    ) -> Address:
        if client is None:
            raise RuntimeError("HttpProvider requires an httpx client")

        spec = self.build_request(cep)

        response = client.request(
            spec.method,
            spec.url,
            headers=spec.headers,
            content=spec.content,
            data=spec.data,
            timeout=timeout,
        )

        return self.parse(response.status_code, response.text)

    async def resolve_async(
        self,
        cep: str,
        client: httpx.AsyncClient | None,
        timeout: float,
    ) -> Address:
        if client is None:
            raise RuntimeError("HttpProvider requires an httpx client")

        spec = self.build_request(cep)

        response = await client.request(
            spec.method,
            spec.url,
            headers=spec.headers,
            content=spec.content,
            data=spec.data,
            timeout=timeout,
        )

        return self.parse(response.status_code, response.text)
