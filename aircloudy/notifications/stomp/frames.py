from __future__ import annotations

import json
from io import StringIO

from .frames_models import StompFrame


class WebsocketMessageParseException(Exception):
    error: str
    message: str
    line: str

    def __init__(self, error: str, message: str, line: str) -> None:
        Exception.__init__(self)
        self.error = error
        self.message = message
        self.line = line


def parse_stomp_frame(content: str) -> StompFrame | None:
    io = StringIO(content)

    first_line = io.readline()
    if first_line == "":
        raise WebsocketMessageParseException("Message is empty", content, first_line)
    if first_line == "\n":
        return None

    message = first_line.strip("\n")
    headers = {}
    while True:
        line = io.readline()
        if line in ("", "\n"):
            break

        header = line.strip("\n").split(":", 1)
        headers[header[0]] = header[1]

    body_raw = io.read().strip("\0")

    if body_raw == "":
        return StompFrame(message, headers, None)

    return StompFrame(message, headers, json.loads(body_raw))
