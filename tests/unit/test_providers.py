from __future__ import annotations

import httpx
import pytest
import respx

import cepx
from tests.conftest import (
    AWESOMEAPI_URL,
    BRASILAPI_URL,
    CORREIOS_ALT_URL,
    CORREIOS_URL,
    CORREIOS_XML_FAULT,
    CORREIOS_XML_FOUND,
    OPENCEP_URL,
    VIACEP_URL,
    WIDENET_URL,
)

pytestmark = pytest.mark.unit


def _assert_matches(address, provider, expected_address):
    assert address == cepx.Address(provider=provider, **expected_address)


def test_brasilapi(mock_all_found, expected_address):
    address = cepx.cep("05010000", providers=["brasilapi"])
    _assert_matches(address, "brasilapi", expected_address)


def test_viacep(mock_all_found, expected_address):
    address = cepx.cep("05010000", providers=["viacep"])
    _assert_matches(address, "viacep", expected_address)


def test_widenet(mock_all_found, expected_address):
    address = cepx.cep("05010000", providers=["widenet"])
    _assert_matches(address, "widenet", expected_address)


def test_opencep(mock_all_found, expected_address):
    address = cepx.cep("05010000", providers=["opencep"])
    _assert_matches(address, "opencep", expected_address)


def test_awesomeapi(mock_all_found, expected_address):
    address = cepx.cep("05010000", providers=["awesomeapi"])
    _assert_matches(address, "awesomeapi", expected_address)


def test_correios(mock_all_found, expected_address):
    address = cepx.cep("05010000", providers=["correios"])
    _assert_matches(address, "correios", expected_address)


def test_correios_alt(mock_all_found, expected_address):
    address = cepx.cep("05010000", providers=["correios-alt"])
    _assert_matches(address, "correios-alt", expected_address)


@respx.mock
def test_viacep_not_found():
    respx.get(VIACEP_URL).respond(json={"erro": True})
    with pytest.raises(cepx.CepxError) as info:
        cepx.cep("05010000", providers=["viacep"])
    assert info.value.errors[0].message == (
        "CEP not found in the ViaCEP database."
    )


@respx.mock
def test_viacep_not_found_string_erro():
    respx.get(VIACEP_URL).respond(json={"erro": "true"})
    with pytest.raises(cepx.CepxError) as info:
        cepx.cep("05010000", providers=["viacep"])
    assert info.value.errors[0].message == (
        "CEP not found in the ViaCEP database."
    )


@respx.mock
def test_widenet_not_found():
    respx.get(WIDENET_URL).respond(json={"status": 404, "ok": False})
    with pytest.raises(cepx.CepxError) as info:
        cepx.cep("05010000", providers=["widenet"])
    assert info.value.errors[0].message == (
        "CEP not found in the WideNet database."
    )


@respx.mock
def test_opencep_not_found():
    respx.get(OPENCEP_URL).respond(status_code=404, json={})
    with pytest.raises(cepx.CepxError) as info:
        cepx.cep("05010000", providers=["opencep"])
    assert info.value.errors[0].message == (
        "CEP not found in the OpenCEP database."
    )


@respx.mock
def test_opencep_non_2xx_is_connection_error():
    respx.get(OPENCEP_URL).respond(status_code=500)
    with pytest.raises(cepx.CepxError) as info:
        cepx.cep("05010000", providers=["opencep"])
    assert info.value.errors[0].message == (
        "Failed to connect to the OpenCEP provider."
    )


@respx.mock
def test_awesomeapi_not_found():
    respx.get(AWESOMEAPI_URL).respond(
        status_code=404, json={"code": "not_found"}
    )
    with pytest.raises(cepx.CepxError) as info:
        cepx.cep("05010000", providers=["awesomeapi"])
    assert info.value.errors[0].message == (
        "CEP not found in the AwesomeAPI database."
    )


@respx.mock
def test_awesomeapi_non_2xx_is_connection_error():
    respx.get(AWESOMEAPI_URL).respond(status_code=500)
    with pytest.raises(cepx.CepxError) as info:
        cepx.cep("05010000", providers=["awesomeapi"])
    assert info.value.errors[0].message == (
        "Failed to connect to the AwesomeAPI provider."
    )


