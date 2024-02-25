from __future__ import annotations

import copy
import logging
import uuid
from dataclasses import dataclass
from types import TracebackType
from typing import Callable, Self

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
    TemperatureUnit,
)
from .errors import CommandFailedException, IllegalStateException, InteriorUnitNotFoundException
from .interior_unit_models import InteriorUnit

logger = logging.getLogger(__name__)


@dataclass
class ConnectionInfo:
    auth_manager: api.AuthManager
    user_profile: api.UserProfile
    notification_socket: notifications.NotificationsWebsocket
    notification_subscription_id: uuid.UUID


class HitachiAirCloud:
    _email: str
    _password: str
    _default_wait_done: int
    _api_host: str
    _api_port: int

    _command_manager: api.CommandManager
    _connection_info: ConnectionInfo | None
    _interior_units: dict[int, InteriorUnit]

    on_change: Callable[[dict[int, tuple[InteriorUnit | None, InteriorUnit | None]]], None] | None

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
        self._api_port = api_port
        self.notification_host = notification_host

        self._command_manager = api.CommandManager(self._get_auth_token_or_fail, host=api_host, port=api_port)
        self._connection_info = None
        self._interior_units = {}

        self.on_change = None

    async def __aenter__(self) -> Self:
        await self.connect()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool:
        await self.close()
        return False

    @property
    def is_open(self) -> bool:
        return self._connection_info is not None

    @property
    def interior_units(self) -> list[InteriorUnit]:
        return [copy.deepcopy(iu) for iu in self._interior_units.values()]

    @property
    def temperature_unit(self) -> TemperatureUnit:
        if self._connection_info is None:
            raise Exception("AirCloud is not connected")

        if self._connection_info.user_profile.settings.temperatureUnit == "degC":
            return "CELSIUS"

        return "FAHRENHEIT"

    def find_interior_unit(self, rac_id: int) -> InteriorUnit | None:
        return self._interior_units.get(rac_id)

    def get_interior_unit(self, rac_id: int) -> InteriorUnit:
        iu = self.find_interior_unit(rac_id)
        if iu is None:
            raise InteriorUnitNotFoundException(f"Interior unit {rac_id} not found")
        return iu

    async def _get_auth_token_or_fail(self) -> str:
        if self._connection_info is None:
            raise Exception("AirCloud is not connected")
        return await self._connection_info.auth_manager.token()

    async def _wait_done(self, override_default_wait_done: int | None, command: CommandResponse) -> None:
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

        auth_manager = api.AuthManager(self._email, self._password, self._api_host, self._api_port)
        user_profile = await api.fetch_profile(auth_manager.token, self._api_host, self._api_port)
        self._interior_units = {
            iu.id: iu
            for iu in await api.get_interior_units(
                auth_manager.token, user_profile.familyId, self._api_host, self._api_port
            )
        }

        notification_socket = notifications.NotificationsWebsocket(
            self.notification_host,
            auth_manager.token,
            user_profile.id,
            user_profile.familyId,
            lambda ius: self._update_interior_units(ius),
        )
        await notification_socket.connect()
        notification_subscription_id = await notification_socket.subscribe()

        self._connection_info = ConnectionInfo(
            auth_manager,
            user_profile,
            notification_socket,
            notification_subscription_id,
        )

        logger.info("Connected")

    async def close(self) -> None:
        try:
            if self._connection_info is not None:
                await self._connection_info.notification_socket.close()
        finally:
            self._connection_info = None
            self._interior_units = {}
        logging.info("Closed")

    def _update_interior_units(self, interior_units: list[InteriorUnit]) -> None:
        logger.debug("Received interior units update: %s", interior_units)
        changes: dict[int, tuple[InteriorUnit | None, InteriorUnit | None]] = {}
        for iu in interior_units:
            old_iu = self._interior_units[iu.id]
            if old_iu != iu:
                changes[iu.id] = (old_iu, iu)
            self._interior_units[iu.id] = iu

        if self.on_change is not None:
            self.on_change(changes)

    async def update_all(self) -> None:
        if self._connection_info is None:
            raise IllegalStateException("Connect must be called before calling this method")

        self._update_interior_units(
            await api.get_interior_units(
                self._connection_info.auth_manager.token,
                self._connection_info.user_profile.familyId,
                self._api_host,
                self._api_port,
            )
        )

    async def request_update_all(self) -> None:
        if self._connection_info is None:
            raise IllegalStateException("Connect must be called before calling this method")

        await self._connection_info.notification_socket.refresh_all()

    async def request_update(self, rac_id: int) -> None:
        if self._connection_info is None:
            raise IllegalStateException("Connect must be called before calling this method")

        await self._connection_info.notification_socket.refresh(rac_id)

    async def set(
        self,
        rac_id: int,
        power: Power | None = None,
        mode: OperatingMode | None = None,
        requested_temperature: float | None = None,
        humidity: int | None = None,
        fan_speed: FanSpeed | None = None,
        fan_swing: FanSwing | None = None,
        override_default_wait_done: int | None = None,
    ) -> None:
        """
        Send command to set interior_unit state

        :raises:
            IllegalStateException: If instance is not connected
            CommandFailedException: If state isn't done after wait delay
        """
        if self._connection_info is None:
            raise IllegalStateException("Connect must be called before calling this method")
        interior_unit = self.get_interior_unit(rac_id)

        command: CommandResponse = await api.configure_interior_unit(
            self._connection_info.auth_manager.token,
            self._connection_info.user_profile.familyId,
            interior_unit,
            power,
            mode,
            requested_temperature,
            humidity,
            fan_speed,
            fan_swing,
            host=self._api_host,
        )
        await self._wait_done(override_default_wait_done, command)
        await self.request_update(rac_id)
