from __future__ import annotations

import asyncio
from asyncio import Future
from typing import Awaitable, TypeVar

T = TypeVar("T")


def awaitable(value: T) -> Awaitable[T]:
    f: Future[T] = asyncio.Future()
    f.set_result(value)
    return f


def to_int(value: str | None) -> int | None:
    return int(value) if value else None


def current_task_is_running() -> bool:
    task = asyncio.current_task()
    if task is None:
        return False
    return not task.cancelling() and not task.cancelled()
