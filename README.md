# cepx

Brazilian CEP (postal code) lookup integrated with the Correios, ViaCEP,
WideNet, and BrasilAPI services. Python port of
[`cep-promise`](https://github.com/BrasilAPI/cep-promise), with both
synchronous and asynchronous APIs.

Providers are queried concurrently and the **first successful** response wins.
The lookup only fails once **every** provider fails, aggregating each error.

## Usage

```python
import cepx

cepx.cep("05010000")
# Address(cep='05010000', state='SP', city='São Paulo',
#         neighborhood='Perdizes', street='Rua Caiubi', provider='brasilapi')

cepx.cep(5010000)                                  # ints are left-padded
cepx.cep("05010000", providers=["viacep"])         # restrict providers
cepx.cep("05010000", timeout=5.0)                  # per-provider timeout (s)
```

```python
import asyncio
import cepx

asyncio.run(cepx.acep("05010000"))
```

## Offline lookups

Install the `local` extra to resolve CEPs with **no network access**, against a
prebuilt database that ships with the
[`cepx-data`](https://github.com/moc-guardian/cepx-data) package:

```bash
pip install "cepx[local]"
```

```python
import cepx

cepx.cep("05010000", providers=["local"])
# Address(cep='05010000', ..., provider='local')
```

The `local` provider is opt-in (not part of the default provider race). It is
found automatically once `cepx-data` is installed; set `CEPX_DB` to point at a
different SQLite database if you build your own. The bundled data is derived
from [CEP Aberto](https://www.cepaberto.com/) under the ODbL.

## Errors

`cepx.CepxError` is raised with a `type` of either `"validation_error"`
(bad input, before any request) or `"provider_error"` (all providers failed).
Its `errors` list holds the underlying `cepx.ProviderError` entries.

## Development

```bash
uv sync
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run ty check
uv run pre-commit install
```
