import json

from aircloudy.contants import DEFAULT_REST_API_HOST

from ..errors import AuthenticationFailedException
from .http_client import perform_request
from .iam_models import AuthenticationSuccess, UserProfile


async def perform_login(
    email: str, password: str, host: str = DEFAULT_REST_API_HOST, port: int = 443
) -> AuthenticationSuccess:
    response = await perform_request(
        "POST",
        "/iam/auth/sign-in",
        {
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


async def fetch_profile(token: str, host: str = DEFAULT_REST_API_HOST, port: int = 443) -> UserProfile:
    response = await perform_request("GET", "/iam/user/v2/who-am-i", token=token, host=host, port=port)

    return json.loads(response.body, object_hook=UserProfile)
