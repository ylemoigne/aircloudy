from __future__ import annotations

from .frames import parse_stomp_frame
from .frames_models import StompFrame
from .frames_server_models import ConnectedFrame, ErrorFrame, MessageFrame, ReceiptFrame


def parse_server_frame(content: str) -> StompFrame | None:
    stomp_frame = parse_stomp_frame(content)
    if stomp_frame is None:
        return None

    match stomp_frame.message:
        case "CONNECTED":
            return ConnectedFrame(stomp_frame)
        case "MESSAGE":
            return MessageFrame(stomp_frame)
        case "RECEIPT":
            return ReceiptFrame(stomp_frame)
        case "ERROR":
            return ErrorFrame(stomp_frame)
        case _:
            raise Exception("Unknown message type", stomp_frame.message)
