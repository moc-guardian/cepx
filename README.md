# cepx

Fast, offline-capable Brazilian CEP (postal code) lookup for Python, sync and
async.

Most CEP libraries are thin HTTP clients: every lookup is a round-trip to
Correios/ViaCEP/BrasilAPI, so you inherit their latency, rate limits, and
downtime. **cepx can resolve CEPs fully offline** from a prebuilt database
bundled with the package; in **microseconds**, with no network at all. When you
do want the network, it still races the same public providers and returns the
first successful answer.

## Why cepx

| | `local` (offline) | network providers |
|---|---|---|
| Latency | **~12 µs/lookup (~85k/s)** | one HTTP round-trip (tens–hundreds of ms) |
| Network | none | required |
| Rate limits / outages | none | subject to both |
| Works air-gapped | ✅ | ❌ |
| Coverage | ~1.14M CEPs (bundled) | whatever the live service returns |

The offline path is **thousands of times faster** than any HTTP lookup and
depends on nothing but your own process. Numbers above are the full public API
(`cepx.cep(...)`) against the complete national database, reproducible with
`make bench-local`.

## Offline lookups (the `local` provider)

Install the `local` extra (it pulls in
[`cepx-data`](https://github.com/moc-guardian/cepx-data)), which ships a prebuilt
SQLite database of ~1.14M CEPs:

```bash
pip install "cepx[local]"
```

```python
import cepx

cepx.cep("05010000", providers=["local"])
# Address(cep='05010000', state='SP', city='São Paulo',
#         neighborhood='Perdizes', street='Rua Caiubi', provider='local')
```

- **Zero network.** No requests, no rate limits, no third-party availability to
  depend on. Ideal for batch jobs, air-gapped environments, and hot paths.
- **Auto-discovered.** Once `cepx-data` is installed, the `local` provider finds
  the database automatically; set `CEPX_DB` to point at your own SQLite file.
- **Opt-in.** `local` is not part of the default provider race; request it
  explicitly with `providers=["local"]`.

### The database

`cepx[local]` adds one dependency, `cepx-data`, which bundles the CEP database:

- **~17 MiB download** (the wheel), **~42 MiB on disk** once installed — a
  one-time cost, no runtime downloads.
- **~1.14 million CEPs**: every UF, ~5.4k municipalities, ~31k neighborhoods,
  ~611k streets.
- Stored as a normalized SQLite database (one row per CEP keyed on the CEP
  itself, with UF/city/neighborhood/street deduplicated into lookup tables), so
  a query is a single indexed primary-key join.
- Data is derived from [CEP Aberto](https://www.cepaberto.com/) under the Open
  Database License (ODbL); `cepx-data` ships it and carries the attribution.

A CEP that isn't in the dataset is a clean miss (`provider_error`); fall back to
the network providers for full coverage if you need it.

### Offline-first with network fallback

Prefer the local database and only touch the network when a CEP isn't covered:

```python
def lookup(cep):
    try:
        return cepx.cep(cep, providers=["local"])   # ~microseconds on a hit
    except cepx.CepxError:
        return cepx.cep(cep)                        # network only on a miss
```

Do this rather than passing `providers=["local", ...]` in a single call: mixing
`local` with network providers forces the concurrent race path, which spins up a
thread pool and fires the network requests on *every* lookup, even the ones
`local` answers instantly (they're just cancelled once `local` wins). The
two-step form keeps hits fully offline at microsecond speed and only touches the
network on genuine misses.

## Network lookups

Without the extra (or when you don't request `local`), cepx queries the live
providers (Correios, ViaCEP, WideNet, BrasilAPI, and OpenCEP) **concurrently**, and the
**first successful** response wins. The lookup only fails once **every** provider
fails, aggregating each error.

```python
import cepx

cepx.cep("05010000")
# Address(cep='05010000', ..., provider='brasilapi')

cepx.cep(5010000)                            # ints are left-padded
cepx.cep("05010000", providers=["viacep"])   # restrict providers
cepx.cep("05010000", timeout=5.0)            # per-provider timeout (s)
```

```python
import asyncio
import cepx

asyncio.run(cepx.acep("05010000"))
```

## Errors

`cepx.CepxError` is raised with a `type` of either `"validation_error"`
(bad input, before any request) or `"provider_error"` (all providers failed).
Its `errors` list holds the underlying `cepx.ProviderError` entries.

## Development

```bash
make setup         # create the venv, install deps, install git hooks
make check         # unit tests + coverage + pre-commit (lint, format, types)
make bench-local   # benchmark the local provider against cepx-data
```

Run `make` with no target to see everything available.

## Credits

cepx began as a Python port of
[`cep-promise`](https://github.com/BrasilAPI/cep-promise) and keeps its
first-successful-provider model for network lookups.
