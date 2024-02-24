import logging
from typing import Literal, Optional, Tuple

import aiohttp
from aiohttp import TCPConnector

from aircloudy.contants import DEFAULT_REST_API_HOST, SSL_CONTEXT
from aircloudy.errors import ConnectionFailed

from .http_client_models import HttpResponse

logger = logging.getLogger(__name__)


def create_headers(host: str, token: Optional[str] = None) -> dict[str, str]:
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json; charset=UTF-8",
        "Host": host,
        "User-Agent": "okhttp/4.2.2",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


async def perform_request(
    method: Literal["GET", "POST", "PUT"],
    url: str,
    body: Optional[object] = None,
    do_not_raise_exception_on: Tuple[int, ...] = (200,),
    token: Optional[str] = None,
    host: str = DEFAULT_REST_API_HOST,
    port: int = 443,
) -> HttpResponse:
    logger.debug("Perform %s %s on %s:%d", method, url, host, port)
    try:
        async with aiohttp.ClientSession(
            f"https://{host}:{port}", connector=TCPConnector(ssl=SSL_CONTEXT)
        ) as session, session.request(method, url, json=body, headers=create_headers(host, token)) as response_http:
            response_status = response_http.status
            response_body = await response_http.text()
            logger.debug("Response status=%d body=%s", response_status, response_body)

            if response_status not in do_not_raise_exception_on:
                raise Exception(f"Call failed (status={response_status} body={response_body}")

            return HttpResponse(response_status, response_body)
    except aiohttp.client_exceptions.ClientConnectorError as e:
        raise ConnectionFailed(f"Failed to connect to host: {host}") from e
