from __future__ import annotations

import json

from cepx._types import Address, RequestSpec
from cepx.errors import ProviderError
from cepx.providers.base import HttpProvider

_NOT_FOUND = "CEP not found in the Correios database."


class CorreiosAlt(HttpProvider):
    name = "correios-alt"
    connection_error_message = "Failed to connect to the Correios Alt provider."

    def build_request(self, cep: str) -> RequestSpec:
        headers = {
            "content-type": (
                "application/x-www-form-urlencoded; charset=UTF-8"
            ),
            "referer": (
                "https://buscacepinter.correios.com.br/app/endereco/index.php"
            ),
            "referrer-policy": "strict-origin-when-cross-origin",
        }

        body = {
            "endereco": cep,
            "tipoCEP": "ALL",
        }

        return RequestSpec(
            method="POST",
            url=(
                "https://buscacepinter.correios.com.br"
                "/app/endereco/carrega-cep-endereco.php"
            ),
            headers=headers,
            data=body,
        )

    def parse(self, status_code: int, body: str) -> Address:
        data = json.loads(body)
        dados = data.get("dados") or [{}]

        not_found = (
            data.get("total") == 0
            or data.get("erro")
            or not dados[0].get("cep")
        )

        if not_found:
            raise ProviderError(_NOT_FOUND, self.name)

        first = dados[0]

        return self.build_address(
            cep=first.get("cep"),
            state=first.get("uf"),
            city=first.get("localidade"),
            neighborhood=first.get("bairro"),
            street=first.get("logradouroDNEC"),
        )
