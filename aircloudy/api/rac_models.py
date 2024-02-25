from __future__ import annotations

from dataclasses import dataclass

from aircloudy.contants import CommandState, FanSpeed, FanSwing, OperatingMode, Power, ScheduleType
from aircloudy.interior_unit_models import InteriorUnit


class CommandResponse:
    commandId: str
    thingId: str

    def __init__(self, data: dict) -> None:
        self.__dict__.update(data)


class CommandStatus:
    commandId: str
    status: CommandState

    def __init__(self, data: dict) -> None:
        self.__dict__.update(data)


class PowerResult:
    racId: int
    success: bool
    errorMessage: str | None
    errorCode: int
    commandResponse: CommandResponse

    def __init__(self, data: dict) -> None:
        self.__dict__.update(data)


class PowerAllResponse:
    allSucceeded: bool
    resultSet: list[PowerResult]

    def __init__(self, data: dict) -> None:
        self.__dict__.update(data)


class _GeneralControlCommand:
    id: int
    power: Power
    mode: OperatingMode
    iduTemperature: float
    humidity: int
    fanSpeed: FanSpeed
    fanSwing: FanSwing

    def __init__(
        self,
        interior_unit: InteriorUnit,
        power: Power | None = None,
        mode: OperatingMode | None = None,
        requested_temperature: float | None = None,
        humidity: int | None = None,
        fan_speed: FanSpeed | None = None,
        fan_swing: FanSwing | None = None,
    ) -> None:
        self.id = interior_unit.id
        self.power = power if power is not None else interior_unit.power
        self.mode = mode if mode is not None else interior_unit.mode
        self.iduTemperature = (
            requested_temperature if requested_temperature is not None else interior_unit.requested_temperature
        )
        # Should be something like `else interior_unit.humidity`
        # but some api return me humidity=126 and this is not a legal value for control
        self.humidity = humidity if humidity is not None else 50
        self.fanSpeed = fan_speed if fan_speed is not None else interior_unit.fan_speed
        self.fanSwing = fan_swing if fan_swing is not None else interior_unit.fan_swing


@dataclass
class _InteriorUnitRest:
    userId: str
    serialNumber: str
    model: str
    id: int
    vendorThingId: str
    name: str
    roomTemperature: float
    mode: OperatingMode
    iduTemperature: float
    humidity: int
    power: Power
    relativeTemperature: float
    fanSpeed: FanSpeed
    fanSwing: FanSwing
    updatedAt: int
    lastOnlineUpdatedAt: int
    racTypeId: int
    iduFrostWash: bool
    specialOperation: bool
    criticalError: bool
    zoneId: str
    scheduleType: ScheduleType
    online: bool

    def __init__(self, data: dict) -> None:
        self.__dict__.update(data)

    def to_internal_representation(self) -> InteriorUnit:
        return InteriorUnit(
            self.id,
            self.name,
            self.power,
            self.mode,
            self.iduTemperature,
            self.humidity,
            self.fanSpeed,
            self.fanSwing,
            self.roomTemperature,
            self.relativeTemperature,
            self.updatedAt,
            self.online,
            self.lastOnlineUpdatedAt,
            self.model,
            str(self.racTypeId),
        )
