from datetime import datetime
from zoneinfo import ZoneInfo


def get_current_time(timezone='Europe/Berlin', format='%Y-%m-%d %H:%M:%S'):
    """Returns the current time in the specified timezone and format."""
    try:
        tz = ZoneInfo(timezone)
    except (KeyError, ValueError):
        tz = ZoneInfo('UTC')
    now = datetime.now(tz)
    return {
        "time": now.strftime(format),
        "timezone": timezone,
        "iso": now.isoformat()
    }


TOOL_DEFINITION = {
    "name": "get_current_time",
    "description": "Gibt die aktuelle Uhrzeit zurueck. Kann eine Zeitzone und ein Format angeben.",
    "input_schema": {
        "type": "object",
        "properties": {
            "timezone": {
                "type": "string",
                "description": "Zeitzone, z.B. 'Europe/Berlin', 'UTC', 'US/Eastern'",
                "default": "Europe/Berlin"
            },
            "format": {
                "type": "string",
                "description": "Zeitformat, z.B. '%H:%M:%S', '%Y-%m-%d %H:%M:%S'",
                "default": "%Y-%m-%d %H:%M:%S"
            }
        },
        "required": []
    }
}
