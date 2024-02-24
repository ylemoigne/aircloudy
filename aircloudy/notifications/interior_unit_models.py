from dataclasses import dataclass

from aircloudy.contants import FanSpeed, FanSwing, OperatingMode, Power, ScheduleType
from aircloudy.interior_unit_models import InteriorUnit


class IduFrostWashStatus:
    active: bool
    priority: int
    astUpdatedA: int
    subCategory = None
    errorCode = None


class SpecialOperationStatus:
    active: bool
    priority: int
    lastUpdatedAt: int
    subCategory = None
    errorCode = None


class ErrorStatus:
    active: bool
    priority: int
    lastUpdatedAt: int
    subCategory: str
    errorCode = None


class HolidayModeStatus:
    active: bool
    priority: int
    lastUpdatedAt: int
    subCategory = None
    errorCode = None


@dataclass
class InteriorUnitNotification:
    serialNumber: str
    iduFrostWashStatus: IduFrostWashStatus
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
    specialOperationStatus: SpecialOperationStatus
    errorStatus: ErrorStatus
    lastOnlineUpdatedAt: int
    scheduletype: ScheduleType
    modelTypeId: int
    cloudId: str
    opt4: int
    holidayModeStatus: HolidayModeStatus
    online: bool
    SysType: int

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
