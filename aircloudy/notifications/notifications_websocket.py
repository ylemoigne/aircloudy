from __future__ import annotations

import asyncio
import logging
import traceback
import uuid
from asyncio import Task
from types import TracebackType
from typing import Callable, Self

import websockets

from aircloudy.contants import SSL_CONTEXT, TokenSupplier
from aircloudy.errors import IllegalStateException
from aircloudy.utils import current_task_is_running

from ..interior_unit_models import InteriorUnit
from . import hitachi_frame_models, stomp
from .interior_unit_models import InteriorUnitNotification

logger = logging.getLogger(__name__)


class NotificationsWebsocket:
    _notification_host: str
    _token_supplier: TokenSupplier
    _user_id: int
    _family_id: int
    state_callback: Callable[[list[InteriorUnit]], None]
    on_connection_closed_by_server: Callable[[websockets.ConnectionClosed], None] | None

    _notification_socket: websockets.WebSocketClientProtocol | None = None
    _task_send_client_heartbeat: Task | None = None
    _task_handle_incoming_frame: Task | None = None

    def __init__(
        self,
        notification_host: str,
        token_supplier: TokenSupplier,
        user_id: int,
        family_id: int,
        state_callback: Callable[[list[InteriorUnit]], None],
        on_connection_closed_by_server: Callable[[websockets.ConnectionClosed], None] | None = None,
    ) -> None:
        self._notification_host = notification_host
        self._token_supplier = token_supplier
        self._user_id = user_id
        self._family_id = family_id
        self.state_callback = state_callback
        self.on_connection_closed_by_server = on_connection_closed_by_server
        self.notification_subscription_id = uuid.uuid4()

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
            raise Exception(f"Excepted stomp.ConnectedFrame but got {first_server_frame}")

        logger.debug("Start send client heartbeat task")
        self._task_send_client_heartbeat = asyncio.create_task(self._send_client_heartbeat_loop())
        logger.debug("Start handle incoming frame task")
        self._task_handle_incoming_frame = asyncio.create_task(self._handle_incoming_frame_loop())

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
        while current_task_is_running() and self._notification_socket is not None:
            try:
                logger.debug("Send heartbeat")
                await self._notification_socket.send("\r\n")
                await asyncio.sleep(10)
            except Exception as e:
                logger.error("Unexpected error while sending client heartbeat : %s", e)
                raise e

    async def _handle_incoming_frame_loop(self) -> None:
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

                        if notification_type in ("ON_CONNECT", "BUCKET_UPDATE"):
                            interior_units = [
                                InteriorUnitNotification(d).to_internal_representation() for d in frame.body["data"]
                            ]
                            self.state_callback(interior_units)
                        else:
                            raise Exception("Unexpected message notification_type", notification_type)

                    case _:
                        logger.warning("Unexpected frame type : %s", frame.message)
            except websockets.ConnectionClosed as e:
                logger.debug("Connection closed (%s)", e)
                if self.on_connection_closed_by_server is not None:
                    self.on_connection_closed_by_server(e)

                # Not sure how to handle the situation knowing
                # that self.close will want the current task to be canceled
                # And the cancellation wait for this to finish
                asyncio.create_task(self.close())
                return
            except Exception as e:
                logger.error("Unexpected error while handling incoming message : %s", traceback.format_exc(e))
                raise e

    async def close(self) -> None:
        try:
            if self._task_send_client_heartbeat is not None:
                self._task_send_client_heartbeat.cancel()
                try:
                    await self._task_send_client_heartbeat
                except asyncio.exceptions.CancelledError as e:
                    logger.debug("Canceled `send client heartbeat` task : %s", e)

            if self._task_handle_incoming_frame is not None:
                self._task_handle_incoming_frame.cancel()
                try:
                    await self._task_handle_incoming_frame
                except asyncio.exceptions.CancelledError as e:
                    logger.debug("Canceled `handle incoming frame` task : %s", e)

            if self._notification_socket is not None:
                await self._notification_socket.close()
                logger.info("Websocket closed")
        finally:
            self._notification_socket = None
            self._task_handle_incoming_frame = None
            self._task_send_client_heartbeat = None
