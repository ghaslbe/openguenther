import base64
import urllib.request
import json

from config import get_tool_settings
from services.tool_context import get_emit_log

SETTINGS_INFO = """**Text-to-Speech via ElevenLabs**

Wandelt Text in natürlich klingende Sprache um und spielt das Audio direkt im Chat ab. Über Telegram wird die Audiodatei versendet.

**API Key:** Kostenlosen Account auf [elevenlabs.io](https://elevenlabs.io) anlegen → Profile → API Key. Das kostenlose Kontingent reicht für Tests.

**Voice ID:** Jede Stimme hat eine eindeutige ID. Eigene Stimmen und alle öffentlichen Stimmen findest du in der [ElevenLabs Voice Library](https://elevenlabs.io/app/voice-library). Die Standard-Stimme "Rachel" (ID: `21m00Tcm4TlvDq8ikWAM`) ist eine gute Ausgangsbasis."""

SETTINGS_SCHEMA = [
    {"key": "api_key", "label": "ElevenLabs API Key", "type": "password",
     "placeholder": "sk_...", "description": "API Key von elevenlabs.io"},
    {"key": "voice_id", "label": "Voice ID", "type": "text",
     "placeholder": "21m00Tcm4TlvDq8ikWAM",
     "description": "Voice ID (leer = Standard: Rachel)",
     "default": "21m00Tcm4TlvDq8ikWAM"},
    {"key": "model_id", "label": "Modell", "type": "text",
     "placeholder": "eleven_multilingual_v2",
     "description": "z.B. eleven_multilingual_v2 oder eleven_turbo_v2_5",
     "default": "eleven_multilingual_v2"},
]

TOOL_DEFINITION = {
    "name": "text_to_speech",
    "description": "Wandelt Text in gesprochene Sprache um (ElevenLabs). Gibt Audio zurück das direkt im Chat abgespielt wird.",
    "input_schema": {
        "type": "object",
        "properties": {
            "text": {"type": "string", "description": "Der vorzulesende Text"}
        },
        "required": ["text"]
    }
}


def text_to_speech(text):
    emit_log = get_emit_log()
    cfg = get_tool_settings("text_to_speech")

    api_key = cfg.get("api_key", "")
    if not api_key:
        return {"error": "Kein ElevenLabs API Key konfiguriert. Bitte in den Tool-Einstellungen eingeben."}

    voice_id = (cfg.get("voice_id") or "").strip() or "21m00Tcm4TlvDq8ikWAM"
    model_id = (cfg.get("model_id") or "").strip() or "eleven_multilingual_v2"

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    body = json.dumps({
        "text": text,
        "model_id": model_id,
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}
    }).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "xi-api-key": api_key,
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
        },
        method="POST"
    )

    preview = text if len(text) <= 60 else text[:57] + "..."
    if emit_log:
        emit_log({"type": "text", "message": f"[TTS] Spreche vor: \"{preview}\""})
        emit_log({"type": "text", "message": f"[TTS] Modell: {model_id} | Voice: {voice_id}"})
        emit_log({"type": "text", "message": f"[TTS] Sende Anfrage an ElevenLabs..."})

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            audio_bytes = resp.read()
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace")
        if emit_log:
            emit_log({"type": "text", "message": f"[TTS] FEHLER {e.code}: {error_body}"})
        return {"error": f"ElevenLabs API Fehler {e.code}: {error_body}"}

    if emit_log:
        kb = len(audio_bytes) / 1024
        emit_log({"type": "text", "message": f"[TTS] Audio empfangen: {kb:.1f} KB — fertig!"})

    return {
        "audio_base64": base64.b64encode(audio_bytes).decode(),
        "mime_type": "audio/mpeg",
    }
