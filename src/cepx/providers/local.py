from __future__ import annotations

import functools
import importlib
import os
import sqlite3
import threading

import httpx

from cepx._types import Address
from cepx.errors import ProviderError
from cepx.providers.base import Provider

_LOOKUP_SQL = (
    "SELECT s.sigla, c.nome, n.nome, st.nome "
    "FROM ceps "
    "JOIN states s ON s.id = ceps.uf_id "
    "JOIN cities c ON c.id = ceps.city_id "
    "JOIN neighborhoods n ON n.id = ceps.neigh_id "
    "JOIN streets st ON st.id = ceps.street_id "
    "WHERE ceps.cep = ?"
)

# Read-only connections are cached per (thread, db_path): opening one per
# lookup dominates the cost, and a connection is not safe to share across
# threads, so thread-local storage gives us reuse without that hazard.
_local = threading.local()


@functools.lru_cache(maxsize=1)
def _bundled_db_path() -> str | None:
    """Path to the database shipped by cepx-data (the `cepx[local]` extra).

    Cached: the installed package location is fixed for the process lifetime,
    and `importlib.resources` resolution is the dominant per-lookup cost. Call
    `_bundled_db_path.cache_clear()` if the environment changes (tests do).
    """
    try:
        cepx_data = importlib.import_module("cepx_data")
    except ImportError:
        return None

    return cepx_data.db_path()


def _discover_db_path(explicit: str | None) -> str | None:
    """Resolve the database path: explicit arg, then CEPX_DB, then cepx-data."""
    if explicit:
        return explicit

    env = os.environ.get("CEPX_DB")

    if env:
        return env

    return _bundled_db_path()


def _get_connection(db_path: str) -> sqlite3.Connection:
    connections: dict[str, sqlite3.Connection] | None = getattr(
        _local,
        "connections",
        None,
    )

    if connections is None:
        connections = _local.connections = {}

    connection = connections.get(db_path)

    if connection is None:
        if not os.path.exists(db_path):
            raise ProviderError(
                f"Local CEP database not found at {db_path}.",
                LocalProvider.name,
            )

        connection = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        connections[db_path] = connection

    return connection


class LocalProvider(Provider):
    """Offline provider: resolves a CEP against a local SQLite database.

    The database is the one shipped by the `cepx-data` package (installed via
    `pip install "cepx[local]"`); pass `db_path` or set `CEPX_DB` to use a
    different file.
    """

    name = "local"
    connection_error_message = "Failed to read the local CEP database."
    in_default_set = False

    def __init__(self, db_path: str | None = None) -> None:
        self.db_path = _discover_db_path(db_path)

    def _lookup(self, cep: str) -> Address:
        if self.db_path is None:
            raise ProviderError(
                "No local CEP database available. Install 'cepx[local]' "
                "or set CEPX_DB to a database path.",
                self.name,
            )

        connection = _get_connection(self.db_path)
        row = connection.execute(_LOOKUP_SQL, (int(cep),)).fetchone()

        if row is None:
            raise ProviderError(
                "CEP not found in the local database.",
                self.name,
            )

        state, city, neighborhood, street = row

        # The schema guarantees non-null, already-clean strings (and `cep` is
        # the padded lookup key), so build the Address directly and skip the
        # defensive normalization build_address() does for untrusted responses.
        return Address(
            cep=cep,
            state=state,
            city=city,
            neighborhood=neighborhood,
            street=street,
            provider=self.name,
        )

    def resolve_sync(
        self,
        cep: str,
        client: httpx.Client | None,
        timeout: float,
    ) -> Address:
        return self._lookup(cep)

    async def resolve_async(
        self,
        cep: str,
        client: httpx.AsyncClient | None,
        timeout: float,
    ) -> Address:
        return self._lookup(cep)
