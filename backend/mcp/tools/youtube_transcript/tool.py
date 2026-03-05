import re

from config import get_tool_settings
from services.tool_context import get_emit_log

SETTINGS_INFO = """**YouTube Transkript abrufen**

Lädt das automatisch generierte oder manuell erstellte Transkript eines YouTube-Videos.

**Kein API Key nötig** — die Library greift direkt auf YouTubes interne Transkript-API zu.

**Sprachen:** Kommagetrennte Prioritätsliste, z.B. `de,en` — das Tool versucht die Sprachen
der Reihe nach und fällt auf jede verfügbare Sprache zurück wenn keine passt."""

SETTINGS_SCHEMA = [
    {
        "key": "languages",
        "label": "Bevorzugte Sprachen",
        "type": "text",
        "placeholder": "de,en",
        "default": "de,en",
        "description": "Kommagetrennte Sprachliste in Prioritätsreihenfolge (z.B. de,en)"
    },
]

TOOL_DEFINITION = {
    "name": "get_youtube_transcript",
    "description": (
        "Lädt das Transkript eines YouTube-Videos als Text. "
        "Akzeptiert eine vollständige YouTube-URL oder direkt die Video-ID. "
        "Gibt den kompletten Transkripttext zurück. Kein API Key erforderlich."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": (
                    "YouTube-URL (z.B. https://www.youtube.com/watch?v=jwBe5QA1x3E "
                    "oder https://youtu.be/jwBe5QA1x3E) oder direkt die Video-ID (z.B. jwBe5QA1x3E)"
                )
            }
        },
        "required": ["url"]
    }
}


def _extract_video_id(url: str) -> str:
    """Extrahiert die Video-ID aus verschiedenen YouTube-URL-Formaten."""
    url = url.strip()
    # Bereits eine reine Video-ID (11 Zeichen alphanumerisch + - + _)
    if re.match(r'^[\w-]{11}$', url):
        return url
    # youtube.com/watch?v=ID
    m = re.search(r'[?&]v=([\w-]{11})', url)
    if m:
        return m.group(1)
    # youtu.be/ID
    m = re.search(r'youtu\.be/([\w-]{11})', url)
    if m:
        return m.group(1)
    # youtube.com/embed/ID oder /v/ID
    m = re.search(r'youtube\.com/(?:embed|v)/([\w-]{11})', url)
    if m:
        return m.group(1)
    return ""


def handler(url: str) -> dict:
    emit_log = get_emit_log()

    def log(msg):
        if emit_log:
            emit_log({"type": "text", "message": msg})

    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        from youtube_transcript_api._errors import NoTranscriptFound, TranscriptsDisabled
    except ImportError:
        return {"error": "youtube-transcript-api nicht installiert. Bitte requirements.txt prüfen."}

    if not url or not url.strip():
        return {"error": "Bitte eine YouTube-URL oder Video-ID angeben."}

    video_id = _extract_video_id(url.strip())
    if not video_id:
        return {"error": f"Konnte keine gültige Video-ID aus '{url}' extrahieren."}

    cfg = get_tool_settings("get_youtube_transcript")
    languages_raw = cfg.get("languages", "").strip() or "de,en"
    languages = [l.strip() for l in languages_raw.split(",") if l.strip()]

    log(f"[YouTube] Video-ID: {video_id}")
    log(f"[YouTube] Bevorzugte Sprachen: {', '.join(languages)}")

    ytt_api = YouTubeTranscriptApi()

    # Erst mit gewünschten Sprachen versuchen, dann Fallback auf alles verfügbare
    used_language = None
    try:
        fetched = ytt_api.fetch(video_id, languages=languages)
        used_language = languages[0]
    except NoTranscriptFound:
        log(f"[YouTube] Keine der bevorzugten Sprachen verfügbar — versuche jede verfügbare...")
        try:
            transcript_list = ytt_api.list(video_id)
            transcript = next(iter(transcript_list))
            fetched = transcript.fetch()
            used_language = transcript.language_code
        except Exception as e:
            return {"error": f"Kein Transkript verfügbar für Video {video_id}: {str(e)}"}
    except TranscriptsDisabled:
        return {"error": f"Transkripte sind für Video {video_id} deaktiviert."}
    except Exception as e:
        return {"error": f"Fehler beim Abrufen des Transkripts: {str(e)}"}

    full_text = " ".join(snippet.text for snippet in fetched)
    word_count = len(full_text.split())

    log(f"[YouTube] Transkript geladen: {len(fetched)} Segmente, ~{word_count} Wörter, Sprache: {used_language}")

    return {
        "video_id": video_id,
        "language": used_language,
        "segments": len(fetched),
        "word_count": word_count,
        "transcript": full_text,
    }
