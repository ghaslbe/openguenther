import base64

from config import get_settings, get_tool_settings
from services.openrouter import generate_image as _generate_image
from services.tool_context import get_emit_log

SETTINGS_SCHEMA = [
    {
        "key": "image_model",
        "label": "Bildgenerierungs-Modell",
        "type": "text",
        "placeholder": "leer = Standard-Modell verwenden",
        "description": "z.B. google/gemini-2.5-flash-image-preview oder black-forest-labs/flux-1.1-pro"
    }
]

TOOL_DEFINITION = {
    "name": "generate_image",
    "description": (
        "Generiert ein Bild anhand einer Beschreibung (Prompt) mit einem KI-Bildgenerierungs-Modell. "
        "Gibt das fertige Bild zurück. Nutze dies wenn der Benutzer ein Bild erstellen, zeichnen oder "
        "generieren lassen möchte."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "prompt": {
                "type": "string",
                "description": (
                    "Detaillierte Bildbeschreibung auf Englisch für beste Ergebnisse, "
                    "z.B. 'a photorealistic cat sitting on a red sofa, warm lighting'"
                )
            },
            "aspect_ratio": {
                "type": "string",
                "description": "Seitenverhältnis des Bildes (Standard: 1:1)",
                "enum": ["1:1", "16:9", "4:3", "3:4", "9:16", "21:9"]
            }
        },
        "required": ["prompt"]
    }
}


def generate_image(prompt, aspect_ratio="1:1"):
    settings = get_settings()
    api_key = settings.get("providers", {}).get("openrouter", {}).get("api_key", "") \
              or settings.get("openrouter_api_key", "")
    if not api_key:
        return {"error": "Kein OpenRouter API-Key konfiguriert."}

    tool_cfg = get_tool_settings("generate_image")
    # Prefer tool-specific image_model, fall back to legacy image_gen_model, then default model
    model = (tool_cfg.get("image_model") or tool_cfg.get("model") or "").strip() \
            or settings.get("image_gen_model", "") \
            or settings.get("model", "openai/gpt-4o-mini")

    timeout = int(tool_cfg.get("timeout") or 120)
    emit_log = get_emit_log()

    try:
        img_bytes, mime = _generate_image(prompt, api_key, model, aspect_ratio, timeout=timeout, emit_log=emit_log)
    except Exception as e:
        return {"error": str(e), "model_used": model, "hint": "Bildgenerierungs-Modell in MCP Tools > generate_image > Timeout/Modell einstellen."}

    return {
        "image_base64": base64.b64encode(img_bytes).decode(),
        "mime_type": mime,
        "prompt": prompt,
        "model": model,
    }
