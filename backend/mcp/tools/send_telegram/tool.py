import os
import io
import requests as http_requests

from config import get_settings
from services.tool_context import get_emit_log

TELEGRAM_API = "https://api.telegram.org/bot{token}/{method}"

_AUDIO_MIME = {
    '.mp3': 'audio/mpeg',
    '.wav': 'audio/wav',
    '.ogg': 'audio/ogg',
    '.flac': 'audio/flac',
    '.m4a': 'audio/mp4',
    '.aac': 'audio/aac',
    '.opus': 'audio/opus',
}

TOOL_DEFINITION = {
    "name": "send_telegram",
    "description": (
        "Sendet eine Textnachricht oder Audiodatei über Telegram an einen bestimmten Nutzer. "
        "Akzeptiert als Empfänger entweder einen @username (z.B. '@mama75') "
        "oder direkt die numerische Telegram-Chat-ID (z.B. '5761888867'). "
        "Bei @username muss der Nutzer dem Bot vorher mindestens einmal geschrieben haben. "
        "Kann optional eine lokale Audiodatei (MP3, WAV, OGG, FLAC, M4A, AAC, Opus) senden — "
        "dann wird 'message' als Bildunterschrift verwendet."
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
                    "der Nutzer muss dem Bot dafür vorher mindestens einmal geschrieben haben."
                )
            },
            "message": {
                "type": "string",
                "description": "Nachrichtentext (max. 4096 Zeichen). Bei Audiodatei: wird als Bildunterschrift gesendet (optional)."
            },
            "file_path": {
                "type": "string",
                "description": (
                    "Optionaler absoluter Serverpfad zu einer Audiodatei (MP3, WAV, OGG, FLAC, M4A, AAC, Opus). "
                    "Wenn angegeben, wird die Datei als Audio-Nachricht gesendet. "
                    "Beispiel: /app/data/uploads/abc123_audio.wav"
                )
            }
        },
        "required": ["recipient", "message"]
    }
}


def handler(recipient: str, message: str, file_path: str = None) -> dict:
    emit_log = get_emit_log()

    def log(msg):
        if emit_log:
            emit_log({"type": "text", "message": msg})

    def header(msg):
        if emit_log:
            emit_log({"type": "header", "message": msg})

    recipient = recipient.strip()

    settings = get_settings()
    token = settings.get('telegram', {}).get('bot_token', '').strip()
    if not token:
        return {"success": False, "error": "Kein Telegram Bot Token konfiguriert. Bitte in den Einstellungen → Telegram eintragen."}

    # Resolve recipient
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
                    f"oder du kannst die numerische Chat-ID direkt angeben."
                )
            }

    # ── Audio file ────────────────────────────────────────────────────────────
    if file_path:
        file_path = file_path.strip()
        if not os.path.isfile(file_path):
            return {"success": False, "error": f"Datei nicht gefunden: {file_path}"}

        ext = os.path.splitext(file_path)[1].lower()
        mime = _AUDIO_MIME.get(ext)
        if not mime:
            return {"success": False, "error": f"Nicht unterstütztes Dateiformat: {ext}. Erlaubt: MP3, WAV, OGG, FLAC, M4A, AAC, Opus."}

        filename = os.path.basename(file_path)
        header(f"TELEGRAM AUDIO → {display}: {filename}")

        try:
            with open(file_path, 'rb') as f:
                audio_bytes = f.read()

            url = TELEGRAM_API.format(token=token, method="sendAudio")
            files = {"audio": (filename, io.BytesIO(audio_bytes), mime)}
            data = {"chat_id": telegram_chat_id}
            if message:
                data["caption"] = message[:1024]

            r = http_requests.post(url, files=files, data=data, timeout=60)
            result = r.json()
            if result.get("ok"):
                log(f"Audio '{filename}' ({len(audio_bytes) // 1024} KB) an {display} gesendet")
                header("TELEGRAM: GESENDET")
                return {"success": True, "recipient": display, "file": filename, "bytes": len(audio_bytes)}
            else:
                err = result.get("description", "Unbekannter Fehler")
                log(f"Telegram-Fehler: {err}")
                return {"success": False, "error": f"Telegram API Fehler: {err}"}
        except Exception as e:
            return {"success": False, "error": f"Fehler beim Senden: {str(e)}"}

    # ── Text message ──────────────────────────────────────────────────────────
    header(f"TELEGRAM → {display}")

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
