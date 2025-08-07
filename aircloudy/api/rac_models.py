from __future__ import annotations

from dataclasses import dataclass

from aircloudy.contants import FanSpeed, FanSwing, OperatingMode, Power


@dataclass
class CommandResponse:
    commandId: str
    thingId: str

    def __init__(self, data: dict) -> None:
        self.__dict__.update(data)


@dataclass
class PowerResult:
    racId: int
    success: bool
    errorMessage: str | None
    errorCode: int
    commandResponse: CommandResponse

    def __init__(self, data: dict) -> None:
        self.__dict__.update(data)


@dataclass
class PowerAllResponse:
    allSucceeded: bool
    resultSet: list[PowerResult]

    def __init__(self, data: dict) -> None:
        self.__dict__.update(data)


class InteriorUnitUserState:
    _rac_id: int
    _power: Power
    _operating_mode: OperatingMode
    _requested_temperature: float
    _humidity: int
    _fan_speed: FanSpeed
    _fan_swing: FanSwing

    def __init__(
        self,
        rac_id: int,
        power: Power,
        operating_mode: OperatingMode,
        requested_temperature: float,
        humidity: int,
        fan_speed: FanSpeed,
        fan_swing: FanSwing,
    ) -> None:
        self._rac_id = rac_id
        self._power = power
        self._operating_mode = operating_mode
        self._requested_temperature = requested_temperature
        self._humidity = humidity
        self._fan_speed = fan_speed
        self._fan_swing = fan_swing

    @property
    def rac_id(self) -> int:
        return self._rac_id

    @property
    def power(self) -> Power:
        return self._power

    @property
    def operating_mode(self) -> OperatingMode:
        return self._operating_mode

    @property
    def requested_temperature(self) -> float:
        return self._requested_temperature

    @property
    def humidity(self) -> int:
        return self._humidity

    @property
    def fan_speed(self) -> FanSpeed:
        return self._fan_speed

    @property
    def fan_swing(self) -> FanSwing:
        return self._fan_swing

    def copy(
        self,
        power: Power | None = None,
        mode: OperatingMode | None = None,
        requested_temperature: float | None = None,
        humidity: int | None = None,
        fan_speed: FanSpeed | None = None,
        fan_swing: FanSwing | None = None,
    ) -> InteriorUnitUserState:
        return InteriorUnitUserState(
            self._rac_id,
            self._power if power is None else power,
            self._operating_mode if mode is None else mode,
            self._requested_temperature if requested_temperature is None else requested_temperature,
            self._humidity if humidity is None else humidity,
            self._fan_speed if fan_speed is None else fan_speed,
            self._fan_swing if fan_swing is None else fan_swing,
        )

    def to_api(self) -> dict:
        return {
            "id": self._rac_id,
            "power": self._power,
            "mode": self._operating_mode,
            "iduTemperature": self._requested_temperature,
            # Should be something like `self._humidity`
            # but some api return me humidity=126 and this is not a legal value for control
            "humidity": 50,
            "fanSpeed": self.fan_speed,
            "fanSwing": self.fan_swing,
        }

    def __hash__(self) -> int:
        return hash(self._rac_id)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, InteriorUnitUserState):
            return False

        return self.__dict__ == other.__dict__
