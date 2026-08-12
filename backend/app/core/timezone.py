import os
from zoneinfo import ZoneInfo

DEFAULT_TZ = os.getenv("FITFLOW_TIMEZONE", "America/Argentina/Buenos_Aires")

LOCAL_TZ = ZoneInfo(DEFAULT_TZ)
