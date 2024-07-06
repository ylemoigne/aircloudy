import ssl
from typing import Awaitable, Callable, Literal, TypeAlias

SSL_CONTEXT = ssl._create_unverified_context()
DEFAULT_REST_API_HOST = "api-global-prod.aircloudhome.com"
DEFAULT_STOMP_WEBSOCKET_HOST = "notification-global-prod.aircloudhome.com"

TokenSupplier: TypeAlias = Callable[[], Awaitable[str]]

ApiCommandState: TypeAlias = Literal["SENDING", "INCOMPLETE", "DONE"]

FanSwing: TypeAlias = Literal["OFF", "VERTICAL", "HORIZONTAL", "BOTH", "AUTO"]
FanSpeed: TypeAlias = Literal["LV1", "LV2", "LV3", "LV4", "LV5", "AUTO"]
Power: TypeAlias = Literal["ON", "OFF"]

OperatingMode: TypeAlias = Literal["AUTO", "COOLING", "DE_HUMIDIFY", "DRY", "FAN", "HEATING"]
TemperatureUnit: TypeAlias = Literal["CELSIUS", "FAHRENHEIT"]

ScheduleType: TypeAlias = Literal[
    "SCHEDULE_DISABLED",
    "OFF_TIMER_ENABLED",
    "ON_TIMER_ENABLED",
    "ON_OFF_TIMER_ENABLED",
    "WEEKLY_TIMER_ENABLED",
    "HOLIDAY_MODE_ENABLED",
]
