from __future__ import annotations

import asyncio
import datetime

import tzlocal

from aircloudy.contants import DEFAULT_REST_API_HOST
from aircloudy.utils import awaitable

from .iam import perform_login, refresh_token
from .iam_models import JWTToken


class AuthManager:
    _token_update_lock: asyncio.Lock
    _refresh_before_expiration: datetime.timedelta
    _email: str
    _password: str
    _host: str
    _port: int
    _token: JWTToken | None
    _refresh_token: JWTToken | None

    def __init__(self, email: str, password: str, host: str = DEFAULT_REST_API_HOST, port: int = 443) -> None:
        self._token_update_lock = asyncio.Lock()
        self._refresh_before_expiration = datetime.timedelta(minutes=1)
        self._email = email
        self._password = password
        self._host = host
        self._port = port
        self._token = None
        self._refresh_token = None

    async def token(self) -> str:
        async with self._token_update_lock:
            if self._token is None:
                return await self._perform_login()

            now = datetime.datetime.now(tzlocal.get_localzone()).astimezone(datetime.UTC)
            limit_date = self._token.exp - self._refresh_before_expiration
            if now <= limit_date:
                return self._token.value

            if self._refresh_token is not None and self._refresh_token.exp <= limit_date:
                token = awaitable(self._refresh_token.value)
                refresh_result = await refresh_token(lambda: token, self._host, self._port)

                self._token = refresh_result.token
                self._refresh_token = refresh_result.refresh_token
                return refresh_result.token.value

            return await self._perform_login()

    async def _perform_login(self) -> str:
        login_result = await perform_login(self._email, self._password, self._host, self._port)
        self._token = login_result.token
        self._refresh_token = login_result.refresh_token
        return login_result.token.value
