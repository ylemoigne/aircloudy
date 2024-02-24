import json
from dataclasses import dataclass


@dataclass
class HttpResponse:
    status: int
    body: str

    @property
    def body_as_json(self) -> dict:
        return json.loads(self.body)
