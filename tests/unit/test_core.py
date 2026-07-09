from __future__ import annotations

import asyncio

import httpx
import pytest
import respx

import cepx
from tests.conftest import (
    BRASILAPI_URL,
    PROVIDER_NAMES,
    VIACEP_URL,
    stub_failed,
    stub_found,
)

pytestmark = pytest.mark.unit


def test_first_success_wins_sync(mock_all_found, expected_address):
    address = cepx.cep("05010000")
    assert address.cep == "05010000"
    assert address.provider in {
        "correios",
        "correios-alt",
        "viacep",
        "widenet",
        "brasilapi",
        "opencep",
        "awesomeapi",
    }


async def test_first_success_wins_async(mock_all_found, expected_address):
    address = await cepx.acep("05010000")
    assert address.cep == "05010000"


@pytest.mark.parametrize("winner", PROVIDER_NAMES)
@respx.mock
def test_falls_back_to_the_only_working_provider(winner):
    for name in PROVIDER_NAMES:
        if name == winner:
            stub_found(respx, name)
        else:
            stub_failed(respx, name)

    address = cepx.cep("05010000")

    assert address.provider == winner
    assert address == cepx.Address(
        cep="05010000",
        state="SP",
        city="São Paulo",
        neighborhood="Perdizes",
        street="Rua Caiubi",
        provider=winner,
    )


@pytest.mark.parametrize("winner", PROVIDER_NAMES)
@respx.mock
async def test_falls_back_to_the_only_working_provider_async(winner):
    for name in PROVIDER_NAMES:
        if name == winner:
            stub_found(respx, name)
        else:
            stub_failed(respx, name)

    address = await cepx.acep("05010000")

    assert address.provider == winner


def test_all_failed_sync(mock_all_failed):
    with pytest.raises(cepx.CepxError) as info:
        cepx.cep("05010000")
    error = info.value
    assert error.type == "provider_error"
    assert error.message == "All CEP providers returned an error."
    providers = {e.provider for e in error.errors}
    assert providers == {
        "correios",
        "correios-alt",
        "viacep",
        "widenet",
        "brasilapi",
        "opencep",
        "awesomeapi",
    }


async def test_all_failed_async(mock_all_failed):
    with pytest.raises(cepx.CepxError) as info:
        await cepx.acep("05010000")
    assert info.value.type == "provider_error"
    assert len(info.value.errors) == 7


def test_aggregated_errors_preserve_provider_order(mock_all_failed):
    with pytest.raises(cepx.CepxError) as info:
        cepx.cep("05010000")
    assert [e.provider for e in info.value.errors] == [
        "awesomeapi",
        "brasilapi",
        "correios",
        "correios-alt",
        "opencep",
        "viacep",
        "widenet",
    ]


@respx.mock
def test_only_selected_provider_is_called():
    viacep_route = respx.get(VIACEP_URL).respond(
        json={
            "cep": "05010-000",
            "logradouro": "Rua Caiubi",
            "bairro": "Perdizes",
            "localidade": "São Paulo",
            "uf": "SP",
        }
    )
    brasilapi_route = respx.get(BRASILAPI_URL).respond(json={})

    cepx.cep("05010000", providers=["viacep"])

    assert viacep_route.called
    assert not brasilapi_route.called


@respx.mock
async def test_only_selected_provider_is_called_async():
    viacep_route = respx.get(VIACEP_URL).respond(
        json={
            "cep": "05010-000",
            "logradouro": "Rua Caiubi",
            "bairro": "Perdizes",
            "localidade": "São Paulo",
            "uf": "SP",
        }
    )
    brasilapi_route = respx.get(BRASILAPI_URL).respond(json={})

    await cepx.acep("05010000", providers=["viacep"])

    assert viacep_route.called
    assert not brasilapi_route.called


@respx.mock
def test_malformed_response_is_contained_sync():
    respx.get(BRASILAPI_URL).respond(text="<<not json>>")
    with pytest.raises(cepx.CepxError) as info:
        cepx.cep("05010000", providers=["brasilapi"])
    assert info.value.errors[0].message == (
        "Malformed response from the brasilapi provider."
    )
    assert info.value.errors[0].provider == "brasilapi"


@respx.mock
async def test_malformed_response_is_contained_async():
    respx.get(BRASILAPI_URL).respond(text="<<not json>>")
    with pytest.raises(cepx.CepxError) as info:
        await cepx.acep("05010000", providers=["brasilapi"])
    assert info.value.errors[0].message == (
        "Malformed response from the brasilapi provider."
    )


@respx.mock
def test_one_malformed_provider_does_not_crash_others():
    respx.get(BRASILAPI_URL).respond(text="<<not json>>")
    respx.get(VIACEP_URL).respond(
        json={
            "cep": "05010-000",
            "logradouro": "Rua Caiubi",
            "bairro": "Perdizes",
            "localidade": "São Paulo",
            "uf": "SP",
        }
    )

    address = cepx.cep("05010000", providers=["brasilapi", "viacep"])

    assert address.provider == "viacep"


@respx.mock
async def test_async_connection_error():
    respx.get(BRASILAPI_URL).mock(side_effect=httpx.ConnectError("boom"))
    with pytest.raises(cepx.CepxError) as info:
        await cepx.acep("05010000", providers=["brasilapi"])
    assert info.value.errors[0].message == (
        "Failed to connect to the BrasilAPI provider."
    )


@respx.mock
async def test_async_first_success_cancels_pending():
    async def slow(request):
        await asyncio.sleep(1)
        return httpx.Response(
            200,
            json={
                "cep": "05010-000",
                "logradouro": "Rua Caiubi",
                "bairro": "Perdizes",
                "localidade": "São Paulo",
                "uf": "SP",
            },
        )

    respx.get(BRASILAPI_URL).respond(
        json={
            "cep": "05010000",
            "state": "SP",
            "city": "São Paulo",
            "neighborhood": "Perdizes",
            "street": "Rua Caiubi",
        }
    )
    respx.get(VIACEP_URL).mock(side_effect=slow)

    address = await asyncio.wait_for(
        cepx.acep("05010000", providers=["brasilapi", "viacep"]),
        timeout=0.5,
    )

    assert address.provider == "brasilapi"


@respx.mock
def test_timeout_is_passed_through():
    route = respx.get(BRASILAPI_URL).mock(
        side_effect=httpx.ConnectTimeout("slow")
    )
    with pytest.raises(cepx.CepxError):
        cepx.cep("05010000", providers=["brasilapi"], timeout=0.5)
    assert route.called


def test_sync_http_client_is_reused_across_calls():
    from cepx._core import _shared_sync_client

    # The http2 client is built once and reused (constructing one costs ms).
    assert _shared_sync_client() is _shared_sync_client()
