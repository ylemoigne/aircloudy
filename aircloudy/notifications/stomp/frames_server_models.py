from __future__ import annotations

from aircloudy.utils import to_int

from .frames_models import StompFrame


class ConnectedFrame(StompFrame):
    version: str
    heart_beat: tuple[int, int] | None
    session: str | None
    server: str | None

    def __init__(self, frame: StompFrame) -> None:
        StompFrame.__init__(
            self,
            frame.message,
            frame.headers,
            frame.body,
        )
        self.version = frame.headers["version"]

        heart_beat_as_string: str = frame.headers["heart-beat"]
        if heart_beat_as_string is not None:
            heart_beat_min, heart_beat_max = heart_beat_as_string.split(",", 2)
            self.heart_beat = (int(heart_beat_min), int(heart_beat_max))

        self.session = frame.headers.get("session")
        self.server = frame.headers.get("server")


class MessageFrame(StompFrame):
    destination: str
    message_id: str
    subscription: str
    ack: str | None
    content_type: str | None
    content_length: int | None

    def __init__(self, frame: StompFrame) -> None:
        StompFrame.__init__(
            self,
            frame.message,
            frame.headers,
            frame.body,
        )
        self.destination = frame.headers["destination"]
        self.message_id = frame.headers["message-id"]
        self.subscription = frame.headers["subscription"]
        self.ack = frame.headers.get("ack")
        self.content_type = frame.headers.get("content-type")
        self.content_length = to_int(frame.headers.get("content-length"))


class ReceiptFrame(StompFrame):
    receipt_id: str

    def __init__(self, frame: StompFrame) -> None:
        StompFrame.__init__(
            self,
            frame.message,
            frame.headers,
            frame.body,
        )
        self.receipt_id = frame.headers["receipt-id"]


class ErrorFrame(StompFrame):
    error_message: str | None
    content_type: str | None
    content_length: int | None

    def __init__(self, frame: StompFrame) -> None:
        StompFrame.__init__(
            self,
            frame.message,
            frame.headers,
            frame.body,
        )
        self.error_message = frame.headers.get("message")
        self.content_type = frame.headers.get("content-type")
        self.content_length = to_int(frame.headers.get("content-length"))
