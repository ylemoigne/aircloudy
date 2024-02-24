from typing import List, Optional

from .interior_unit_models import InteriorUnit


def compute_interior_unit_diff_description(old: Optional[InteriorUnit], new: Optional[InteriorUnit]) -> str:
    if old == new:
        return "No change"

    if old is None:
        return f"Created {new}"

    if new is None:
        return f"Deleted {old.id}"

    changes: List[str] = []
    if old.id != new.id:
        changes.append(f"id: {old.id}=>{new.id}")
    if old.name != new.name:
        changes.append(f"name: {old.name}=>{new.name}")
    if old.power != new.power:
        changes.append(f"power: {old.power}=>{new.power}")
    if old.mode != new.mode:
        changes.append(f"mode: {old.mode}=>{new.mode}")
    if old.requested_temperature != new.requested_temperature:
        changes.append(f"requested_temperature: {old.requested_temperature}=>{new.requested_temperature}")
    if old.humidity != new.humidity:
        changes.append(f"humidity: {old.humidity}=>{new.humidity}")
    if old.fan_speed != new.fan_speed:
        changes.append(f"fan_speed: {old.fan_speed}=>{new.fan_speed}")
    if old.fan_swing != new.fan_swing:
        changes.append(f"fan_swing: {old.fan_swing}=>{new.fan_swing}")
    if old.room_temperature != new.room_temperature:
        changes.append(f"room_temperature: {old.room_temperature}=>{new.room_temperature}")
    if old.updated_at != new.updated_at:
        changes.append(f"updated_at: {old.updated_at}=>{new.updated_at}")
    if old.online != new.online:
        changes.append(f"online: {old.online}=>{new.online}")
    if old.online_updated_at != new.online_updated_at:
        changes.append(f"online_updated_at: {old.online_updated_at}=>{new.online_updated_at}")

    return "Changed " + ", ".join(changes)
