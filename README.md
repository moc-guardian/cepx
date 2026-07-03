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
