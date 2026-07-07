from __future__ import annotations

import sqlite3
import sys
import types

import pytest

import cepx
from cepx.providers.local import LocalProvider

pytestmark = pytest.mark.unit

# (cep, uf, city, neighborhood, street), mirrors the cepx-data schema.
_CEPS = [
    (5010000, "SP", "São Paulo", "Perdizes", "Rua Caiubi"),
    (1001000, "SP", "São Paulo", "Sé", "Praça da Sé"),
]

_DDL = """
CREATE TABLE states (
    id INTEGER PRIMARY KEY,
    sigla TEXT NOT NULL
);

CREATE TABLE cities (
    id INTEGER PRIMARY KEY,
    nome TEXT NOT NULL
);

CREATE TABLE neighborhoods (
    id INTEGER PRIMARY KEY,
    nome TEXT NOT NULL
);

CREATE TABLE streets (
    id INTEGER PRIMARY KEY,
    nome TEXT NOT NULL
);

CREATE TABLE ceps (
    cep INTEGER PRIMARY KEY,
    uf_id INTEGER,
    city_id INTEGER,
    neigh_id INTEGER,
    street_id INTEGER
);
"""


def _build_db(path: str) -> None:
    con = sqlite3.connect(path)
    con.executescript(_DDL)

    dims: dict[str, dict[str, int]] = {
        "states": {},
        "cities": {},
        "neighborhoods": {},
        "streets": {},
    }

    def intern(table: str, value: str) -> int:
        mapping = dims[table]

        if value not in mapping:
            mapping[value] = len(mapping)

        return mapping[value]

    for cep, uf, city, neigh, street in _CEPS:
        con.execute(
            "INSERT INTO ceps VALUES (?, ?, ?, ?, ?)",
            (
                cep,
                intern("states", uf),
                intern("cities", city),
                intern("neighborhoods", neigh),
                intern("streets", street),
            ),
        )

    for table, col in (
        ("states", "sigla"),
        ("cities", "nome"),
        ("neighborhoods", "nome"),
        ("streets", "nome"),
    ):
        con.executemany(
            f"INSERT INTO {table} (id, {col}) VALUES (?, ?)",
            ((i, value) for value, i in dims[table].items()),
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


def test_local_lookup_reuses_cached_connection(db_path):
    provider = LocalProvider(db_path)
    first = provider._lookup("05010000")

    assert first.street == "Rua Caiubi"
    # a second lookup reuses the cached (thread-local) connection
    second = provider._lookup("01001000")

    assert second.street == "Praça da Sé"


def test_local_absent_cep_is_a_miss(db_path, monkeypatch):
    monkeypatch.setenv("CEPX_DB", db_path)

    with pytest.raises(cepx.CepxError) as info:
        cepx.cep("07000000", providers=["local"])

    assert info.value.errors[0].message == (
        "CEP not found in the local database."
    )


def test_local_missing_database_file_is_a_provider_error(tmp_path, monkeypatch):
    monkeypatch.setenv("CEPX_DB", str(tmp_path / "does-not-exist.sqlite"))

    with pytest.raises(cepx.CepxError) as info:
        cepx.cep("05010000", providers=["local"])

    assert "not found at" in info.value.errors[0].message


def test_local_no_database_available(monkeypatch):
    # Neither CEPX_DB nor the cepx-data package is available.
    monkeypatch.delenv("CEPX_DB", raising=False)
    monkeypatch.setitem(sys.modules, "cepx_data", None)  # forces ImportError

    with pytest.raises(cepx.CepxError) as info:
        cepx.cep("05010000", providers=["local"])

    assert "cepx[local]" in info.value.errors[0].message


def test_local_discovers_bundled_cepx_data(db_path, monkeypatch):
    # Simulate the cepx-data package being installed and exposing db_path().
    monkeypatch.delenv("CEPX_DB", raising=False)
    fake = types.ModuleType("cepx_data")
    fake.db_path = lambda: db_path  # ty: ignore[unresolved-attribute]
    monkeypatch.setitem(sys.modules, "cepx_data", fake)

    assert LocalProvider().db_path == db_path

    address = cepx.cep("01001000", providers=["local"])

    assert address.city == "São Paulo"
    assert address.provider == "local"


def test_local_is_selectable_but_not_in_default_race():
    available = cepx.get_available_providers()

    assert "local" in available

    from cepx.providers import DEFAULT_PROVIDER_NAMES

    assert "local" not in DEFAULT_PROVIDER_NAMES


async def test_local_async(db_path, monkeypatch):
    monkeypatch.setenv("CEPX_DB", db_path)
    address = await cepx.acep("01001000", providers=["local"])

    assert address.provider == "local"
    assert address.cep == "01001000"


def test_http_provider_requires_a_client():
    from cepx.providers.brasilapi import BrasilAPI

    with pytest.raises(RuntimeError, match="requires an httpx client"):
        BrasilAPI().resolve_sync("05010000", None, 1.0)


async def test_http_provider_requires_a_client_async():
    from cepx.providers.brasilapi import BrasilAPI

    with pytest.raises(RuntimeError, match="requires an httpx client"):
        await BrasilAPI().resolve_async("05010000", None, 1.0)
