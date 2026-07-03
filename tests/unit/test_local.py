from __future__ import annotations

import sqlite3

import pytest

import cepx
from cepx.providers.local import LocalProvider

pytestmark = pytest.mark.unit

# Two ranges with a gap between them; 05010000..05010999 is São Paulo/Perdizes.
_ROWS = [
    (5010000, 5010999, "SP|São Paulo|Perdizes|Rua Caiubi"),
    (1000000, 1000500, "SP|São Paulo|Sé|Praça da Sé"),
]


def _build_db(path: str) -> None:
    con = sqlite3.connect(path)

    con.execute("CREATE TABLE names (id INTEGER PRIMARY KEY, name TEXT)")

    con.execute(
        "CREATE TABLE ranges (start INTEGER PRIMARY KEY, end INTEGER, "
        "name_id INTEGER)"
    )

    for i, (start, end, name) in enumerate(_ROWS):
        con.execute(
            "INSERT INTO names (id, name) VALUES (?, ?)",
            (i, name),
        )

        con.execute(
            "INSERT INTO ranges (start, end, name_id) VALUES (?, ?, ?)",
            (start, end, i),
        )

    con.commit()
    con.close()


@pytest.fixture
def db_path(tmp_path):
    path = tmp_path / "cepx.sqlite"
    _build_db(str(path))
    return str(path)


def test_local_lookup_hit(db_path, monkeypatch):
    monkeypatch.setenv("CEPX_DB", db_path)

    address = cepx.cep("05010000", providers=["local"])

    assert address == cepx.Address(
        cep="05010000",
        state="SP",
        city="São Paulo",
        neighborhood="Perdizes",
        street="Rua Caiubi",
        provider="local",
    )


def test_local_lookup_within_range(db_path):
    provider = LocalProvider(db_path)
    address = provider._lookup("05010500")
    assert address.city == "São Paulo"
    assert address.street == "Rua Caiubi"
    # a second lookup reuses the cached (thread-local) connection
    again = provider._lookup("05010999")
    assert again.city == "São Paulo"


def test_local_lookup_miss_between_ranges(db_path, monkeypatch):
    monkeypatch.setenv("CEPX_DB", db_path)
    with pytest.raises(cepx.CepxError) as info:
        cepx.cep("07000000", providers=["local"])
    assert info.value.errors[0].message == (
        "CEP not found in the local database."
    )


def test_local_lookup_below_all_ranges(db_path, monkeypatch):
    monkeypatch.setenv("CEPX_DB", db_path)
    with pytest.raises(cepx.CepxError) as info:
        cepx.cep("00500000", providers=["local"])
    assert info.value.errors[0].provider == "local"


def test_local_missing_database_is_a_provider_error(tmp_path, monkeypatch):
    monkeypatch.setenv("CEPX_DB", str(tmp_path / "does-not-exist.sqlite"))
    with pytest.raises(cepx.CepxError) as info:
        cepx.cep("05010000", providers=["local"])
    assert "not found at" in info.value.errors[0].message


def test_local_is_selectable_but_not_in_default_race():
    available = cepx.get_available_providers()
    assert "local" in available
    from cepx.providers import DEFAULT_PROVIDER_NAMES

    assert "local" not in DEFAULT_PROVIDER_NAMES


async def test_local_async(db_path, monkeypatch):
    monkeypatch.setenv("CEPX_DB", db_path)
    address = await cepx.acep("05010999", providers=["local"])
    assert address.provider == "local"
    assert address.cep == "05010999"


def test_http_provider_requires_a_client():
    from cepx.providers.brasilapi import BrasilAPI

    with pytest.raises(RuntimeError, match="requires an httpx client"):
        BrasilAPI().resolve_sync("05010000", None, 1.0)


async def test_http_provider_requires_a_client_async():
    from cepx.providers.brasilapi import BrasilAPI

    with pytest.raises(RuntimeError, match="requires an httpx client"):
        await BrasilAPI().resolve_async("05010000", None, 1.0)
