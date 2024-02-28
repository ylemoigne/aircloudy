import datetime

from .api.rac_models import InteriorUnitUserState
from .contants import FanSpeed, FanSwing, OperatingMode, Power, ScheduleType


class InteriorUnitBase:
    _rac_id: int
    _name: str
    _room_temperature: float
    _relative_temperature: float
    _updated_at: datetime.datetime
    _online: bool
    _online_updated_at: datetime.datetime
    _vendor: str
    _model_id: str
    _serial_number: str
    _vendor_thing_id: str
    _schedule_type: ScheduleType
    _user_state: InteriorUnitUserState

    def __init__(
        self,
        rac_id: int,
        name: str,
        room_temperature: float,
        relative_temperature: float,
        updated_at: datetime.datetime,
        online: bool,
        online_updated_at: datetime.datetime,
        vendor: str,
        model_id: str,
        serial_number: str,
        vendor_thing_id: str,
        schedule_type: ScheduleType,
        power: Power,
        operating_mode: OperatingMode,
        requested_temperature: float,
        humidity: int,
        fan_speed: FanSpeed,
        fan_swing: FanSwing,
    ) -> None:
        self._rac_id = rac_id
        self._name = name
        self._room_temperature = room_temperature
        self._relative_temperature = relative_temperature
        self._updated_at = updated_at
        self._online = online
        self._online_updated_at = online_updated_at
        self._vendor = vendor
        self._model_id = model_id
        self._serial_number = serial_number
        self._vendor_thing_id = vendor_thing_id
        self._schedule_type = schedule_type
        self._user_state = InteriorUnitUserState(
            rac_id, power, operating_mode, requested_temperature, humidity, fan_speed, fan_swing
        )

    @property
    def rac_id(self) -> int:
        return self._rac_id

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
    def user_state(self) -> InteriorUnitUserState:
        return self._user_state

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
