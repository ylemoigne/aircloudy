from typing import Optional


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
