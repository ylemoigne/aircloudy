from __future__ import annotations


class StompFrame:
    message: str
    headers: dict[str, str]
    body: dict | None = None

    def __init__(self, message: str, headers: dict[str, str], body: dict | None = None) -> None:
        self.message = message
        self.headers = headers
        self.body = body

    def __repr__(self) -> str:
        return f"WebsocketMessage(message={self.message}, headers={self.headers}, body={self.body})"

    def get_frame(self) -> str:
        websocket_message = f"{self.message}\n"
        for name, value in self.headers.items():
            websocket_message += f"{name}:{value}\n"
        websocket_message += "\n"

        if self.body:
            websocket_message += f"{self.body}\n"

        return websocket_message + "\0"
