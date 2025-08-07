from uuid import UUID

from .stomp import StompFrame


class ConnectFrame(StompFrame):
    def __init__(self, token: str) -> None:
        StompFrame.__init__(
            self,
            "CONNECT",
            {
                "accept-version": "1.1,1.2",
                "heart-beat": "10000,10000",
                "Authorization": f"Bearer {token}",
            },
        )


class RefreshAllInteriorUnitFrame(StompFrame):
    def __init__(self, token: str, user_id: int, family_id: int) -> None:
        StompFrame.__init__(
            self,
            "MESSAGE",
            {
                "Authorization": f"Bearer {token}",
                "destination": f"/app/racs/{user_id}/{family_id}",
            },
            {
                "racId": 0,
                "requestType": "REFRESH_ALL",
            },
        )


class RefreshInteriorUnitFrame(StompFrame):
    def __init__(self, token: str, user_id: int, family_id: int, rac_id: int) -> None:
        StompFrame.__init__(
            self,
            "MESSAGE",
            {
                "Authorization": f"Bearer {token}",
                "destination": f"/app/racs/{user_id}/{family_id}",
            },
            {
                "racId": rac_id,
                "requestType": "REFRESH_INDIVIDUAL",
            },
        )


class SubscribeFrame(StompFrame):
    def __init__(self, uuid: UUID, user_id: int, family_id: int) -> None:
        StompFrame.__init__(
            self,
            "SUBSCRIBE",
            {
                "id": str(uuid),
                "destination": f"/notification/{user_id}/{family_id}",
                "ack": "auto",
            },
        )


class UnsubscribeFrame(StompFrame):
    def __init__(self, uuid: UUID) -> None:
        StompFrame.__init__(
            self,
            "UNSUBSCRIBE",
            {
                "id": str(uuid),
            },
        )
