from __future__ import annotations

import os
import sqlite3
import threading

import httpx

from cepx._types import Address
from cepx.errors import ProviderError
from cepx.providers.base import Provider

##──── Default location of the bundled database. Override with the CEPX_DB env
##──── variable or by passing db_path to LocalProvider(). The database itself
##──── is built by tools/build_cep_db.py from a source address dataset.
DEFAULT_DB_PATH = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "data", "cepx.sqlite")
)

##──── Bisect-equivalent in SQL: the largest range whose start is <= the CEP,
##──── then a bounds-check against that range's end (done in Python below).
_LOOKUP_SQL = (
    "SELECT r.end, n.name "
    "FROM ranges r JOIN names n ON n.id = r.name_id "
    "WHERE r.start <= ? "
    "ORDER BY r.start DESC LIMIT 1"
)

##──── Read-only connections are cached per (thread, db_path): opening one per
##──── lookup dominates the cost, and a connection is not safe to share across
##──── threads, so thread-local storage gives us reuse without that hazard.
_local = threading.local()


def _get_connection(db_path: str) -> sqlite3.Connection:
    connections: dict[str, sqlite3.Connection] | None = getattr(
        _local, "connections", None
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
    """Offline provider: resolves a CEP against a bundled SQLite database.

    Ranges are stored as `(start, end, name_id)` with an index on `start`,
    and locality/street names are deduplicated into a `names` table. A lookup
    is a single indexed range query — no network access.
    """

    name = "local"
    connection_error_message = "Failed to read the local CEP database."

    def __init__(self, db_path: str | None = None) -> None:
        self.db_path = db_path or os.environ.get("CEPX_DB") or DEFAULT_DB_PATH

    def _lookup(self, cep: str) -> Address:
        cep_int = int(cep)
        connection = _get_connection(self.db_path)
        row = connection.execute(_LOOKUP_SQL, (cep_int,)).fetchone()

        if row is None or cep_int > row[0]:
            raise ProviderError(
                "CEP not found in the local database.",
                self.name,
            )

        state, city, neighborhood, street = row[1].split("|")

        return self.build_address(
            cep=cep,
            state=state,
            city=city,
            neighborhood=neighborhood,
            street=street,
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
