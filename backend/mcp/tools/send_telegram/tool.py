import requests as http_requests

from config import get_settings
from services.tool_context import get_emit_log

TELEGRAM_API = "https://api.telegram.org/bot{token}/{method}"

TOOL_DEFINITION = {
    "name": "send_telegram",
    "description": (
        "Sendet eine Textnachricht über Telegram an einen bestimmten Nutzer. "
        "Der Nutzer muss dem Bot vorher mindestens einmal geschrieben haben. "
        "Verwende dieses Tool wenn der Nutzer möchte, dass Guenther ein Ergebnis "
        "(z.B. Wetterdaten, Aktienkurs, Zusammenfassung) per Telegram weiterleitet."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "username": {
                "type": "string",
                "description": (
                    "Telegram-Username des Empfängers (mit oder ohne @), z.B. '@meinname' oder 'meinname'. "
                    "Der Nutzer muss dem Bot bereits mindestens einmal geschrieben haben."
                )
            },
            "message": {
                "type": "string",
                "description": "Der Nachrichtentext der gesendet werden soll (max. 4096 Zeichen)."
            }
        },
        "required": ["username", "message"]
    }
}


def handler(username: str, message: str) -> dict:
    emit_log = get_emit_log()

    def log(msg):
        if emit_log:
            emit_log({"type": "text", "message": msg})

    def header(msg):
        if emit_log:
            emit_log({"type": "header", "message": msg})

    # Normalize username
    username = username.lstrip('@').strip()
    header(f"TELEGRAM → @{username}")

    # Get bot token from settings
    settings = get_settings()
    token = settings.get('telegram', {}).get('bot_token', '').strip()
    if not token:
        return {"success": False, "error": "Kein Telegram Bot Token konfiguriert. Bitte in den Einstellungen → Telegram eintragen."}

    # Look up Telegram chat_id for the username
    from services.telegram_gateway import get_telegram_chat_id
    telegram_chat_id = get_telegram_chat_id(username)
    if not telegram_chat_id:
        return {
            "success": False,
            "error": (
                f"Kein Telegram-Chat für '@{username}' gefunden. "
                f"Der Nutzer muss dem Bot zuerst mindestens einmal schreiben, "
                f"damit die Verbindung bekannt ist."
            )
        }

    # Truncate if necessary
    if len(message) > 4096:
        message = message[:4090] + "\n[...]"

    url = TELEGRAM_API.format(token=token, method="sendMessage")
    try:
        r = http_requests.post(
            url,
            json={"chat_id": telegram_chat_id, "text": message},
            timeout=10
        )
        result = r.json()
        if result.get("ok"):
            log(f"Nachricht an @{username} gesendet ({len(message)} Zeichen)")
            header("TELEGRAM: GESENDET")
            return {"success": True, "recipient": f"@{username}", "chars": len(message)}
        else:
            err = result.get("description", "Unbekannter Fehler")
            log(f"Telegram-Fehler: {err}")
            return {"success": False, "error": f"Telegram API Fehler: {err}"}
    except Exception as e:
        return {"success": False, "error": f"Verbindungsfehler: {str(e)}"}
