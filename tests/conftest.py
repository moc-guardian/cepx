from __future__ import annotations

import httpx
import pytest
import respx

BRASILAPI_URL = "https://brasilapi.com.br/api/cep/v1/05010000"
VIACEP_URL = "https://viacep.com.br/ws/05010000/json/"
WIDENET_URL = "https://cdn.apicep.com/file/apicep/05010-000.json"

CORREIOS_URL = (
    "https://apps.correios.com.br"
    "/SigepMasterJPA/AtendeClienteService/AtendeCliente"
)

CORREIOS_ALT_URL = (
    "https://buscacepinter.correios.com.br"
    "/app/endereco/carrega-cep-endereco.php"
)

CORREIOS_XML_FOUND = (
    '<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">'
    "<soap:Body><ns2:consultaCEPResponse><return>"
    "<bairro>Perdizes</bairro><cep>05010000</cep>"
    "<cidade>São Paulo</cidade><end>Rua Caiubi</end><uf>SP</uf>"
    "</return></ns2:consultaCEPResponse></soap:Body></soap:Envelope>"
)

CORREIOS_XML_FAULT = (
    '<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">'
    "<soap:Body><soap:Fault>"
    "<faultstring>INVALID CEP</faultstring>"
    "</soap:Fault></soap:Body></soap:Envelope>"
)

PROVIDER_NAMES = ["correios", "correios-alt", "viacep", "widenet", "brasilapi"]


def stub_found(router, name):
    if name == "brasilapi":
        router.get(BRASILAPI_URL).respond(
            json={
                "cep": "05010000",
                "state": "SP",
                "city": "São Paulo",
                "neighborhood": "Perdizes",
                "street": "Rua Caiubi",
            }
        )
    elif name == "viacep":
        router.get(VIACEP_URL).respond(
            json={
                "cep": "05010-000",
                "logradouro": "Rua Caiubi",
                "bairro": "Perdizes",
                "localidade": "São Paulo",
                "uf": "SP",
            }
        )
    elif name == "widenet":
        router.get(WIDENET_URL).respond(
            json={
                "status": 200,
                "ok": True,
                "code": "05010-000",
                "state": "SP",
                "city": "São Paulo",
                "district": "Perdizes",
                "address": "Rua Caiubi",
            }
        )
    elif name == "correios":
        router.post(CORREIOS_URL).respond(text=CORREIOS_XML_FOUND)
    elif name == "correios-alt":
        router.post(CORREIOS_ALT_URL).respond(
            json={
                "erro": False,
                "total": 1,
                "dados": [
                    {
                        "uf": "SP",
                        "localidade": "São Paulo",
                        "logradouroDNEC": "Rua Caiubi",
                        "bairro": "Perdizes",
                        "cep": "05010000",
                    }
                ],
            }
        )


def stub_failed(router, name):
    if name == "brasilapi":
        router.get(BRASILAPI_URL).respond(status_code=404, json={})
    elif name == "viacep":
        router.get(VIACEP_URL).respond(json={"erro": True})
    elif name == "widenet":
        router.get(WIDENET_URL).respond(
            json={"status": 404, "ok": False, "message": "not found"}
        )
    elif name == "correios":
        router.post(CORREIOS_URL).respond(
            status_code=500, text=CORREIOS_XML_FAULT
        )
    elif name == "correios-alt":
        router.post(CORREIOS_ALT_URL).respond(json={"total": 0, "dados": []})


@pytest.fixture
def mock_all_found():
    with respx.mock(assert_all_called=False) as router:
        for name in PROVIDER_NAMES:
            stub_found(router, name)
        yield router


@pytest.fixture
def mock_all_failed():
    with respx.mock(assert_all_called=False) as router:
        for name in PROVIDER_NAMES:
            stub_failed(router, name)
        yield router


@pytest.fixture
def expected_address():
    return {
        "cep": "05010000",
        "state": "SP",
        "city": "São Paulo",
        "neighborhood": "Perdizes",
        "street": "Rua Caiubi",
    }


@pytest.fixture(autouse=True)
def _clear_bundled_db_cache():
    # LocalProvider caches the cepx-data path for the process; tests that swap
    # the cepx_data module in/out must not see each other's cached result.
    from cepx.providers.local import _bundled_db_path

    _bundled_db_path.cache_clear()

    yield


__all__ = (
    "BRASILAPI_URL",
    "CORREIOS_ALT_URL",
    "CORREIOS_URL",
    "CORREIOS_XML_FAULT",
    "CORREIOS_XML_FOUND",
    "PROVIDER_NAMES",
    "VIACEP_URL",
    "WIDENET_URL",
    "httpx",
    "stub_failed",
    "stub_found",
)
