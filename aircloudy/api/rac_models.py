from dataclasses import dataclass
from typing import List, Optional

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
    errorMessage: Optional[str]
    errorCode: int
    commandResponse: CommandResponse

    def __init__(self, data: dict) -> None:
        self.__dict__.update(data)


class PowerAllResponse:
    allSucceeded: bool
    resultSet: List[PowerResult]

    def __init__(self, data: dict) -> None:
        self.__dict__.update(data)


@dataclass
class _GeneralControlCommand:
    id: int
    power: Power
    mode: OperatingMode
    iduTemperature: float
    humidity: int
    fanSpeed: FanSpeed
    fanSwing: FanSwing

    def __init__(self, interior_unit: InteriorUnit) -> None:
        self.id = interior_unit.id
        self.power = interior_unit.power
        self.mode = interior_unit.mode
        self.iduTemperature = interior_unit.requested_temperature
        # Should be something like `self.humidity = interior_unit.humidity`
        # but some api return me humidity=126 and this is not a legal value for control
        self.humidity = 50
        self.fanSpeed = interior_unit.fan_speed
        self.fanSwing = interior_unit.fan_swing


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
            self.updatedAt,
            self.online,
            self.lastOnlineUpdatedAt,
        )
