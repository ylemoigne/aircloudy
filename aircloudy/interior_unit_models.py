from __future__ import annotations

from dataclasses import dataclass

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
    relative_temperature: float
    updated_at: int
    online: bool
    online_updated_at: int
    vendor: str
    model_id: str

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, InteriorUnit):
            return False

        return self.__dict__ == other.__dict__
