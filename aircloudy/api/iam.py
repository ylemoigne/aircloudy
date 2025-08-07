import json
import logging

from aircloudy.contants import DEFAULT_REST_API_HOST, TokenSupplier

from ..errors import AuthenticationFailedException
from .http_client import perform_request
from .iam_models import AuthenticationSuccess, TokenRefreshSuccess, UserProfile

logger = logging.getLogger(__name__)


async def perform_login(
    email: str, password: str, host: str = DEFAULT_REST_API_HOST, port: int = 443
) -> AuthenticationSuccess:
    response = await perform_request(
        "POST",
        "/iam/auth/sign-in",
        body={
            "email": email,
            "password": password,
        },
        do_not_raise_exception_on=(200, 401),
        host=host,
        port=port,
    )

    if response.status == 401:
        raise AuthenticationFailedException(f"Autentication Failed: {response.body_as_json.get('errorState')}")

    return json.loads(response.body, object_hook=AuthenticationSuccess)


async def fetch_profile(
    token_supplier: TokenSupplier, host: str = DEFAULT_REST_API_HOST, port: int = 443
) -> UserProfile:
    response = await perform_request(
        "GET", "/iam/user/v2/who-am-i", token_supplier=token_supplier, host=host, port=port
    )

    return json.loads(response.body, object_hook=UserProfile)


async def refresh_token(
    refresh_token_supplier: TokenSupplier, host: str = DEFAULT_REST_API_HOST, port: int = 443
) -> TokenRefreshSuccess:
    response = await perform_request(
        "POST",
        "/iam/auth/refresh-token",
        additional_headers={"isRefreshToken": "true"},
        token_supplier=refresh_token_supplier,
        host=host,
        port=port,
    )

    return json.loads(response.body, object_hook=TokenRefreshSuccess)
