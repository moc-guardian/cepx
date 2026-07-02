from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import cast

import httpx

from cepx._types import Address
from cepx._validation import prepare
from cepx.errors import CepxError, ProviderError
from cepx.providers import DEFAULT_TIMEOUT, Provider


def cep(
    cep_raw: str | int,
    *,
    providers: list[str] | None = None,
    timeout: float = DEFAULT_TIMEOUT,
) -> Address:
    padded, resolved = prepare(cep_raw, providers)

    return _first_success_sync(resolved, padded, timeout)


async def acep(
    cep_raw: str | int,
    *,
    providers: list[str] | None = None,
    timeout: float = DEFAULT_TIMEOUT,
) -> Address:
    padded, resolved = prepare(cep_raw, providers)

    return await _first_success_async(resolved, padded, timeout)


def _wrap_error(provider: Provider, error: Exception) -> ProviderError:
    if isinstance(error, httpx.HTTPError):
        message = provider.connection_error_message
    else:
        message = f"Malformed response from the {provider.name} provider."

    return ProviderError(message, provider.name)


def _run_sync(
    client: httpx.Client,
    provider: Provider,
    cep: str,
    timeout: float,
) -> Address:
    try:
        spec = provider.build_request(cep)

        response = client.request(
            spec.method,
            spec.url,
            headers=spec.headers,
            content=spec.content,
            data=spec.data,
            timeout=timeout,
        )
        return provider.parse(response.status_code, response.text)
    except ProviderError:
        raise
    except Exception as error:
        raise _wrap_error(provider, error) from error


async def _run_async(
    client: httpx.AsyncClient,
    provider: Provider,
    cep: str,
    timeout: float,
) -> Address:
    try:
        spec = provider.build_request(cep)

        response = await client.request(
            spec.method,
            spec.url,
            headers=spec.headers,
            content=spec.content,
            data=spec.data,
            timeout=timeout,
        )
        return provider.parse(response.status_code, response.text)
    except ProviderError:
        raise
    except Exception as error:
        raise _wrap_error(provider, error) from error


def _first_success_sync(
    providers: list[Provider],
    cep: str,
    timeout: float,
) -> Address:
    errors: list[ProviderError | None] = [None] * len(providers)

    with httpx.Client(http2=True) as client:
        executor = ThreadPoolExecutor(max_workers=len(providers))

        try:
            futures = {
                executor.submit(_run_sync, client, provider, cep, timeout): i
                for i, provider in enumerate(providers)
            }

            for future in as_completed(futures):
                try:
                    return future.result()
                except ProviderError as error:
                    errors[futures[future]] = error
        finally:
            executor.shutdown(wait=False, cancel_futures=True)

    raise _aggregate(errors)


async def _first_success_async(
    providers: list[Provider],
    cep: str,
    timeout: float,
) -> Address:
    async with httpx.AsyncClient(http2=True) as client:
        tasks = [
            asyncio.ensure_future(_run_async(client, provider, cep, timeout))
            for provider in providers
        ]

        index = {task: i for i, task in enumerate(tasks)}
        errors: list[ProviderError | None] = [None] * len(tasks)
        pending = set(tasks)

        while pending:
            done, pending = await asyncio.wait(
                pending,
                return_when=asyncio.FIRST_COMPLETED,
            )

            for task in done:
                error = task.exception()

                if error is None:
                    for other in pending:
                        other.cancel()

                    if pending:
                        await asyncio.gather(*pending, return_exceptions=True)

                    return task.result()

                errors[index[task]] = cast(ProviderError, error)

    raise _aggregate(errors)


def _aggregate(errors: list[ProviderError | None]) -> CepxError:
    return CepxError(
        "All CEP providers returned an error.",
        "provider_error",
        [error for error in errors if error is not None],
    )