@respx.mock
def test_correios_fault_message():
    respx.post(CORREIOS_URL).respond(status_code=500, text=CORREIOS_XML_FAULT)
    with pytest.raises(cepx.CepxError) as info:
        cepx.cep("05010000", providers=["correios"])
    assert info.value.errors[0].message == "INVALID CEP"


@respx.mock
def test_correios_alt_not_found():
    respx.post(CORREIOS_ALT_URL).respond(json={"total": 0, "dados": []})
    with pytest.raises(cepx.CepxError) as info:
        cepx.cep("05010000", providers=["correios-alt"])
    assert info.value.errors[0].message == (
        "CEP not found in the Correios database."
    )


@respx.mock
def test_connection_error_maps_to_provider_message():
    respx.get(VIACEP_URL).mock(side_effect=httpx.ConnectError("boom"))
    with pytest.raises(cepx.CepxError) as info:
        cepx.cep("05010000", providers=["viacep"])
    assert info.value.errors[0].message == (
        "Failed to connect to the ViaCEP provider."
    )


@respx.mock
def test_correios_success_uses_found_xml():
    respx.post(CORREIOS_URL).respond(text=CORREIOS_XML_FOUND)
    address = cepx.cep("05010000", providers=["correios"])
    assert address.city == "São Paulo"
    assert address.street == "Rua Caiubi"


@respx.mock
def test_correios_success_without_return_block():
    respx.post(CORREIOS_URL).respond(text="<soap:Envelope></soap:Envelope>")
    with pytest.raises(cepx.CepxError) as info:
        cepx.cep("05010000", providers=["correios"])
    assert info.value.errors[0].message == ("Could not parse the response XML.")


@respx.mock
def test_correios_fault_without_faultstring():
    respx.post(CORREIOS_URL).respond(
        status_code=500, text="<soap:Envelope></soap:Envelope>"
    )
    with pytest.raises(cepx.CepxError) as info:
        cepx.cep("05010000", providers=["correios"])
    assert info.value.errors[0].message == ("Could not parse the response XML.")


@respx.mock
def test_viacep_non_2xx_is_connection_error():
    respx.get(VIACEP_URL).respond(status_code=500)
    with pytest.raises(cepx.CepxError) as info:
        cepx.cep("05010000", providers=["viacep"])
    assert info.value.errors[0].message == (
        "Failed to connect to the ViaCEP provider."
    )


@respx.mock
def test_widenet_non_2xx_is_connection_error():
    respx.get(WIDENET_URL).respond(status_code=500)
    with pytest.raises(cepx.CepxError) as info:
        cepx.cep("05010000", providers=["widenet"])
    assert info.value.errors[0].message == (
        "Failed to connect to the WideNet provider."
    )


@respx.mock
def test_null_essential_field_fails_the_provider():
    respx.get(BRASILAPI_URL).respond(
        json={
            "cep": "05010000",
            "state": None,
            "city": "São Paulo",
            "neighborhood": "Perdizes",
            "street": "Rua Caiubi",
        }
    )
    with pytest.raises(cepx.CepxError) as info:
        cepx.cep("05010000", providers=["brasilapi"])
    assert info.value.errors[0].message == (
        "Incomplete response from the brasilapi provider."
    )


@respx.mock
def test_empty_essential_field_fails_the_provider():
    respx.get(BRASILAPI_URL).respond(
        json={
            "cep": "05010000",
            "state": "SP",
            "city": "   ",
            "neighborhood": "Perdizes",
            "street": "Rua Caiubi",
        }
    )
    with pytest.raises(cepx.CepxError) as info:
        cepx.cep("05010000", providers=["brasilapi"])
    assert info.value.errors[0].message == (
        "Incomplete response from the brasilapi provider."
    )


@respx.mock
def test_null_optional_fields_are_coerced_to_empty():
    respx.get(BRASILAPI_URL).respond(
        json={
            "cep": "05010000",
            "state": "SP",
            "city": "São Paulo",
            "neighborhood": None,
            "street": None,
        }
    )
    address = cepx.cep("05010000", providers=["brasilapi"])
    assert address.neighborhood == ""
    assert address.street == ""
