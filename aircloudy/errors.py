from __future__ import annotations

import json


class IllegalStateException(Exception):
    def __init__(self, message: str) -> None:
        Exception.__init__(self, message)


class UnitIsOfflineException(IllegalStateException):
    def __init__(self) -> None:
        super().__init__("Unit is offline")


class TooManyRequestsException(Exception):
    error_type: str
    error_desc: str
    error_stack_trace: str | None
    error_code: str | None

    def __init__(self, body: str) -> None:
        data = json.loads(body)
        self.error_type = data["type"]
        self.error_desc = data["desc"]
        self.error_stack_trace = data.get("strackTrace")
        self.error_code = data.get("code")
        Exception.__init__(self, f"Too many requests: {self.error_desc}")


class InteriorUnitNotFoundException(Exception):
    def __init__(self, message: str) -> None:
        Exception.__init__(self, message)


class CommandFailedException(Exception):
    def __init__(self, message: str) -> None:
        Exception.__init__(self, message)


class InvalidArgumentException(Exception):
    def __init__(self, message: str) -> None:
        Exception.__init__(self, message)


class AuthenticationFailedException(Exception):
    def __init__(self, message: str) -> None:
        Exception.__init__(self, message)


class ConnectionFailed(Exception):
    def __init__(self, message: str) -> None:
        Exception.__init__(self, message)
