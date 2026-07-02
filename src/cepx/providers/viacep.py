from __future__ import annotations

import json

from cepx._types import Address, RequestSpec
from cepx.errors import ProviderError
from cepx.providers.base import Provider


class ViaCep(Provider):
    name = "viacep"
    connection_error_message = "Failed to connect to the ViaCEP provider."

    def build_request(self, cep: str) -> RequestSpec:
        headers = {
            "content-type": "application/json;charset=utf-8",
            "user-agent": "cepx",
        }

        return RequestSpec(
            method="GET",
            url=f"https://viacep.com.br/ws/{cep}/json/",
            headers=headers,
        )

    def parse(self, status_code: int, body: str) -> Address:
        if not 200 <= status_code < 300:
            raise ProviderError(self.connection_error_message, self.name)

        data = json.loads(body)

        if data.get("erro"):
            raise ProviderError(
                "CEP not found in the ViaCEP database.",
                self.name,
            )

        return self.build_address(
            cep=data.get("cep"),
            state=data.get("uf"),
            city=data.get("localidade"),
            neighborhood=data.get("bairro"),
            street=data.get("logradouro"),
        )
