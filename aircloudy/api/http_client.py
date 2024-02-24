import http.client
import json
import logging
import socket
from typing import Literal, Optional, Tuple

from aircloudy.contants import DEFAULT_REST_API_HOST, SSL_CONTEXT
from aircloudy.errors import ConnectionTimeout, HostnameResolutionFailed

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


def perform_request(
    method: Literal["GET", "POST", "PUT"],
    url: str,
    body: Optional[object] = None,
    do_not_raise_exception_on: Tuple[int, ...] = (200,),
    token: Optional[str] = None,
    host: str = DEFAULT_REST_API_HOST,
    port: int = 443,
) -> HttpResponse:
    con = http.client.HTTPSConnection(host, port=port, context=SSL_CONTEXT)
    try:
        logger.debug("Perform %s %s on %s:%d", method, url, host, port)
        con.request(
            method,
            url,
            body=json.dumps(body) if body is not None else None,
            headers=create_headers(host, token),
        )
        response_http = con.getresponse()
        response_status = response_http.status
        response_body = response_http.read().decode()
        logger.debug("Response status=%d body=%s", response_status, response_body)

        if response_status not in do_not_raise_exception_on:
            raise Exception(f"Call failed (status={response_status} body={response_body}")

        return HttpResponse(response_status, response_body)
    except socket.gaierror as e:
        match e.errno:
            case 8:
                raise HostnameResolutionFailed(f"Failed to resolve hostname: {host}") from e
            case 60:
                raise ConnectionTimeout(f"Failed to connect to host: {host}") from e
            case _:
                raise e
    finally:
        con.close()
