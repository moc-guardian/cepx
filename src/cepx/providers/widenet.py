from __future__ import annotations

import json

from cepx._types import Address, RequestSpec
from cepx.errors import ProviderError
from cepx.providers.base import Provider


class WideNet(Provider):
    name = "widenet"
    connection_error_message = "Failed to connect to the WideNet provider."

    def build_request(self, cep: str) -> RequestSpec:
        cep_with_dash = f"{cep[:5]}-{cep[5:]}"

        headers = {
            "accept": "application/json",
        }

        return RequestSpec(
            method="GET",
            url=f"https://cdn.apicep.com/file/apicep/{cep_with_dash}.json",
            headers=headers,
        )

    def parse(self, status_code: int, body: str) -> Address:
        if not 200 <= status_code < 300:
            raise ProviderError(self.connection_error_message, self.name)

        data = json.loads(body)

        if data.get("ok") is False or data.get("status") != 200:
            raise ProviderError(
                "CEP not found in the WideNet database.",
                self.name,
            )

        return self.build_address(
            cep=data.get("code"),
            state=data.get("state"),
            city=data.get("city"),
            neighborhood=data.get("district"),
            street=data.get("address"),
        )
