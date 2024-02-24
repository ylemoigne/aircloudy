import asyncio
from typing import Optional


def to_int(value: Optional[str]) -> Optional[int]:
    return int(value) if value else None


def current_task_is_running() -> bool:
    task = asyncio.current_task()
    if task is None:
        return False
    return not task.cancelling() and not task.cancelled()
