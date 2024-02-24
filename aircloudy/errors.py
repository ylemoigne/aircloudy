import json
from typing import Optional


class IllegalStateException(Exception):
    def __init__(self, message: str) -> None:
        Exception.__init__(self, message)


class TooManyRequestsException(Exception):
    error_type: str
    error_desc: str
    error_stack_trace: Optional[str]
    error_code: Optional[str]

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
