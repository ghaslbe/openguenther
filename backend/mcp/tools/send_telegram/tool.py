import requests as http_requests

from config import get_settings
from services.tool_context import get_emit_log

TELEGRAM_API = "https://api.telegram.org/bot{token}/{method}"

TOOL_DEFINITION = {
    "name": "send_telegram",
    "description": (
        "Sendet eine Textnachricht über Telegram an einen bestimmten Nutzer. "
        "Akzeptiert als Empfänger entweder einen @username (z.B. '@mama75') "
        "oder direkt die numerische Telegram-Chat-ID (z.B. '5761888867'). "
        "Bei @username muss der Nutzer dem Bot vorher mindestens einmal geschrieben haben. "
        "Verwende dieses Tool wenn der Nutzer möchte, dass Guenther ein Ergebnis "
        "(z.B. Wetterdaten, Aktienkurs, Zusammenfassung) per Telegram weiterleitet."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "recipient": {
                "type": "string",
                "description": (
                    "Empfänger: entweder @username (z.B. '@mama75' oder 'mama75') "
                    "oder direkt die numerische Telegram-Chat-ID (z.B. '5761888867'). "
                    "Bei @username wird die ID aus dem gespeicherten Mapping gelesen — "
                    "der Nutzer muss dem Bot dafür vorher mindestens einmal geschrieben haben. "
                    "Mit der numerischen ID funktioniert es sofort ohne vorherigen Kontakt."
                )
            },
            "message": {
                "type": "string",
                "description": "Der Nachrichtentext der gesendet werden soll (max. 4096 Zeichen)."
            }
        },
        "required": ["recipient", "message"]
    }
}


def handler(recipient: str, message: str) -> dict:
    emit_log = get_emit_log()

    def log(msg):
        if emit_log:
            emit_log({"type": "text", "message": msg})

    def header(msg):
        if emit_log:
            emit_log({"type": "header", "message": msg})

    recipient = recipient.strip()

    # Get bot token from settings
    settings = get_settings()
    token = settings.get('telegram', {}).get('bot_token', '').strip()
    if not token:
        return {"success": False, "error": "Kein Telegram Bot Token konfiguriert. Bitte in den Einstellungen → Telegram eintragen."}

    # Determine telegram_chat_id: numeric ID directly, or lookup by username
    if recipient.lstrip('-').isdigit():
        telegram_chat_id = int(recipient)
        display = str(telegram_chat_id)
    else:
        username = recipient.lstrip('@')
        display = f"@{username}"
        from services.telegram_gateway import get_telegram_chat_id
        telegram_chat_id = get_telegram_chat_id(username)
        if not telegram_chat_id:
            return {
                "success": False,
                "error": (
                    f"Kein Telegram-Chat für '@{username}' gefunden. "
                    f"Entweder muss der Nutzer dem Bot zuerst einmal schreiben, "
                    f"oder du kannst die numerische Chat-ID direkt angeben (z.B. '5761888867')."
                )
            }

    header(f"TELEGRAM → {display}")

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
            log(f"Nachricht an {display} gesendet ({len(message)} Zeichen)")
            header("TELEGRAM: GESENDET")
            return {"success": True, "recipient": display, "chars": len(message)}
        else:
            err = result.get("description", "Unbekannter Fehler")
            log(f"Telegram-Fehler: {err}")
            return {"success": False, "error": f"Telegram API Fehler: {err}"}
    except Exception as e:
        return {"success": False, "error": f"Verbindungsfehler: {str(e)}"}
