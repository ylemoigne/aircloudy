from __future__ import annotations

import ssl

import pytest
import trustme


@pytest.fixture(scope="session")
def httpserver_ssl_context() -> ssl.SSLContext | None:
    ca = trustme.CA()
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    localhost_cert = ca.issue_cert("localhost")
    localhost_cert.configure_cert(context)
    return context
