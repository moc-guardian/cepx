from __future__ import annotations

import json

from cepx._types import Address, RequestSpec
from cepx.errors import ProviderError
from cepx.providers.base import HttpProvider


class BrasilAPI(HttpProvider):
    name = "brasilapi"
    connection_error_message = "Failed to connect to the BrasilAPI provider."

    def build_request(self, cep: str) -> RequestSpec:
        headers = {
            "content-type": "application/json;charset=utf-8",
        }

        return RequestSpec(
            method="GET",
            url=f"https://brasilapi.com.br/api/cep/v2/{cep}",
            headers=headers,
        )

    def parse(self, status_code: int, body: str) -> Address:
        if status_code != 200:
            raise ProviderError(
                "CEP not found in the BrasilAPI database.",
                self.name,
            )

        data = json.loads(body)

        return self.build_address(
            cep=data.get("cep"),
            state=data.get("state"),
            city=data.get("city"),
            neighborhood=data.get("neighborhood"),
            street=data.get("street"),
        )
