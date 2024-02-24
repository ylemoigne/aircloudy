from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .contants import FanSpeed, FanSwing, OperatingMode, Power


@dataclass
class InteriorUnit:
    id: int
    name: str
    power: Power
    mode: OperatingMode
    requested_temperature: float
    humidity: int  # don't know the effect/working, is it current or requested, ?
    fan_speed: FanSpeed
    fan_swing: FanSwing
    room_temperature: float
    updated_at: int
    online: bool
    online_updated_at: int

    def copy(
        self,
        name: Optional[str] = None,
        power: Optional[Power] = None,
        mode: Optional[OperatingMode] = None,
        requested_temperature: Optional[float] = None,
        humidity: Optional[int] = None,
        fan_speed: Optional[FanSpeed] = None,
        fan_swing: Optional[FanSwing] = None,
        room_temperature: Optional[float] = None,
        updated_at: Optional[int] = None,
        online: Optional[bool] = None,
        online_updated_at: Optional[int] = None,
    ) -> InteriorUnit:
        new_name = self.name
        new_power = self.power
        new_mode = self.mode
        new_requested_temperature = self.requested_temperature
        new_humidity = self.humidity
        new_fan_speed = self.fan_speed
        new_fan_swing = self.fan_swing
        new_room_temperature = self.room_temperature
        new_updated_at = self.updated_at
        new_online = self.online
        new_online_updated_at = self.online_updated_at

        if name is not None:
            new_name = name
        if power is not None:
            new_power = power
        if mode is not None:
            new_mode = mode
        if requested_temperature is not None:
            new_requested_temperature = requested_temperature
        if humidity is not None:
            new_humidity = humidity
        if fan_speed is not None:
            new_fan_speed = fan_speed
        if fan_swing is not None:
            new_fan_swing = fan_swing
        if room_temperature is not None:
            new_room_temperature = room_temperature
        if updated_at is not None:
            new_updated_at = updated_at
        if online is not None:
            new_online = online
        if online_updated_at is not None:
            new_online_updated_at = online_updated_at

        return InteriorUnit(
            self.id,
            new_name,
            new_power,
            new_mode,
            new_requested_temperature,
            new_humidity,
            new_fan_speed,
            new_fan_swing,
            new_room_temperature,
            new_updated_at,
            new_online,
            new_online_updated_at,
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, InteriorUnit):
            return False

        return (
            self.id == other.id
            and self.name == other.name
            and self.power == other.power
            and self.mode == other.mode
            and self.requested_temperature == other.requested_temperature
            and self.humidity == other.humidity
            and self.fan_speed == other.fan_speed
            and self.fan_swing == other.fan_swing
            and self.room_temperature == other.room_temperature
            and self.updated_at == other.updated_at
            and self.online == other.online
            and self.online_updated_at == other.online_updated_at
        )
