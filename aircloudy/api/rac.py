from __future__ import annotations

import json
import logging

from aircloudy.contants import DEFAULT_REST_API_HOST, ApiCommandState, Power, TokenSupplier

from ..errors import TooManyRequestsException
from ..interior_unit_base import InteriorUnitBase
from ..utils import utc_datetime_from_millis
from .http_client import perform_request
from .rac_models import CommandResponse, InteriorUnitUserState, PowerAllResponse

logger = logging.getLogger(__name__)


async def get_interior_units(
    token_supplier: TokenSupplier, family_id: int, host: str = DEFAULT_REST_API_HOST, port: int = 443
) -> list[InteriorUnitBase]:
    response = await perform_request(
        "GET", f"/rac/ownership/groups/{family_id}/idu-list", token_supplier=token_supplier, host=host, port=port
    )

    if response.status != 200:
        raise Exception(f"Call failed (status={response.status} body={response.body}")

    return [
        InteriorUnitBase(
            d["id"],
            d["name"],
            d["roomTemperature"],
            d["relativeTemperature"],
            utc_datetime_from_millis(d["updatedAt"]),
            d["online"],
            utc_datetime_from_millis(d["lastOnlineUpdatedAt"]),
            d["model"],
            str(d["racTypeId"]),
            d["serialNumber"],
            d["vendorThingId"],
            d["scheduleType"],
            d["power"],
            d["mode"],
            d["iduTemperature"],
            d["humidity"],
            d["fanSpeed"],
            d["fanSwing"],
        )
        for d in response.body_as_json
    ]


async def get_commands_state(
    token_supplier: TokenSupplier, commands: list[CommandResponse], host: str = DEFAULT_REST_API_HOST, port: int = 443
) -> dict[str, ApiCommandState]:
    response = await perform_request(
        "POST",
        "/rac/status/command",
        body=[c.__dict__ for c in commands],
        token_supplier=token_supplier,
        host=host,
        port=port,
    )

    return {item["commandId"]: item["status"] for item in response.body_as_json}


async def send_command(
    token_supplier: TokenSupplier,
    family_id: int,
    command: InteriorUnitUserState,
    host: str = DEFAULT_REST_API_HOST,
    port: int = 443,
) -> CommandResponse:
    """Send command to change interior unit (like a remote control)

    :raises:
        TooManyRequestsException: If previous command is still in progress
    """
    body = command.to_api()
    logger.info("Configure interior unit family_id=%s : %s", family_id, body)
    response = await perform_request(
        "PUT",
        f"/rac/basic-idu-control/general-control-command/{command.rac_id}?familyId={family_id}",
        body=body,
        do_not_raise_exception_on=(200, 429),
        token_supplier=token_supplier,
        host=host,
        port=port,
    )

    if response.status == 429:
        raise TooManyRequestsException(response.body)

    return CommandResponse(response.body_as_json)


async def request_refresh_interior_unit_state(
    token_supplier: TokenSupplier, rac_id: int, family_id: int, host: str = DEFAULT_REST_API_HOST, port: int = 443
) -> None:
    logger.debug("Request refresh interior unit state for rac id=%s, family_id=%s", rac_id, family_id)
    await perform_request(
        "PUT", f"/rac/status/{rac_id}?familyId={family_id}", token_supplier=token_supplier, host=host, port=port
    )


async def set_power(
    token_supplier: TokenSupplier, rac_id: str, power: Power, host: str = DEFAULT_REST_API_HOST, port: int = 443
) -> None:
    logger.debug("Set power rac_id=%s, power=%s", rac_id, power)
    await perform_request(
        "PUT",
        f"/rac/basic-idu-control/switch-on-off/{rac_id}",
        body={
            "power": power,
        },
        token_supplier=token_supplier,
        host=host,
        port=port,
    )


async def set_power_all(
    token_supplier: TokenSupplier,
    family_id: str,
    power: Power,
    interior_units_state: list[InteriorUnitUserState],
    host: str = DEFAULT_REST_API_HOST,
    port: int = 443,
) -> PowerAllResponse:
    match power:
        case "ON":
            url = f"/rac/manage-idu/groups/{family_id}/idu/start"
        case "OFF":
            url = f"/rac/manage-idu/groups/{family_id}/idu/stop"
        case _:
            raise Exception(f"Unknown power value {power}")

    units = [iu.copy(power=power).to_api() for iu in interior_units_state]

    logger.debug("Set power all power=%s for %s", power, units)
    response = await perform_request(
        "PUT",
        url,
        body=json.dumps(units),
        do_not_raise_exception_on=(200, 207),
        token_supplier=token_supplier,
        host=host,
        port=port,
    )

    return PowerAllResponse(response.body_as_json)
