from __future__ import annotations

import asyncio
import datetime
import logging
import traceback
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from .api.rac_models import InteriorUnitUserState
from .contants import ApiCommandState, FanSpeed, FanSwing, OperatingMode, Power
from .errors import CommandFailedException, InvalidArgumentException, UnitIsOfflineException
from .interior_unit_base import InteriorUnitBase
from .interior_unit_changes import InteriorUnitChanges

logger = logging.getLogger(__name__)


@dataclass
class NextState:
    _command: InteriorUnitUserState
    _created_at: datetime.datetime

    def __init__(self, command: InteriorUnitUserState) -> None:
        self._command = command
        self._created_at = datetime.datetime.now(datetime.UTC)

    @property
    def command(self) -> InteriorUnitUserState:
        return self._command

    @property
    def created_at(self) -> datetime.datetime:
        return self._created_at

    def __hash__(self) -> int:
        return hash(self._command)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, NextState):
            return False
        return self.command == other.command


@dataclass
class InteriorUnit:
    _send_command_and_wait_ack: Callable[[InteriorUnitUserState], Awaitable[ApiCommandState | None]]

    _id: int
    _name: str
    _room_temperature: float
    _relative_temperature: float
    _updated_at: datetime.datetime
    _online: bool
    _online_updated_at: datetime.datetime
    _vendor: str
    _model_id: str
    _user_state: InteriorUnitUserState

    on_changes: Callable[[InteriorUnitChanges], None] | None = None

    _state_lock: asyncio.Lock = asyncio.Lock()
    _next_state: NextState | None = None
    _state_updater: asyncio.Task | None = None

    def __init__(
        self,
        send_command_and_wait_ack: Callable[[InteriorUnitUserState], Awaitable[None]],
        base: InteriorUnitBase,
    ) -> None:
        self._send_command_and_wait_ack = send_command_and_wait_ack
        self._id = base.rac_id
        self._name = base.name
        self._room_temperature = base.room_temperature
        self._relative_temperature = base.relative_temperature
        self._updated_at = base.updated_at
        self._online = base.online
        self._online_updated_at = base.online_updated_at
        self._vendor = base.vendor
        self._model_id = base.model_id
        self._user_state = base.user_state

    def update(self, base: InteriorUnitBase) -> InteriorUnitChanges:
        if base.rac_id != self.id:
            raise InvalidArgumentException("Update must come from the same id")
        changes = InteriorUnitChanges(
            (self._name, base.name) if self._name != base.name else None,
            (
                (self._room_temperature, base.room_temperature)
                if self._room_temperature != base.room_temperature
                else None
            ),
            (
                (self._relative_temperature, base.relative_temperature)
                if self._relative_temperature != base.relative_temperature
                else None
            ),
            (self._updated_at, base.updated_at) if self._updated_at != base.updated_at else None,
            (self._online, base.online) if self._online != base.online else None,
            (
                (self._online_updated_at, base.online_updated_at)
                if self._online_updated_at != base.online_updated_at
                else None
            ),
            (self._vendor, base.vendor) if self._vendor != base.vendor else None,
            (self._model_id, base.model_id) if self._model_id != base.model_id else None,
            (self._user_state.power, base.power) if self._user_state._power != base.power else None,
            (
                (self._user_state.operating_mode, base.operating_mode)
                if self._user_state._operating_mode != base.operating_mode
                else None
            ),
            (
                (self._user_state.requested_temperature, base.requested_temperature)
                if self._user_state._requested_temperature != base.requested_temperature
                else None
            ),
            (self._user_state.humidity, base.humidity) if self._user_state._humidity != base.humidity else None,
            (self._user_state.fan_speed, base.fan_speed) if self._user_state._fan_speed != base.fan_speed else None,
            (self._user_state.fan_swing, base.fan_swing) if self._user_state._fan_swing != base.fan_swing else None,
        )

        self._name = base.name
        self._room_temperature = base.room_temperature
        self._relative_temperature = base.relative_temperature
        self._updated_at = base.updated_at
        self._online = base.online
        self._online_updated_at = base.online_updated_at
        self._vendor = base.vendor
        self._model_id = base.model_id
        self._user_state = base.user_state

        if self.on_changes is not None:
            self.on_changes(changes)

        return changes

    @property
    def id(self) -> int:
        return self._id

    @property
    def name(self) -> str:
        return self._name

    @property
    def room_temperature(self) -> float:
        return self._room_temperature

    @property
    def relative_temperature(self) -> float:
        return self._relative_temperature

    @property
    def updated_at(self) -> datetime.datetime:
        return self._updated_at

    @property
    def online(self) -> bool:
        return self._online

    @property
    def online_updated_at(self) -> datetime.datetime:
        return self._online_updated_at

    @property
    def vendor(self) -> str:
        return self._vendor

    @property
    def model_id(self) -> str:
        return self._model_id

    @property
    def power(self) -> Power:
        return self._user_state._power

    @property
    def operating_mode(self) -> OperatingMode:
        return self._user_state._operating_mode

    @property
    def requested_temperature(self) -> float:
        return self._user_state._requested_temperature

    @property
    def humidity(self) -> int:
        return self._user_state._humidity

    @property
    def fan_speed(self) -> FanSpeed:
        return self._user_state._fan_speed

    @property
    def fan_swing(self) -> FanSwing:
        return self._user_state._fan_swing

    async def send_command(
        self,
        power: Power | None = None,
        mode: OperatingMode | None = None,
        requested_temperature: float | None = None,
        humidity: int | None = None,
        fan_speed: FanSpeed | None = None,
        fan_swing: FanSwing | None = None,
    ) -> None:
        if not self._online:
            raise UnitIsOfflineException

        async with self._state_lock:
            base_state = (
                self._next_state.command
                if self._next_state is not None and self._next_state.created_at > self._updated_at
                else self._user_state
            )
            self._next_state = NextState(
                base_state.copy(power, mode, requested_temperature, humidity, fan_speed, fan_swing)
            )
            if self._state_updater is None or self._state_updater.done():
                self._state_updater = asyncio.create_task(self._update_state())

    async def _update_state(self) -> None:
        last_state: NextState | None = None
        while True:
            async with self._state_lock:
                new_state = self._next_state
                if new_state is None or new_state == last_state:
                    break

            try:
                await self._send_command_and_wait_ack(new_state.command)
                async with self._state_lock:
                    self._user_state = new_state.command
                    self._updated_at = new_state.created_at
            except CommandFailedException:
                logger.warning("Failed to acknowledge command execution: %s", traceback.format_exc())

            last_state = new_state

    def __hash__(self) -> int:
        return hash(self._id)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, InteriorUnit):
            return False

        return (
            self._id == other._id
            and self._name == other._name
            and self._room_temperature == other._room_temperature
            and self._relative_temperature == other._relative_temperature
            and self._updated_at == other._updated_at
            and self._online == other._online
            and self._online_updated_at == other._online_updated_at
            and self._vendor == other._vendor
            and self._model_id == other._model_id
            and self._user_state == other._user_state
        )
