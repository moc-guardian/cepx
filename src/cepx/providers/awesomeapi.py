from __future__ import annotations

import json

from cepx._types import Address, RequestSpec
from cepx.errors import ProviderError
from cepx.providers.base import HttpProvider


class AwesomeAPI(HttpProvider):
    name = "awesomeapi"
    connection_error_message = "Failed to connect to the AwesomeAPI provider."

    def build_request(self, cep: str) -> RequestSpec:
        headers = {
            "content-type": "application/json;charset=utf-8",
        }

        return RequestSpec(
            method="GET",
            url=f"https://cep.awesomeapi.com.br/json/{cep}",
            headers=headers,
        )

    def parse(self, status_code: int, body: str) -> Address:
        if status_code == 404:
            raise ProviderError(
                "CEP not found in the AwesomeAPI database.",
                self.name,
            )

        if not 200 <= status_code < 300:
            raise ProviderError(self.connection_error_message, self.name)

        data = json.loads(body)

        return self.build_address(
            cep=data.get("cep"),
            state=data.get("state"),
            city=data.get("city"),
            neighborhood=data.get("district"),
            street=data.get("address"),
        )
