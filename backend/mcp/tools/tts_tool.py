import base64
import urllib.request
import json

from config import get_tool_settings
from services.tool_context import get_emit_log

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

    if emit_log:
        emit_log({"type": "header", "message": "TTS API REQUEST"})
        emit_log({"type": "json", "label": "request", "data": {
            "url": url,
            "voice_id": voice_id,
            "model_id": model_id,
            "text_length": len(text),
        }})

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            audio_bytes = resp.read()
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace")
        if emit_log:
            emit_log({"type": "text", "message": f"TTS API Fehler {e.code}: {error_body}"})
        return {"error": f"ElevenLabs API Fehler {e.code}: {error_body}"}

    if emit_log:
        emit_log({"type": "text", "message": f"TTS API Response: {len(audio_bytes)} Bytes MP3"})

    return {
        "audio_base64": base64.b64encode(audio_bytes).decode(),
        "mime_type": "audio/mpeg",
    }
