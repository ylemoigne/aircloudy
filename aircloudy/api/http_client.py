from __future__ import annotations

import logging
from typing import Literal

import aiohttp
from aiohttp import TCPConnector

from aircloudy.contants import DEFAULT_REST_API_HOST, SSL_CONTEXT, TokenSupplier
from aircloudy.errors import ConnectionFailed

from .http_client_models import HttpResponse

logger = logging.getLogger(__name__)


async def create_headers(
    host: str, additional_headers: dict[str, str] | None = None, token_supplier: TokenSupplier | None = None
) -> dict[str, str]:
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json; charset=UTF-8",
        "Host": host,
        "User-Agent": "okhttp/4.2.2",
    }

    if token_supplier is not None:
        headers["Authorization"] = f"Bearer {await token_supplier()}"

    if additional_headers is not None:
        headers.update(additional_headers)

    return headers


async def perform_request(
    method: Literal["GET", "POST", "PUT"],
    url: str,
    additional_headers: dict[str, str] | None = None,
    body: object | None = None,
    token_supplier: TokenSupplier | None = None,
    do_not_raise_exception_on: tuple[int, ...] = (200,),
    host: str = DEFAULT_REST_API_HOST,
    port: int = 443,
) -> HttpResponse:
    logger.debug("Perform %s %s on %s:%d, %s", method, url, host, port, body)
    try:
        async with (
            aiohttp.ClientSession(f"https://{host}:{port}", connector=TCPConnector(ssl=SSL_CONTEXT)) as session,
            session.request(
                method, url, json=body, headers=await create_headers(host, additional_headers, token_supplier)
            ) as response_http,
        ):
            response_status = response_http.status
            response_body = await response_http.text()
            logger.debug("Response status=%d body=%s", response_status, response_body)

            if response_status not in do_not_raise_exception_on:
                raise Exception(f"Call failed (status={response_status} body={response_body})")

            return HttpResponse(response_status, response_body)
    except aiohttp.client_exceptions.ClientConnectorError as e:
        raise ConnectionFailed(f"Failed to connect to host: {host}") from e
