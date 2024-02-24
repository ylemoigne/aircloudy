import http.client
import json

from aircloudy.contants import DEFAULT_REST_API_HOST, SSL_CONTEXT

from .common import create_headers
from .iam_models import AuthenticationSuccess, UserProfile


def perform_login(
    email: str, password: str, host: str = DEFAULT_REST_API_HOST, port: int = 443
) -> AuthenticationSuccess:
    con = http.client.HTTPSConnection(host, port=port, context=SSL_CONTEXT)
    try:
        con.request(
            "POST",
            "/iam/auth/sign-in",
            json.dumps(
                {
                    "email": email,
                    "password": password,
                }
            ),
            headers=create_headers(host),
        )
        response_http = con.getresponse()
        response_status = response_http.status
        response_body = response_http.read().decode()

        if response_http.status != 200:
            raise Exception(f"Authentication failed (status={response_status} body={response_body}")

        return json.loads(response_body, object_hook=AuthenticationSuccess)
    finally:
        con.close()


def fetch_profile(token: str, host: str = DEFAULT_REST_API_HOST, port: int = 443) -> UserProfile:
    con = http.client.HTTPSConnection(host, port=port, context=SSL_CONTEXT)
    try:
        con.request("GET", "/iam/user/v2/who-am-i", headers=create_headers(host, token))
        response_http = con.getresponse()
        response_status = response_http.status
        response_body = response_http.read().decode()

        if response_http.status != 200:
            raise Exception(f"Fet user profile failed (status={response_status} body={response_body}")

        return json.loads(response_body, object_hook=UserProfile)
    finally:
        con.close()
