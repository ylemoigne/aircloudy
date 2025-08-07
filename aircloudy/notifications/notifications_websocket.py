from __future__ import annotations

import asyncio
import logging
import traceback
import uuid
from asyncio import Task
from collections.abc import Awaitable, Callable
from types import TracebackType
from typing import Self

import websockets

from aircloudy.contants import SSL_CONTEXT, TokenSupplier
from aircloudy.errors import IllegalStateException
from aircloudy.utils import current_task_is_running, utc_datetime_from_millis

from ..interior_unit_base import InteriorUnitBase
from . import hitachi_frame_models, stomp

logger = logging.getLogger(__name__)


class NotificationsWebsocket:
    _notification_host: str
    _token_supplier: TokenSupplier
    _user_id: int
    _family_id: int
    state_callback: Callable[[list[InteriorUnitBase], bool], None]
    on_unexpected_connection_close: Callable[[websockets.ConnectionClosed], Awaitable[None]] | None

    _notification_socket: websockets.WebSocketClientProtocol | None = None
    _handle_connection_task: Task | None
    _closed_by_client: bool

    def __init__(
        self,
        notification_host: str,
        token_supplier: TokenSupplier,
        user_id: int,
        family_id: int,
        state_callback: Callable[[list[InteriorUnitBase], bool], None],
        on_unexpected_connection_close: Callable[[websockets.ConnectionClosed], Awaitable[None]] | None = None,
    ) -> None:
        self._notification_host = notification_host
        self._token_supplier = token_supplier
        self._user_id = user_id
        self._family_id = family_id
        self.state_callback = state_callback
        self.on_unexpected_connection_close = on_unexpected_connection_close
        self.notification_subscription_id = uuid.uuid4()
        self._closed_by_client = True

    async def __aenter__(self) -> Self:
        await self.connect()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool:
        await self.close()
        return False

    @property
    def is_open(self) -> bool:
        return self._notification_socket is not None

    async def connect(self) -> None:
        self._closed_by_client = False
        await self._init_connection()

        self._handle_connection_task = asyncio.create_task(self._handle_connection())

    async def _handle_connection(self) -> None:
        try:
            async with asyncio.TaskGroup() as tg:
                tg.create_task(self._send_client_heartbeat_loop())
                tg.create_task(self._handle_incoming_frame_loop())
        except ExceptionGroup as e:
            connection_closed: websockets.ConnectionClosed | None = (
                e.exceptions[0]
                if len(e.exceptions) == 1 and isinstance(e.exceptions[0], websockets.ConnectionClosed)
                else None
            )
            if connection_closed is not None:
                logger.info(
                    "Connection closed with status %d and reason %s", connection_closed.code, connection_closed.reason
                )
                if not self._closed_by_client and self.on_unexpected_connection_close is not None:
                    await self.on_unexpected_connection_close(connection_closed)

    async def _init_connection(self) -> None:
        if self.is_open:
            raise Exception(__name__ + " already connected")

        websocket_url = f"wss://{self._notification_host}/rac-notifications/websocket"
        logger.info("Open websocket to %s", websocket_url)
        self._notification_socket = await websockets.connect(websocket_url, ssl=SSL_CONTEXT)
        logger.debug("Send CONNECT stomp frame")
        await self._notification_socket.send(
            hitachi_frame_models.ConnectFrame(await self._token_supplier()).get_frame()
        )

        logger.debug("Wait first server frame (expect CONNECTED frame)")
        frame_data = await self._notification_socket.recv()
        if isinstance(frame_data, bytes):
            raise Exception("Binary frame was unexpected")
        first_server_frame = stomp.parse_server_frame(frame_data)
        if not isinstance(first_server_frame, stomp.ConnectedFrame):
            raise Exception(f"Expected stomp.ConnectedFrame but got {first_server_frame}")

    async def subscribe(self) -> uuid.UUID:
        if self._notification_socket is None:
            raise IllegalStateException(__name__ + " is not connected")

        subscription_id = uuid.uuid4()
        logger.info(
            "Create subscription %s to notifications from user_id=%s, family_id=%s",
            subscription_id,
            self._user_id,
            self._family_id,
        )
        payload = hitachi_frame_models.SubscribeFrame(subscription_id, self._user_id, self._family_id)
        await self._notification_socket.send(payload.get_frame())
        return subscription_id

    async def unsubscribe(self, subscription_id: uuid.UUID) -> None:
        if self._notification_socket is None:
            raise IllegalStateException(__name__ + " is not connected")

        logger.info("Remove subscription %s", subscription_id)
        payload = hitachi_frame_models.UnsubscribeFrame(subscription_id)
        await self._notification_socket.send(payload.get_frame())

    async def refresh_all(self) -> None:
        if self._notification_socket is None:
            raise IllegalStateException(__name__ + " is not connected")

        logger.info("Request refresh all")
        payload = hitachi_frame_models.RefreshAllInteriorUnitFrame(
            await self._token_supplier(), self._user_id, self._family_id
        )
        await self._notification_socket.send(payload.get_frame())

    async def refresh(self, rac_id: int) -> None:
        if self._notification_socket is None:
            raise IllegalStateException(__name__ + " is not connected")

        logger.info("Request refresh rac_id=%d", rac_id)
        payload = hitachi_frame_models.RefreshInteriorUnitFrame(
            await self._token_supplier(), self._user_id, self._family_id, rac_id
        )
        await self._notification_socket.send(payload.get_frame())

    async def _send_client_heartbeat_loop(self) -> None:
        logger.debug("Start send client heartbeat loop")
        while current_task_is_running() and self._notification_socket is not None:
            try:
                logger.debug("Send heartbeat")
                await self._notification_socket.send("\r\n")
                await asyncio.sleep(10)
            except websockets.ConnectionClosed as e:
                raise e
            except Exception as e:
                logger.error("Unexpected error while sending client heartbeat : %s", traceback.format_exc())
                raise e
        logger.debug("End send client heartbeat loop")

    async def _handle_incoming_frame_loop(self) -> None:
        logger.debug("Start handle incoming frame loop")
        while current_task_is_running() and self._notification_socket is not None:
            try:
                logger.debug("Waiting for message")
                data = await self._notification_socket.recv()
                if isinstance(data, bytes):
                    raise Exception("Binary frame was unexpected")

                frame = stomp.parse_server_frame(data)
                logger.debug("Received frame %s", frame)
                match frame:
                    case None:
                        logger.debug("Frame was server-heartbeat")
                    case stomp.ConnectedFrame():
                        raise Exception("ConnectedFrame should have been received at initialization")
                    case stomp.MessageFrame():
                        if frame.body is None:
                            raise Exception("Unexpected message without body")

                        notification_type = frame.body.get("notificationType")
                        if notification_type is None:
                            raise Exception("Unexpected message without notificationType")

                        if notification_type in ("ON_CONNECT", "BUCKET_UPDATE", "REFRESH_ALL"):
                            interior_units = [
                                InteriorUnitBase(
                                    d["id"],
                                    d["name"],
                                    d["roomTemperature"],
                                    d["relativeTemperature"],
                                    utc_datetime_from_millis(d["updatedAt"]),
                                    d["online"],
                                    utc_datetime_from_millis(d["lastOnlineUpdatedAt"]),
                                    d["model"],
                                    str(d["modelTypeId"]),
                                    d["serialNumber"],
                                    d["vendorThingId"],
                                    d["scheduletype"],
                                    d["power"],
                                    d["mode"],
                                    d["iduTemperature"],
                                    d["humidity"],
                                    d["fanSpeed"],
                                    d["fanSwing"],
                                )
                                for d in frame.body["data"]
                            ]
                            self.state_callback(interior_units, notification_type == "BUCKET_UPDATE")
                        else:
                            raise Exception("Unexpected message notification_type", notification_type)

                    case _:
                        logger.warning("Unexpected frame type : %s", frame.message)
            except websockets.ConnectionClosed as e:
                raise e
            except Exception as e:
                logger.error("Unexpected error while handling incoming message : %s", traceback.format_exc())
                raise e
        logger.debug("End handle incoming frame loop")

    async def close(self) -> None:
        self._closed_by_client = True
        try:
            tasks: list[Awaitable] = []
            if self._notification_socket is not None:
                tasks.append(self._notification_socket.close())
            if self._handle_connection_task is not None:
                tasks.append(self._handle_connection_task)

            await asyncio.gather(*tasks)
        finally:
            self._notification_socket = None
        logger.info("Websocket closed")
