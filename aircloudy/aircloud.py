from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from dataclasses import dataclass
from types import TracebackType
from typing import Self

from . import api, notifications
from .api.rac_models import InteriorUnitUserState
from .contants import (
    DEFAULT_REST_API_HOST,
    DEFAULT_STOMP_WEBSOCKET_HOST,
    TemperatureUnit,
)
from .errors import IllegalStateException, InteriorUnitNotFoundException
from .interior_unit import InteriorUnit
from .interior_unit_base import InteriorUnitBase
from .interior_unit_changes import InteriorUnitChanges

logger = logging.getLogger(__name__)


@dataclass
class ConnectionInfo:
    auth_manager: api.AuthManager
    user_profile: api.UserProfile
    notification_socket: notifications.NotificationsWebsocket


class HitachiAirCloud:
    _email: str
    _password: str
    _api_host: str
    _api_port: int

    _command_state_monitor: api.CommandStateMonitor
    _connection_info: ConnectionInfo | None
    _interior_units: dict[int, InteriorUnit]

    on_change: Callable[[dict[int, InteriorUnitChanges]], None] | None

    def __init__(
        self,
        email: str,
        password: str,
        api_host: str = DEFAULT_REST_API_HOST,
        api_port: int = 443,
        notification_host: str = DEFAULT_STOMP_WEBSOCKET_HOST,
    ) -> None:
        self._email = email
        self._password = password
        self._api_host = api_host
        self._api_port = api_port
        self.notification_host = notification_host

        self._command_state_monitor = api.CommandStateMonitor(
            self._get_auth_token_or_fail, host=api_host, port=api_port
        )
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
        return list(self._interior_units.values())

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

    async def connect(self) -> None:
        if self.is_open:
            raise IllegalStateException("AirCloud already connected")

        auth_manager = api.AuthManager(self._email, self._password, self._api_host, self._api_port)
        user_profile = await api.fetch_profile(auth_manager.token, self._api_host, self._api_port)
        self._interior_units = {
            iu.rac_id: InteriorUnit(self._send_command_and_wait_ack, iu)
            for iu in await api.get_interior_units(
                auth_manager.token, user_profile.familyId, self._api_host, self._api_port
            )
        }

        notification_socket = notifications.NotificationsWebsocket(
            self.notification_host,
            auth_manager.token,
            user_profile.id,
            user_profile.familyId,
            self._update_interior_units,
        )
        notification_socket.on_unexpected_connection_close = lambda _: self._init_notification_socket(
            notification_socket
        )
        await self._init_notification_socket(notification_socket)

        self._connection_info = ConnectionInfo(
            auth_manager,
            user_profile,
            notification_socket,
        )

        logger.info("Connected")

    async def _init_notification_socket(self, socket: notifications.NotificationsWebsocket) -> None:
        await socket.connect()
        await socket.subscribe()

    async def close(self) -> None:
        try:
            if self._connection_info is not None:
                await self._connection_info.notification_socket.close()
        finally:
            self._connection_info = None
            self._interior_units = {}

    def _update_interior_units(self, interior_units: list[InteriorUnitBase], partial: bool) -> None:
        logger.debug("Received interior units update: %s", interior_units)
        changes: dict[int, InteriorUnitChanges] = {}
        for iu in interior_units:
            changes[iu.rac_id] = self._interior_units[iu.rac_id].update(iu)

        # If update is not partial, compare given list and current list to detected deleted interior_unit
        # and notify change
        if partial:
            pass

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
            ),
            False,
        )

    async def request_update_all(self) -> None:
        if self._connection_info is None:
            raise IllegalStateException("Connect must be called before calling this method")

        await self._connection_info.notification_socket.refresh_all()

    async def request_update(self, rac_id: int) -> None:
        if self._connection_info is None:
            raise IllegalStateException("Connect must be called before calling this method")

        await self._connection_info.notification_socket.refresh(rac_id)

    async def _send_command_and_wait_ack(
        self,
        interior_unit_command: InteriorUnitUserState,
    ) -> None:
        """
        Send command to set interior_unit state

        :raises:
            IllegalStateException: If instance is not connected
            CommandFailedException: If state isn't done after wait delay
        """
        if self._connection_info is None:
            raise IllegalStateException("Connect must be called before calling this method")

        command_state = await self._command_state_monitor.watch_command(
            await api.send_command(
                self._connection_info.auth_manager.token,
                self._connection_info.user_profile.familyId,
                interior_unit_command,
                host=self._api_host,
                port=self._api_port,
            )
        )
        await asyncio.wait_for(command_state.wait_done(), 30)
        await self.request_update(interior_unit_command.rac_id)
