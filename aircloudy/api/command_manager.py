import asyncio
import logging
from asyncio import Task
from typing import Callable, Optional

from aircloudy.api.rac import get_command_status
from aircloudy.api.rac_models import CommandResponse, CommandStatus
from aircloudy.contants import DEFAULT_REST_API_HOST, DEFAULT_WAIT_DONE, CommandState
from aircloudy.utils import current_task_is_running

logger = logging.getLogger(__name__)


class CommandManager:
    _token_supplier: Callable[[], str]
    _update_interval: int
    _api_host: str
    _port: int

    _commands: dict[str, CommandResponse]
    _commands_status: dict[str, CommandStatus]
    _events: dict[str, asyncio.Event]
    _task_fetch_command_status: Optional[Task]

    def __init__(
        self,
        token_supplier: Callable[[], str],
        update_interval: int = 2,
        host: str = DEFAULT_REST_API_HOST,
        port: int = 443,
    ) -> None:
        self._token_supplier = token_supplier
        self._update_interval = update_interval
        self._api_host = host
        self._port = port

        self._commands = {}
        self._commands_status = {}
        self._events = {}
        self._task_fetch_command_status = None

    def add_command_watch(self, command: CommandResponse) -> None:
        self._commands[command.commandId] = command
        if self._task_fetch_command_status is None:
            self._task_fetch_command_status = asyncio.create_task(self._fetch_command_status_loop())

    def remove_command_watch(self, command_id: str) -> None:
        del self._commands[command_id]
        if self._task_fetch_command_status is not None and len(self._commands) == 0:
            self._task_fetch_command_status.cancel()

    def clear(self) -> None:
        self._commands = {}
        if self._task_fetch_command_status is not None:
            self._task_fetch_command_status.cancel()

    async def wait_ack(self, command: CommandResponse, wait: int = DEFAULT_WAIT_DONE) -> CommandState:
        self.add_command_watch(command)
        event = asyncio.Event()
        self._events[command.commandId] = event
        try:
            await asyncio.wait_for(event.wait(), wait)
            del self._events[command.commandId]
            self.remove_command_watch(command.commandId)
        except asyncio.TimeoutError:
            pass

        status = self._commands_status[command.commandId]
        return status.status

    async def _fetch_command_status_loop(self) -> None:
        while current_task_is_running():
            try:
                logger.debug("Fetch tasks status")
                self._commands_status = {
                    s.commandId: s
                    for s in get_command_status(
                        self._token_supplier(), list(self._commands.values()), self._api_host, self._port
                    )
                }
                for command_id, event in self._events.items():
                    if not event.is_set():
                        status = self._commands_status[command_id]
                        if status is not None and status.status == "DONE":
                            event.set()

                await asyncio.sleep(self._update_interval)
            except Exception as e:
                logger.error("Unexpected error while fetching status : %s", e)
                raise e
