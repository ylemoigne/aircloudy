import ssl
from collections.abc import Awaitable, Callable
from typing import Literal

SSL_CONTEXT = ssl._create_unverified_context()
DEFAULT_REST_API_HOST = "api-global-prod.aircloudhome.com"
DEFAULT_STOMP_WEBSOCKET_HOST = "notification-global-prod.aircloudhome.com"

type TokenSupplier = Callable[[], Awaitable[str]]

type ApiCommandState = Literal["SENDING", "INCOMPLETE", "DONE"]

type FanSwing = Literal["OFF", "VERTICAL", "HORIZONTAL", "BOTH", "AUTO"]
type FanSpeed = Literal["LV1", "LV2", "LV3", "LV4", "LV5", "AUTO"]
type Power = Literal["ON", "OFF"]

type OperatingMode = Literal["AUTO", "COOLING", "DRY", "FAN", "HEATING"]
type TemperatureUnit = Literal["CELSIUS", "FAHRENHEIT"]

type ScheduleType = Literal[
    "SCHEDULE_DISABLED",
    "OFF_TIMER_ENABLED",
    "ON_TIMER_ENABLED",
    "ON_OFF_TIMER_ENABLED",
    "WEEKLY_TIMER_ENABLED",
    "HOLIDAY_MODE_ENABLED",
]
