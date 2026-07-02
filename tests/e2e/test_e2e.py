from __future__ import annotations

import pytest

import cepx
from tests.conftest import PROVIDER_NAMES

pytestmark = pytest.mark.e2e


def _assert_paulista(address):
    assert address.cep == "05010000"
    assert address.state == "SP"
    assert address.city == "São Paulo"
    assert address.provider in PROVIDER_NAMES


def test_valid_string():
    _assert_paulista(cepx.cep("05010000"))


def test_valid_int_is_left_padded():
    _assert_paulista(cepx.cep(5010000))


async def test_valid_string_async():
    _assert_paulista(await cepx.acep("05010000"))


def test_invalid_cep_rejects_with_validation_error():
    with pytest.raises(cepx.CepxError) as info:
        cepx.cep("123456789")
    assert info.value.type == "validation_error"
