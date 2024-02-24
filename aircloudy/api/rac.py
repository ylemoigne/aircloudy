import http.client
import json
import logging
from typing import List, Optional

from aircloudy.contants import DEFAULT_REST_API_HOST, SSL_CONTEXT, FanSpeed, FanSwing, OperatingMode, Power

from ..errors import TooManyRequestsException
from ..interior_unit_models import InteriorUnit
from .common import create_headers
from .rac_models import CommandResponse, CommandStatus, PowerAllResponse, _GeneralControlCommand, _InteriorUnitRest

logger = logging.getLogger(__name__)


def get_interior_units(
    token: str, family_id: int, host: str = DEFAULT_REST_API_HOST, port: int = 443
) -> List[InteriorUnit]:
    con = http.client.HTTPSConnection(host, port=port, context=SSL_CONTEXT)
    try:
        logger.debug("Get interior units")
        con.request("GET", f"/rac/ownership/groups/{family_id}/idu-list", headers=create_headers(host, token))
        response_http = con.getresponse()
        response_status = response_http.status
        response_body = response_http.read().decode()
        logger.debug("Response status: %d, body: %s", response_status, response_body)

        if response_http.status != 200:
            raise Exception(f"Call failed (status={response_status} body={response_body}")

        return [_InteriorUnitRest(d).to_internal_representation() for d in json.loads(response_body)]
    finally:
        con.close()


def get_command_status(
    token: str, commands: List[CommandResponse], host: str = DEFAULT_REST_API_HOST, port: int = 443
) -> List[CommandStatus]:
    con = http.client.HTTPSConnection(host, port=port, context=SSL_CONTEXT)
    try:
        logger.debug("Get command status")
        con.request(
            "POST",
            "/rac/status/command",
            json.dumps([c.__dict__ for c in commands]),
            headers=create_headers(host, token),
        )
        response_http = con.getresponse()
        response_status = response_http.status
        response_body = response_http.read().decode()
        logger.debug("Response status: %d, body: %s", response_status, response_body)

        if response_http.status != 200:
            raise Exception(f"Call failed (status={response_status} body={response_body}")

        return [CommandStatus(s) for s in json.loads(response_body)]
    finally:
        con.close()


def configure_interior_unit(
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
    con = http.client.HTTPSConnection(host, port=port, context=SSL_CONTEXT)
    try:
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
        con.request(
            "PUT",
            f"/rac/basic-idu-control/general-control-command/{command.id}?familyId={family_id}",
            json.dumps(command.__dict__),
            headers=create_headers(host, token),
        )
        response_http = con.getresponse()
        response_status = response_http.status
        response_body = response_http.read().decode()
        logger.debug("Response status: %d, body: %s", response_status, response_body)

        if response_http.status == 429:
            raise TooManyRequestsException(response_body)
        if response_http.status != 200:
            raise Exception(f"Call failed (status={response_status} body={response_body}")

        return CommandResponse(json.loads(response_body))
    finally:
        con.close()


def request_refresh_interior_unit_state(
    token: str, rac_id: int, family_id: int, host: str = DEFAULT_REST_API_HOST, port: int = 443
) -> None:
    con = http.client.HTTPSConnection(host, port=port, context=SSL_CONTEXT)
    try:
        logger.debug("Request refresh interior unit state for rac id=%s, family_id=%s", rac_id, family_id)
        con.request("PUT", f"/rac/status/{rac_id}?familyId={family_id}", headers=create_headers(host, token))
        response_http = con.getresponse()
        response_status = response_http.status
        response_body = response_http.read().decode()
        logger.debug("Response status: %d, body: %s", response_status, response_body)

        if response_http.status != 200:
            raise Exception(f"Call failed (status={response_status} body={response_body}")
    finally:
        con.close()


def set_power(token: str, rac_id: str, power: Power, host: str = DEFAULT_REST_API_HOST, port: int = 443) -> None:
    con = http.client.HTTPSConnection(host, port=port, context=SSL_CONTEXT)
    try:
        logger.debug("Set power rac_id=%s, power=%s", rac_id, power)
        con.request(
            "PUT",
            f"/rac/basic-idu-control/switch-on-off/{rac_id}",
            json.dumps(
                {
                    "power": power,
                }
            ),
            headers=create_headers(host, token),
        )
        response_http = con.getresponse()
        response_status = response_http.status
        response_body = response_http.read().decode()
        logger.debug("Response status: %d, body: %s", response_status, response_body)

        if response_http.status != 200:
            raise Exception(f"Fetch idu list failed (status={response_status} body={response_body}")
    finally:
        con.close()


def set_power_all(
    token: str,
    family_id: str,
    power: Power,
    interior_units: List[InteriorUnit],
    host: str = DEFAULT_REST_API_HOST,
    port: int = 443,
) -> PowerAllResponse:
    con = http.client.HTTPSConnection(host, port=port, context=SSL_CONTEXT)
    url = ""
    match power:
        case "ON":
            url = f"/rac/manage-idu/groups/{family_id}/idu/start"
        case "OFF":
            url = f"/rac/manage-idu/groups/{family_id}/idu/stop"

    units = [_GeneralControlCommand(iu.copy(power=power)).__dict__ for iu in interior_units]

    try:
        logger.debug("Set power all power=%s for %s", power, units)
        con.request("PUT", url, json.dumps(units), headers=create_headers(host, token))
        response_http = con.getresponse()
        response_status = response_http.status
        response_body = response_http.read().decode()
        logger.debug("Response status: %d, body: %s", response_status, response_body)

        if response_http.status not in (200, 207):
            raise Exception(f"Fetch idu list failed (status={response_status} body={response_body}")

        return PowerAllResponse(json.loads(response_body))
    finally:
        con.close()
