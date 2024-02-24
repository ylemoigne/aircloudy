import copy
import logging
import uuid
from dataclasses import dataclass
from types import TracebackType
from typing import Callable, List, Optional, Self, Tuple, Type

from . import api, notifications
from .api import CommandResponse
from .contants import (
    DEFAULT_REST_API_HOST,
    DEFAULT_STOMP_WEBSOCKET_HOST,
    DEFAULT_WAIT_DONE,
    FanSpeed,
    FanSwing,
    OperatingMode,
    Power,
)
from .errors import CommandFailedException, IllegalStateException, InteriorUnitNotFoundException
from .interior_unit_models import InteriorUnit

logger = logging.getLogger(__name__)


@dataclass
class ConnectionInfo:
    authentication_result: api.AuthenticationSuccess
    user_profile: api.UserProfile
    notification_socket: notifications.NotificationsWebsocket
    notification_subscription_id: uuid.UUID


class HitachiAirCloud:
    _email: str
    _password: str
    _default_wait_done: int
    _api_host: str

    _command_manager: api.CommandManager
    _connection_info: Optional[ConnectionInfo]
    _interior_units: dict[int, InteriorUnit]

    on_change: Optional[Callable[[dict[int, Tuple[Optional[InteriorUnit], Optional[InteriorUnit]]]], None]]

    def __init__(
        self,
        email: str,
        password: str,
        default_wait_done: int = DEFAULT_WAIT_DONE,
        api_host: str = DEFAULT_REST_API_HOST,
        api_port: int = 443,
        notification_host: str = DEFAULT_STOMP_WEBSOCKET_HOST,
    ) -> None:
        self._email = email
        self._password = password
        self._default_wait_done = default_wait_done
        self._api_host = api_host
        self.notification_host = notification_host

        self._command_manager = api.CommandManager(self._get_auth_token_or_fail, host=api_host, port=api_port)
        self._connection_info = None
        self._interior_units = {}

    async def __aenter__(self) -> Self:
        await self.connect()
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> bool:
        await self.close()
        return False

    @property
    def is_open(self) -> bool:
        return self._connection_info is not None

    @property
    def interior_units(self) -> List[InteriorUnit]:
        return [copy.deepcopy(iu) for iu in self._interior_units.values()]

    def interior_unit(self, rac_id: int) -> Optional[InteriorUnit]:
        return self._interior_units.get(rac_id)

    def _get_auth_token_or_fail(self) -> str:
        if self._connection_info is None:
            raise Exception("AirCloud is not connected")
        return self._connection_info.authentication_result.token

    async def _wait_done(self, override_default_wait_done: Optional[int], command: CommandResponse) -> None:
        wait_done = self._default_wait_done if override_default_wait_done is None else override_default_wait_done
        if wait_done > 0:
            final_state = await self._command_manager.wait_ack(command, wait_done)
            if final_state != "DONE":
                raise CommandFailedException(
                    f"Command state is still not done (current: {final_state}) after delay {wait_done}"
                )

    async def connect(self) -> None:
        if self.is_open:
            raise IllegalStateException("AirCloud already connected")

        authentication_result = api.perform_login(self._email, self._password, self._api_host)
        user_profile = api.fetch_profile(authentication_result.token, self._api_host)
        self._interior_units = {
            iu.id: iu
            for iu in api.get_interior_units(authentication_result.token, user_profile.familyId, self._api_host)
        }

        notification_socket = notifications.NotificationsWebsocket(
            self.notification_host,
            lambda: authentication_result.token,
            user_profile.id,
            user_profile.familyId,
            lambda ius: self._update_interior_units(ius),
        )
        await notification_socket.connect()
        notification_subscription_id = await notification_socket.subscribe()

        self._connection_info = ConnectionInfo(
            authentication_result,
            user_profile,
            notification_socket,
            notification_subscription_id,
        )

        notification_socket.token_supplier = self._get_auth_token_or_fail
        logger.info("Connected")

    async def close(self) -> None:
        try:
            if self._connection_info is not None:
                await self._connection_info.notification_socket.close()
        finally:
            self._connection_info = None
            self._interior_units = {}
        logging.info("Closed")

    def _update_interior_units(self, interior_units: List[InteriorUnit]) -> None:
        logger.debug("Received interior units update: %s", interior_units)
        changes: dict[int, Tuple[Optional[InteriorUnit], Optional[InteriorUnit]]] = {}
        for iu in interior_units:
            old_iu = self._interior_units[iu.id]
            if old_iu != iu:
                changes[iu.id] = (old_iu, iu)
            self._interior_units[iu.id] = iu

        if self.on_change is not None:
            self.on_change(changes)

    async def set(self, interior_unit: InteriorUnit, override_default_wait_done: Optional[int] = None) -> None:
        """
        Send command to set interior_unit state

        :raises:
            IllegalStateException: If instance is not connected
            CommandFailedException: If state isn't done after wait delay
        """
        if self._connection_info is None:
            raise IllegalStateException("Connect must be called before calling this method")

        command: CommandResponse = api.configure_interior_unit(
            self._connection_info.authentication_result.token,
            self._connection_info.user_profile.familyId,
            interior_unit,
            host=self._api_host,
        )
        await self._wait_done(override_default_wait_done, command)
        await self._connection_info.notification_socket.refresh(interior_unit.id)

    async def set_power(
        self, interior_unit: InteriorUnit, power: Power, override_default_wait_done: Optional[int] = None
    ) -> None:
        """
        Send command to set interior_unit on/off

        :raises:
            IllegalStateException: If instance is not connected
            InteriorUnitNotFoundException: If given interior_unit id doesn't exists in current know states
            CommandFailedException: If state isn't done after wait delay
        """
        if self._connection_info is None:
            raise IllegalStateException("Connect must be called before calling this method")
        up_to_date_interior_unit = self.interior_unit(interior_unit.id)
        if up_to_date_interior_unit is None:
            raise InteriorUnitNotFoundException(f"Interior unit {interior_unit.id} not found")

        command = api.configure_interior_unit(
            self._connection_info.authentication_result.token,
            self._connection_info.user_profile.familyId,
            up_to_date_interior_unit,
            power=power,
            host=self._api_host,
        )
        await self._wait_done(override_default_wait_done, command)
        await self._connection_info.notification_socket.refresh(interior_unit.id)

    async def set_operating_mode(
        self, interior_unit: InteriorUnit, mode: OperatingMode, override_default_wait_done: Optional[int] = None
    ) -> None:
        """
        Send command to set interior_unit operating mode

        :raises:
            IllegalStateException: If instance is not connected
            InteriorUnitNotFoundException: If given interior_unit id doesn't exists in current know states
        """
        if self._connection_info is None:
            raise IllegalStateException("Connect must be called before calling this method")
        up_to_date_interior_unit = self.interior_unit(interior_unit.id)
        if up_to_date_interior_unit is None:
            raise InteriorUnitNotFoundException(f"Interior unit {interior_unit.id} not found")

        command = api.configure_interior_unit(
            self._connection_info.authentication_result.token,
            self._connection_info.user_profile.familyId,
            up_to_date_interior_unit,
            mode=mode,
            host=self._api_host,
        )
        await self._wait_done(override_default_wait_done, command)
        await self._connection_info.notification_socket.refresh(interior_unit.id)

    async def set_requested_temperature(
        self, interior_unit: InteriorUnit, temperature: float, override_default_wait_done: Optional[int] = None
    ) -> None:
        """
        Send command to set interior_unit requested temperature

        :raises:
            IllegalStateException: If instance is not connected
            InteriorUnitNotFoundException: If given interior_unit id doesn't exists in current know states
        """
        if self._connection_info is None:
            raise IllegalStateException("Connect must be called before calling this method")
        up_to_date_interior_unit = self.interior_unit(interior_unit.id)
        if up_to_date_interior_unit is None:
            raise InteriorUnitNotFoundException(f"Interior unit {interior_unit.id} not found")

        command = api.configure_interior_unit(
            self._connection_info.authentication_result.token,
            self._connection_info.user_profile.familyId,
            up_to_date_interior_unit,
            requested_temperature=temperature,
            host=self._api_host,
        )
        await self._wait_done(override_default_wait_done, command)
        await self._connection_info.notification_socket.refresh(interior_unit.id)

    async def set_humidity(
        self, interior_unit: InteriorUnit, humidity: int, override_default_wait_done: Optional[int] = None
    ) -> None:
        """
        Send command to set interior_unit humidity

        :raises:
            IllegalStateException: If instance is not connected
            InteriorUnitNotFoundException: If given interior_unit id doesn't exists in current know states
        """
        if self._connection_info is None:
            raise IllegalStateException("Connect must be called before calling this method")
        up_to_date_interior_unit = self.interior_unit(interior_unit.id)
        if up_to_date_interior_unit is None:
            raise InteriorUnitNotFoundException(f"Interior unit {interior_unit.id} not found")

        command = api.configure_interior_unit(
            self._connection_info.authentication_result.token,
            self._connection_info.user_profile.familyId,
            up_to_date_interior_unit,
            humidity=humidity,
            host=self._api_host,
        )
        await self._wait_done(override_default_wait_done, command)
        await self._connection_info.notification_socket.refresh(interior_unit.id)

    async def set_fan_speed(
        self, interior_unit: InteriorUnit, speed: FanSpeed, override_default_wait_done: Optional[int] = None
    ) -> None:
        """
        Send command to set interior_unit fan speed

        :raises:
            IllegalStateException: If instance is not connected
            InteriorUnitNotFoundException: If given interior_unit id doesn't exists in current know states
        """
        if self._connection_info is None:
            raise IllegalStateException("Connect must be called before calling this method")
        up_to_date_interior_unit = self.interior_unit(interior_unit.id)
        if up_to_date_interior_unit is None:
            raise InteriorUnitNotFoundException(f"Interior unit {interior_unit.id} not found")

        command = api.configure_interior_unit(
            self._connection_info.authentication_result.token,
            self._connection_info.user_profile.familyId,
            up_to_date_interior_unit,
            fan_speed=speed,
            host=self._api_host,
        )
        await self._wait_done(override_default_wait_done, command)
        await self._connection_info.notification_socket.refresh(interior_unit.id)

    async def set_fan_swing(
        self, interior_unit: InteriorUnit, swing: FanSwing, override_default_wait_done: Optional[int] = None
    ) -> None:
        """
        Send command to set interior_unit fan swing

        :raises:
            IllegalStateException: If instance is not connected
            InteriorUnitNotFoundException: If given interior_unit id doesn't exists in current know states
        """
        if self._connection_info is None:
            raise IllegalStateException("Connect must be called before calling this method")
        up_to_date_interior_unit = self.interior_unit(interior_unit.id)
        if up_to_date_interior_unit is None:
            raise InteriorUnitNotFoundException(f"Interior unit {interior_unit.id} not found")

        command = api.configure_interior_unit(
            self._connection_info.authentication_result.token,
            self._connection_info.user_profile.familyId,
            up_to_date_interior_unit,
            fan_swing=swing,
            host=self._api_host,
        )
        await self._wait_done(override_default_wait_done, command)
        await self._connection_info.notification_socket.refresh(interior_unit.id)
