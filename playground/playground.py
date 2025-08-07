from __future__ import annotations

import asyncio
import datetime
import json
import logging.config
import uuid

import aircloudy
import aircloudy.api
from aircloudy import HitachiAirCloud
from aircloudy.interior_unit_changes import InteriorUnitChanges

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
            "__main__": {
                "level": "DEBUG",
                "handlers": ["console"],
                "propagate": True,
            },
        },
    }
)
# logging.basicConfig(level="INFO")
logger = logging.getLogger(__name__)

with open("../.secrets/playground_credentials.json", "r") as f:
    data = json.loads(f.read())
    credentials_email = data["email"]
    credentials_password = data["password"]


def print_changes(changes: dict[int, InteriorUnitChanges]) -> None:
    for id, change in changes.items():
        print(
            f"Change on interior unit {id}: " + str(change))


async def main() -> None:
    async with HitachiAirCloud(credentials_email, credentials_password) as ac:
        ac.on_change = print_changes


        bureau = [iu for iu in ac.interior_units if iu.name == "Bureau"][0]
        bureau.on_changes = lambda changes: print("bureau: "+str(changes))
        print("0", bureau.requested_temperature, bureau.fan_speed, bureau.fan_swing, bureau.power)
        await bureau.send_command(requested_temperature=18)
        print("1", bureau.requested_temperature, bureau.fan_speed, bureau.fan_swing, bureau.power)
        await bureau.send_command(requested_temperature=19, fan_speed="LV1")
        print("2", bureau.requested_temperature, bureau.fan_speed, bureau.fan_swing, bureau.power)
        await bureau.send_command(requested_temperature=20, fan_swing="HORIZONTAL")
        print("3", bureau.requested_temperature, bureau.fan_speed, bureau.fan_swing, bureau.power)
        await bureau.send_command(requested_temperature=21, power="OFF")
        print("4", bureau.requested_temperature, bureau.fan_speed, bureau.fan_swing, bureau.power)
        await asyncio.sleep(60)
    print("Ac closed")

asyncio.run(main())
