from __future__ import annotations

import asyncio
import logging
import traceback
from asyncio import Task

from aircloudy.api.rac import get_commands_state
from aircloudy.api.rac_models import CommandResponse
from aircloudy.contants import DEFAULT_REST_API_HOST, ApiCommandState, TokenSupplier

logger = logging.getLogger(__name__)


class CommandState:
    _origin: CommandResponse
    _event: asyncio.Event
    _state: ApiCommandState | None

    _state_lock: asyncio.Lock

    def __init__(self, command: CommandResponse) -> None:
        self._command = command
        self._event = asyncio.Event()
        self._state = None
        self._state_lock = asyncio.Lock()

    @property
    def id(self) -> str:
        return self._command.commandId

    @property
    def command(self) -> CommandResponse:
        return self._command

    async def get_state(self) -> ApiCommandState | None:
        async with self._state_lock:
            return self._state

    async def is_terminated(self) -> bool:
        state = await self.get_state()
        return state is None or state == "DONE"

    async def wait_done(self) -> None:
        await self._event.wait()

    def __repr__(self) -> str:
        return (
            f"CommandStatus("
            f"command_id={self._command.commandId}, "
            f"state={self._state}, "
            f"event_is_set={self._event.is_set()})"
        )

    async def set_state(self, state: ApiCommandState) -> None:
        async with self._state_lock:
            self._state = state
            if self._state == "DONE":
                self._event.set()


class CommandStateMonitor:
    _token_supplier: TokenSupplier
    _update_interval: int
    _api_host: str
    _port: int

    _commands: dict[str, CommandState]
    _task_fetch_command_status: Task | None

    _lock: asyncio.Lock

    def __init__(
        self,
        token_supplier: TokenSupplier,
        update_interval: int = 2,
        host: str = DEFAULT_REST_API_HOST,
        port: int = 443,
    ) -> None:
        self._token_supplier = token_supplier
        self._update_interval = update_interval
        self._api_host = host
        self._port = port

        self._lock = asyncio.Lock()
        self._commands = {}
        self._task_fetch_command_status = None

    async def watch_command(self, command: CommandResponse) -> CommandState:
        async with self._lock:
            logger.debug("Add command watch for command %s", command)
            command_status = CommandState(command)
            self._commands[command.commandId] = command_status
            if self._task_fetch_command_status is None or self._task_fetch_command_status.done():
                self._task_fetch_command_status = asyncio.create_task(self._fetch_command_status_loop())
            return command_status

    async def _fetch_command_status_loop(self) -> None:
        logger.debug("Start fetch_command_status_loop")
        try:
            while True:
                async with self._lock:
                    if len(self._commands) == 0:
                        break

                    commands_to_watch = [command_status.command for command_status in self._commands.values()]
                try:
                    commands_state = await get_commands_state(
                        self._token_supplier, commands_to_watch, self._api_host, self._port
                    )

                    async with self._lock:
                        await asyncio.gather(
                            *[self._commands[rac_id].set_state(state) for rac_id, state in commands_state.items()]
                        )
                        self._commands = {
                            cmd.id: cmd for cmd in self._commands.values() if not await cmd.is_terminated()
                        }

                    await asyncio.sleep(self._update_interval)
                except Exception as e:
                    logger.error("Unexpected error while fetching status : %s", traceback.format_exc())
                    raise e
        finally:
            logger.debug("Finish fetch_command_status_loop")
