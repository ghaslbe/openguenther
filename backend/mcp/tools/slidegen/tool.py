import io
import re
import json
import base64

from config import get_settings, get_tool_settings
from services.tool_context import get_emit_log

SETTINGS_INFO = """**PowerPoint-Präsentationen generieren**

Erstellt vollständige .pptx-Dateien aus einem Thema oder Text. Kein eigener API-Key nötig — läuft über den konfigurierten LLM-Provider.

**Modell:** Für beste Ergebnisse ein leistungsfähiges Modell mit großem Kontextfenster wählen, z.B. `google/gemini-flash-1.5` oder `openai/gpt-4o`. Mit einem schwächeren Modell können Struktur und Inhalte schlechter ausfallen.

**Themes:** `dark` (dunkel mit orangefarbenen Akzenten) oder `purple` (dunkel mit lila Akzenten). 8 verschiedene Folienlayouts werden automatisch gemischt."""

SETTINGS_SCHEMA = [
    {
        "key": "model",
        "label": "Modell",
        "type": "text",
        "placeholder": "leer = Standard-Modell verwenden",
        "description": "LLM-Modell für die Folien-Generierung (empfohlen: google/gemini-flash-1.5 oder openai/gpt-4o)"
    },
    {
        "key": "theme",
        "label": "Standard-Theme",
        "type": "text",
        "placeholder": "dark",
        "description": "Farbthema: 'dark' (dunkel/orange) oder 'purple' (dunkel/lila)"
    }
]

TOOL_DEFINITION = {
    "name": "generate_presentation",
    "description": (
        "Erstellt eine professionelle PowerPoint-Präsentation (.pptx) auf Basis eines Themas oder Textes. "
        "Generiert automatisch Folien mit verschiedenen Layouts (Titel, Karten, Spalten, Schritte, etc.). "
        "Gibt eine .pptx-Datei zum Download zurück."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "topic": {
                "type": "string",
                "description": "Thema oder Titel der Präsentation, z.B. 'Machine Learning Grundlagen' oder 'Unser Q4-Ausblick'"
            },
            "source_text": {
                "type": "string",
                "description": "Optionaler Quelltext als inhaltliche Basis. Das LLM strukturiert und visualisiert ihn — nicht wörtlich übernommen."
            },
            "theme": {
                "type": "string",
                "description": "Farbthema: 'dark' (dunkel mit Orange-Akzent, Standard) oder 'purple' (dunkel mit Lila-Akzent)"
            }
        },
        "required": ["topic"]
    }
}


def handler(topic: str, source_text: str = "", theme: str = "") -> dict:
    emit_log = get_emit_log()
    settings = get_settings()
    tool_cfg = get_tool_settings("generate_presentation")

    provider_id = settings.get('default_provider', 'openrouter')
    providers = settings.get('providers', {})
    provider_cfg = providers.get(provider_id, {})
    api_key = provider_cfg.get('api_key', '') or settings.get('openrouter_api_key', '')
    base_url = provider_cfg.get('base_url', 'https://openrouter.ai/api/v1')
    model = (tool_cfg.get('model') or '').strip() or settings.get('model', 'google/gemini-flash-1.5')
    theme = theme or (tool_cfg.get('theme') or '').strip() or 'dark'

    def log(msg):
        if emit_log:
            emit_log({"type": "text", "message": msg})

    def header(msg):
        if emit_log:
            emit_log({"type": "header", "message": msg})

    # Import slidegen internals (deferred to avoid startup crash if packages missing)
    try:
        import slidegen as sg
    except (ImportError, SystemExit) as e:
        return {"error": f"slidegen nicht verfügbar: {e}. Bitte 'python-pptx' und 'lxml' installieren."}

    if theme not in sg.THEMES:
        theme = 'dark'

    header("SLIDEGEN: PRÄSENTATION GENERIEREN")
    log(f"Thema: {topic} | Modell: {model} | Theme: {theme}")

    # Build user message (same format as slidegen CLI)
    if source_text:
        user_msg = (
            f"Create a presentation about: {topic}\n\n"
            f"Use the following source text as the basis for the content "
            f"(summarise, structure and visualise it — do not copy verbatim):\n\n"
            f"{source_text}"
        )
    else:
        user_msg = f"Create a presentation about: {topic}"

    # Call LLM with slidegen's system prompt
    header("SLIDEGEN: LLM-ANFRAGE")
    from services.openrouter import call_openrouter as _call_llm
    try:
        response = _call_llm(
            [
                {"role": "system", "content": sg.SYSTEM_PROMPT},
                {"role": "user", "content": user_msg},
            ],
            None, api_key, model, temperature=0.7, base_url=base_url
        )
    except Exception as e:
        return {"error": f"LLM-Fehler: {str(e)}"}

    raw = response.get("choices", [{}])[0].get("message", {}).get("content", "")
    usage = response.get("usage", {})
    if usage:
        log(f"Tokens: prompt={usage.get('prompt_tokens','?')} completion={usage.get('completion_tokens','?')}")

    # Parse JSON from LLM response
    try:
        data = sg._parse_json(raw)
    except Exception as e:
        return {"error": f"JSON-Parsing-Fehler: {str(e)}", "raw_preview": raw[:300]}

    pres_title = data.get("presentation_title", topic)
    slides = data.get("slides", [])

    header("SLIDEGEN: FOLIEN ERSTELLEN")
    log(f"Titel: {pres_title} | Folien: {len(slides)}")

    # Set theme (module-level global in slidegen.py)
    sg.T = sg.THEMES[theme]

    # Build PPTX
    try:
        prs = sg.build_pptx(slides)
    except Exception as e:
        return {"error": f"PPTX-Fehler: {str(e)}"}

    # Serialize to bytes
    buf = io.BytesIO()
    prs.save(buf)
    pptx_bytes = buf.getvalue()
    pptx_b64 = base64.b64encode(pptx_bytes).decode()

    # Build filename
    safe = re.sub(r'[^\w\s-]', '', topic).strip()
    safe = re.sub(r'\s+', '-', safe).lower()[:50]
    filename = f"{safe}.pptx"

    log(f"Fertig — {len(slides)} Folien, {len(pptx_bytes) // 1024} KB → {filename}")
    header("SLIDEGEN: FERTIG")

    return {
        "success": True,
        "title": pres_title,
        "slides": len(slides),
        "filename": filename,
        "pptx_base64": pptx_b64,
    }
