from __future__ import annotations

import re

from cepx._types import Address, RequestSpec
from cepx.errors import ProviderError
from cepx.providers.base import Provider

_RETURN_RE = re.compile(r"<return>(.*)</return>")
_FAULT_RE = re.compile(r"<faultstring>(.*)</faultstring>")
_UNPARSEABLE = "Could not parse the response XML."


class Correios(Provider):
    name = "correios"
    connection_error_message = "Failed to connect to the Correios provider."

    def build_request(self, cep: str) -> RequestSpec:
        headers = {
            "content-type": "text/xml;charset=UTF-8",
            "cache-control": "no-cache",
        }

        envelope = (
            '<?xml version="1.0"?>\n'
            "<soapenv:Envelope "
            'xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" '
            'xmlns:cli="http://cliente.bean.master.sigep.bsb.correios.com.br/">'
            "\n  <soapenv:Header />\n  <soapenv:Body>\n"
            "    <cli:consultaCEP>\n"
            f"      <cep>{cep}</cep>\n"
            "    </cli:consultaCEP>\n"
            "  </soapenv:Body>\n</soapenv:Envelope>"
        )

        return RequestSpec(
            method="POST",
            url=(
                "https://apps.correios.com.br"
                "/SigepMasterJPA/AtendeClienteService/AtendeCliente"
            ),
            headers=headers,
            content=envelope,
        )

    def parse(self, status_code: int, body: str) -> Address:
        if 200 <= status_code < 300:
            fields = _parse_return(body)

            return self.build_address(
                cep=fields.get("cep"),
                state=fields.get("uf"),
                city=fields.get("cidade"),
                neighborhood=fields.get("bairro"),
                street=fields.get("end"),
            )

        raise ProviderError(_parse_fault(body), self.name)


def _parse_return(xml: str) -> dict[str, str]:
    match = _RETURN_RE.search(xml.replace("\r", "").replace("\n", ""))

    if match is None:
        raise ProviderError(_UNPARSEABLE, Correios.name)

    fields: dict[str, str] = {}

    for chunk in match.group(1).split("<"):
        tag, _, value = chunk.partition(">")

        if value:
            fields[tag] = value

    return fields


def _parse_fault(xml: str) -> str:
    match = _FAULT_RE.search(xml)

    if match is None:
        raise ProviderError(_UNPARSEABLE, Correios.name)

    return match.group(1)
