from __future__ import annotations
import asyncio
import json
import logging.config
from datetime import datetime, timezone

import tzlocal

from aircloudy import HitachiAirCloud, InteriorUnit, compute_interior_unit_diff_description

logging.config.dictConfig(
    {
        "version": 1,
        "formatters": {
            "simple": {
                "format": "[%(asctime)s] %(levelname)s %(message)s",
            },
            "verbose": {
                "format": "[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": "DEBUG",
                "formatter": "verbose",
            },
        },
        "loggers": {
            "aircloudy": {
                "level": "DEBUG",
                "handlers": ["console"],
                "propagate": True,
            },
        },
    }
)

with open("../.secrets/playground_credentials.json", "r") as f:
    data = json.loads(f.read())
    credentials_email = data["email"]
    credentials_password = data["password"]


def print_changes(changes: dict[int, tuple[InteriorUnit|None, InteriorUnit|None]]) -> None:
    for id, change in changes.items():
        print(f"Change on interior unit {id}: " + compute_interior_unit_diff_description(change[0], change[1]))


async def main() -> None:
    async with HitachiAirCloud(credentials_email, credentials_password) as ac:
        ac.on_change = print_changes

        while True:
            await asyncio.sleep(30)


asyncio.run(main())
