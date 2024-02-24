import logging
from typing import List, Optional

from aircloudy.contants import DEFAULT_REST_API_HOST, FanSpeed, FanSwing, OperatingMode, Power

from ..errors import TooManyRequestsException
from ..interior_unit_models import InteriorUnit
from .http_client import perform_request
from .rac_models import CommandResponse, CommandStatus, PowerAllResponse, _GeneralControlCommand, _InteriorUnitRest

logger = logging.getLogger(__name__)


async def get_interior_units(
    token: str, family_id: int, host: str = DEFAULT_REST_API_HOST, port: int = 443
) -> List[InteriorUnit]:
    logger.debug("Get interior units")
    response = await perform_request(
        "GET", f"/rac/ownership/groups/{family_id}/idu-list", token=token, host=host, port=port
    )

    if response.status != 200:
        raise Exception(f"Call failed (status={response.status} body={response.body}")

    return [_InteriorUnitRest(d).to_internal_representation() for d in response.body_as_json]


async def get_command_status(
    token: str, commands: List[CommandResponse], host: str = DEFAULT_REST_API_HOST, port: int = 443
) -> List[CommandStatus]:
    logger.debug("Get command status")

    response = await perform_request(
        "POST", "/rac/status/command", [c.__dict__ for c in commands], token=token, host=host, port=port
    )

    return [CommandStatus(s) for s in response.body_as_json]


async def configure_interior_unit(
    token: str,
    family_id: int,
    interior_unit: InteriorUnit,
    power: Optional[Power] = None,
    mode: Optional[OperatingMode] = None,
    requested_temperature: Optional[float] = None,
    humidity: Optional[int] = None,
    fan_speed: Optional[FanSpeed] = None,
    fan_swing: Optional[FanSwing] = None,
    host: str = DEFAULT_REST_API_HOST,
    port: int = 443,
) -> CommandResponse:
    """Send command to change interior unit (like a remote control)

    :raises:
        TooManyRequestsException: If previous command is still in progress
    """
    command = _GeneralControlCommand(
        interior_unit.copy(
            power=power,
            mode=mode,
            requested_temperature=requested_temperature,
            humidity=humidity,
            fan_speed=fan_speed,
            fan_swing=fan_swing,
        )
    )

    logger.debug("Configure interior unit familiy_id=%s : %s", family_id, command)
    response = await perform_request(
        "PUT",
        f"/rac/basic-idu-control/general-control-command/{command.id}?familyId={family_id}",
        command.__dict__,
        do_not_raise_exception_on=(200, 429),
        token=token,
        host=host,
        port=port,
    )

    if response.status == 429:
        raise TooManyRequestsException(response.body)

    return CommandResponse(response.body_as_json)


async def request_refresh_interior_unit_state(
    token: str, rac_id: int, family_id: int, host: str = DEFAULT_REST_API_HOST, port: int = 443
) -> None:
    logger.debug("Request refresh interior unit state for rac id=%s, family_id=%s", rac_id, family_id)
    await perform_request("PUT", f"/rac/status/{rac_id}?familyId={family_id}", token=token, host=host, port=port)


async def set_power(token: str, rac_id: str, power: Power, host: str = DEFAULT_REST_API_HOST, port: int = 443) -> None:
    logger.debug("Set power rac_id=%s, power=%s", rac_id, power)
    await perform_request(
        "PUT",
        f"/rac/basic-idu-control/switch-on-off/{rac_id}",
        {
            "power": power,
        },
        token=token,
        host=host,
        port=port,
    )


async def set_power_all(
    token: str,
    family_id: str,
    power: Power,
    interior_units: List[InteriorUnit],
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

    units = [_GeneralControlCommand(iu.copy(power=power)).__dict__ for iu in interior_units]

    logger.debug("Set power all power=%s for %s", power, units)
    response = await perform_request(
        "PUT", url, units, do_not_raise_exception_on=(200, 207), token=token, host=host, port=port
    )

    return PowerAllResponse(response.body_as_json)
