from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Address:
    cep: str
    state: str
    city: str
    neighborhood: str
    street: str
    provider: str


@dataclass(frozen=True)
class RequestSpec:
    method: str
    url: str
    headers: dict[str, str]
    content: str | None = None
    data: dict[str, str] | None = None
