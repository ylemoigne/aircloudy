from __future__ import annotations

import logging

from aircloudy.contants import DEFAULT_REST_API_HOST, FanSpeed, FanSwing, OperatingMode, Power, TokenSupplier

from ..errors import TooManyRequestsException
from ..interior_unit_models import InteriorUnit
from .http_client import perform_request
from .rac_models import CommandResponse, CommandStatus, PowerAllResponse, _GeneralControlCommand, _InteriorUnitRest

logger = logging.getLogger(__name__)


async def get_interior_units(
    token_supplier: TokenSupplier, family_id: int, host: str = DEFAULT_REST_API_HOST, port: int = 443
) -> list[InteriorUnit]:
    logger.debug("Get interior units")
    response = await perform_request(
        "GET", f"/rac/ownership/groups/{family_id}/idu-list", token_supplier=token_supplier, host=host, port=port
    )

    if response.status != 200:
        raise Exception(f"Call failed (status={response.status} body={response.body}")

    return [_InteriorUnitRest(d).to_internal_representation() for d in response.body_as_json]


async def get_command_status(
    token_supplier: TokenSupplier, commands: list[CommandResponse], host: str = DEFAULT_REST_API_HOST, port: int = 443
) -> list[CommandStatus]:
    logger.debug("Get command status")

    response = await perform_request(
        "POST",
        "/rac/status/command",
        body=[c.__dict__ for c in commands],
        token_supplier=token_supplier,
        host=host,
        port=port,
    )

    return [CommandStatus(s) for s in response.body_as_json]


async def configure_interior_unit(
    token_supplier: TokenSupplier,
    family_id: int,
    interior_unit: InteriorUnit,
    power: Power | None = None,
    mode: OperatingMode | None = None,
    requested_temperature: float | None = None,
    humidity: int | None = None,
    fan_speed: FanSpeed | None = None,
    fan_swing: FanSwing | None = None,
    host: str = DEFAULT_REST_API_HOST,
    port: int = 443,
) -> CommandResponse:
    """Send command to change interior unit (like a remote control)

    :raises:
        TooManyRequestsException: If previous command is still in progress
    """
    command = _GeneralControlCommand(interior_unit, power, mode, requested_temperature, humidity, fan_speed, fan_swing)

    logger.debug("Configure interior unit familiy_id=%s : %s", family_id, command.__dict__)
    response = await perform_request(
        "PUT",
        f"/rac/basic-idu-control/general-control-command/{command.id}?familyId={family_id}",
        body=command.__dict__,
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
    interior_units: list[InteriorUnit],
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

    units = [_GeneralControlCommand(iu, power=power).__dict__ for iu in interior_units]

    logger.debug("Set power all power=%s for %s", power, units)
    response = await perform_request(
        "PUT",
        url,
        body=units,
        do_not_raise_exception_on=(200, 207),
        token_supplier=token_supplier,
        host=host,
        port=port,
    )

    return PowerAllResponse(response.body_as_json)
