#!/usr/bin/env python3
"""Benchmark the offline LocalProvider, like geoip2fast's speed test.

geoip2fast reports "lookups per second" over a batch of random inputs. We do
the same over random CEPs -- a mix of real hits sampled from the DB and random
misses -- but across three layers, so you can see where the time goes:

  1. raw indexed SQL on a single reused connection  (the ceiling)
  2. LocalProvider._lookup                           (opens a connection/call)
  3. cepx.cep(providers=["local"])                   (full public path)

The gap between (1) and (2) is the per-call connection cost; the gap between
(2) and (3) is input validation + the httpx.Client that _core still builds.

Usage:
  CEPX_DB=path/to/cepx.sqlite python tools/bench_local.py [--n 50000]
  python tools/bench_local.py --db path/to/cepx.sqlite --n 200000
"""

from __future__ import annotations

import argparse
import os
import random
import sqlite3
import time
from collections.abc import Callable

import cepx
from cepx.providers.local import LocalProvider

_LOOKUP_SQL = (
    "SELECT s.sigla, c.nome, n.nome, st.nome FROM ceps "
    "JOIN states s ON s.id = ceps.uf_id "
    "JOIN cities c ON c.id = ceps.city_id "
    "JOIN neighborhoods n ON n.id = ceps.neigh_id "
    "JOIN streets st ON st.id = ceps.street_id "
    "WHERE ceps.cep = ?"
)


def _resolve_db(db_arg: str | None) -> str:
    db = db_arg or os.environ.get("CEPX_DB") or LocalProvider().db_path

    if not db or not os.path.exists(db):
        raise SystemExit(f"database not found: {db} (set CEPX_DB or --db)")

    return db


def _load_starts(db: str) -> list[int]:
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)

    try:
        return [row[0] for row in con.execute("SELECT cep FROM ceps")]
    finally:
        con.close()


def _make_queries(
    starts: list[int],
    n: int,
    hit_ratio: float,
    rng: random.Random,
) -> list[str]:
    """A shuffled mix of guaranteed hits (real CEPs) and random misses."""
    queries: list[str] = []

    for _ in range(n):
        if starts and rng.random() < hit_ratio:
            queries.append(str(rng.choice(starts)).zfill(8))
        else:
            queries.append(str(rng.randint(0, 99_999_999)).zfill(8))

    return queries


def _bench(
    label: str,
    lookup: Callable[[str], bool],
    queries: list[str],
) -> None:
    # warm-up (page cache, imports, connection) -- excluded from timing.
    for q in queries[: min(1000, len(queries))]:
        lookup(q)

    latencies = [0.0] * len(queries)
    hits = 0
    start = time.perf_counter()

    for i, q in enumerate(queries):
        t0 = time.perf_counter()
        found = lookup(q)
        latencies[i] = time.perf_counter() - t0
        hits += found

    total = time.perf_counter() - start

    latencies.sort()

    def pct(p: float) -> float:
        return latencies[min(len(latencies) - 1, int(p * len(latencies)))]

    print(
        f"  {label:<26} {len(queries) / total:>12,.0f}/s  "
        f"avg {total / len(queries) * 1e6:7.2f}us  "
        f"p50 {pct(0.50) * 1e6:6.2f}  p95 {pct(0.95) * 1e6:7.2f}  "
        f"p99 {pct(0.99) * 1e6:8.2f}  (hits {hits:,})"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument(
        "--db",
        default=None,
        help="path to cepx.sqlite",
    )

    parser.add_argument(
        "--n",
        type=int,
        default=50_000,
        help="lookups (50k)",
    )

    parser.add_argument(
        "--hit-ratio",
        type=float,
        default=0.5,
        help="fraction of queries that are real CEPs (default 0.5)",
    )

    args = parser.parse_args()

    db = _resolve_db(args.db)
    starts = _load_starts(db)
    rng = random.Random(7)
    queries = _make_queries(starts, args.n, args.hit_ratio, rng)

    print(
        f"db={db}\n{len(starts):,} CEPs in DB, {args.n:,} lookups, "
        f"hit_ratio={args.hit_ratio}\n"
    )

    # Layer 1: raw SQL on one reused connection.
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)

    def raw(cep: str) -> bool:
        return con.execute(_LOOKUP_SQL, (int(cep),)).fetchone() is not None

    # Layer 2: the shipped provider (connection per call).
    provider = LocalProvider(db)

    def provider_lookup(cep: str) -> bool:
        try:
            provider._lookup(cep)
            return True
        except cepx.ProviderError:
            return False

    # Layer 3: full public path.
    prev = os.environ.get("CEPX_DB")
    os.environ["CEPX_DB"] = db

    def public(cep: str) -> bool:
        try:
            cepx.cep(cep, providers=["local"])

            return True
        except cepx.CepxError:
            return False

    try:
        _bench("raw SQL (reused conn)", raw, queries)
        _bench("LocalProvider._lookup", provider_lookup, queries)
        _bench("cepx.cep(local)", public, queries)
    finally:
        con.close()

        if prev is None:
            os.environ.pop("CEPX_DB", None)
        else:
            os.environ["CEPX_DB"] = prev


if __name__ == "__main__":
    main()
