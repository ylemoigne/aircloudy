import ssl
from typing import Optional

import pytest
import trustme


@pytest.fixture(scope="session")
def httpserver_ssl_context() -> Optional[ssl.SSLContext]:
    ca = trustme.CA()
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    localhost_cert = ca.issue_cert("localhost")
    localhost_cert.configure_cert(context)
    return context
