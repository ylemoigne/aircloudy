import asyncio
import json
import logging.config
from time import sleep
from typing import Optional, Tuple

import aircloudy.api.rac
from aircloudy import HitachiAirCloud, InteriorUnit, compute_interior_unit_diff_description
from aircloudy.contants import DEFAULT_REST_API_HOST

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


def print_changes(changes: dict[int, Tuple[Optional[InteriorUnit], Optional[InteriorUnit]]]) -> None:
    for id, change in changes.items():
        print(f"Change on interior unit {id}: " + compute_interior_unit_diff_description(change[0], change[1]))


async def main() -> None:
    async with HitachiAirCloud(credentials_email, credentials_password) as ac:
        ac.on_change = print_changes

        unit_bureau = next((iu for iu in ac.interior_units if iu.name == "Bureau"), None)
        if unit_bureau is None:
            raise Exception("No unit named `Bureau`")

        await ac.set_power(unit_bureau, "ON")
        await asyncio.sleep(10)
        # aircloudy.api.rac.request_refresh_interior_unit_state(DEFAULT_REST_API_HOST, ac._connection_info.authentication_result.token, unit_bureau.id, ac._connection_info.user_profile.familyId)
        await ac.set(unit_bureau.copy(requested_temperature=21, fan_speed="LV3"))
        # await asyncio.sleep(5)
        await ac.set_power(unit_bureau, "OFF")

        await asyncio.sleep(30)
        await ac.set_power(unit_bureau, "OFF")


async def play_raw_api():
    auth = await aircloudy.api.iam.perform_login(credentials_email, credentials_password+"a")
    # user = aircloudy.api.iam.fetch_profile(auth.token, DEFAULT_REST_API_HOST)
    # units = aircloudy.api.rac.get_interior_units(auth.token, user.familyId, DEFAULT_REST_API_HOST)
    # unit_bureau = next((iu for iu in units if iu.name == "Bureau"), None)
    # if unit_bureau is None:
    #     raise Exception("No unit named `Bureau`")
    #
    # cmd= aircloudy.api.rac.configure_interior_unit(auth.token, user.familyId, unit_bureau, power="ON",
    #                                                host=DEFAULT_REST_API_HOST)
    # aircloudy.api.rac.get_command_status(auth.token, [{"commandId": cmd.commandId, "thingId": cmd.thingId}],
    #                                      DEFAULT_REST_API_HOST)
    # sleep(3)
    # cmd = aircloudy.api.rac.configure_interior_unit(auth.token, user.familyId, unit_bureau, power="OFF",
    #                                                 host=DEFAULT_REST_API_HOST)

# asyncio.run(main())
asyncio.run(play_raw_api())