from __future__ import annotations

import pytest

import cepx
from cepx._validation import prepare

pytestmark = pytest.mark.unit


def test_int_is_left_padded():
    padded, _ = prepare(5010000, None)
    assert padded == "05010000"


def test_strips_non_digits():
    padded, _ = prepare("05010-000", None)
    assert padded == "05010000"


def test_none_providers_uses_all():
    _, providers = prepare("05010000", None)
    assert [s.name for s in providers] == [
        "correios",
        "correios-alt",
        "viacep",
        "widenet",
        "brasilapi",
    ]


def test_empty_providers_uses_all():
    _, providers = prepare("05010000", [])
    assert len(providers) == 5


def test_selected_providers_preserve_order():
    _, providers = prepare("05010000", ["viacep", "correios"])
    assert [s.name for s in providers] == ["viacep", "correios"]


@pytest.mark.parametrize("bad", [3.14, True, ["05010000"], {}])
def test_invalid_input_type(bad):
    with pytest.raises(cepx.CepxError) as info:
        cepx.cep(bad)
    error = info.value
    assert error.type == "validation_error"
    assert error.errors[0].provider == "cep_validation"


def test_input_too_long():
    with pytest.raises(cepx.CepxError) as info:
        cepx.cep("123456789")
    error = info.value
    assert error.type == "validation_error"
    assert error.message == "CEP must contain exactly 8 characters."
    assert error.errors[0].provider == "cep_validation"


@pytest.mark.parametrize("bad", ["viacep", 123, {}, lambda: None])
def test_providers_not_a_list(bad):
    with pytest.raises(cepx.CepxError) as info:
        cepx.cep("05010000", providers=bad)
    error = info.value
    assert error.type == "validation_error"
    assert error.errors[0].provider == "providers_validation"
    assert error.errors[0].message == (
        "The providers parameter must be a list."
    )


def test_unknown_provider():
    bad: list = [123, "viacep"]
    with pytest.raises(cepx.CepxError) as info:
        cepx.cep("05010000", providers=bad)
    error = info.value
    assert error.type == "validation_error"
    assert error.errors[0].provider == "providers_validation"
    assert '"123" is invalid' in error.errors[0].message
