import ssl
from typing import Literal

SSL_CONTEXT = ssl._create_unverified_context()
DEFAULT_REST_API_HOST = "api-global-prod.aircloudhome.com"
DEFAULT_STOMP_WEBSOCKET_HOST = "notification-global-prod.aircloudhome.com"
DEFAULT_WAIT_DONE = 10

CommandState = Literal["SENDING", "INCOMPLETE", "DONE"]

FanSwing = Literal["OFF", "VERTICAL", "HORIZONTAL", "BOTH", "AUTO"]
FanSpeed = Literal["LV1", "LV2", "LV3", "LV4", "LV5", "AUTO"]
Power = Literal["ON", "OFF"]

# Don't know what is DRY_COOL but it exist in Android client source code
OperatingMode = Literal["AUTO", "COOLING", "DE_HUMIDIFY", "DRY_COOL", "FAN", "HEATING"]

ScheduleType = Literal[
    "SCHEDULE_DISABLED",
    "OFF_TIMER_ENABLED",
    "ON_TIMER_ENABLED",
    "ON_OFF_TIMER_ENABLED",
    "WEEKLY_TIMER_ENABLED",
    "HOLIDAY_MODE_ENABLED",
]
