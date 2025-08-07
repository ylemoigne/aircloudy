from __future__ import annotations

import datetime
from dataclasses import dataclass

from .contants import FanSpeed, FanSwing, OperatingMode, Power


@dataclass
class InteriorUnitChanges:
    name: tuple[str, str] | None
    room_temperature: tuple[float, float] | None
    relative_temperature: tuple[float, float] | None
    updated_at: tuple[datetime.datetime, datetime.datetime] | None
    online: tuple[bool, bool] | None
    online_updated_at: tuple[datetime.datetime, datetime.datetime] | None
    vendor: tuple[str, str] | None
    model_id: tuple[str, str] | None
    power: tuple[Power, Power] | None
    operating_mode: tuple[OperatingMode, OperatingMode] | None
    requested_temperature: tuple[float, float] | None
    humidity: tuple[int, int] | None
    fan_speed: tuple[FanSpeed, FanSpeed] | None
    fan_swing: tuple[FanSwing, FanSwing] | None

    @property
    def has_changes(self) -> bool:
        return (
            self.name is not None
            or self.room_temperature is not None
            or self.relative_temperature is not None
            or self.updated_at is not None
            or self.online is not None
            or self.online_updated_at is not None
            or self.vendor is not None
            or self.model_id is not None
            or self.power is not None
            or self.operating_mode is not None
            or self.requested_temperature is not None
            or self.humidity is not None
            or self.fan_speed is not None
            or self.fan_swing is not None
        )

    def __repr__(self) -> str:
        changes_as_string: list[str] = []
        if self.name is not None:
            changes_as_string.append(f"name={self.name[0]}->{self.name[1]}")
        if self.room_temperature is not None:
            changes_as_string.append(f"room_temperature={self.room_temperature[0]}->{self.room_temperature[1]}")
        if self.relative_temperature is not None:
            changes_as_string.append(
                f"relative_temperature={self.relative_temperature[0]}->{self.relative_temperature[1]}"
            )
        if self.updated_at is not None:
            changes_as_string.append(f"updated_at={self.updated_at[0]}->{self.updated_at[1]}")
        if self.online is not None:
            changes_as_string.append(f"online={self.online[0]}->{self.online[1]}")
        if self.online_updated_at is not None:
            changes_as_string.append(f"online_updated_at={self.online_updated_at[0]}->{self.online_updated_at[1]}")
        if self.vendor is not None:
            changes_as_string.append(f"vendor={self.vendor[0]}->{self.vendor[1]}")
        if self.model_id is not None:
            changes_as_string.append(f"model_id={self.model_id[0]}->{self.model_id[1]}")
        if self.power is not None:
            changes_as_string.append(f"power={self.power[0]}->{self.power[1]}")
        if self.operating_mode is not None:
            changes_as_string.append(f"operating_mode={self.operating_mode[0]}->{self.operating_mode[1]}")
        if self.requested_temperature is not None:
            changes_as_string.append(
                f"requested_temperature={self.requested_temperature[0]}->{self.requested_temperature[1]}"
            )
        if self.humidity is not None:
            changes_as_string.append(f"humidity={self.humidity[0]}->{self.humidity[1]}")
        if self.fan_speed is not None:
            changes_as_string.append(f"fan_speed={self.fan_speed[0]}->{self.fan_speed[1]}")
        if self.fan_swing is not None:
            changes_as_string.append(f"fan_swing={self.fan_swing[0]}->{self.fan_swing[1]}")

        return f"InteriorUnitChanges({', '.join(changes_as_string)})"
