import base64

from config import get_settings
from services.openrouter import generate_image as _generate_image

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
    api_key = settings.get("openrouter_api_key", "")
    if not api_key:
        return {"error": "Kein OpenRouter API-Key konfiguriert."}

    model = settings.get("image_gen_model") or settings.get("model", "openai/gpt-4o-mini")

    try:
        img_bytes, mime = _generate_image(prompt, api_key, model, aspect_ratio)
    except Exception as e:
        return {"error": str(e)}

    return {
        "image_base64": base64.b64encode(img_bytes).decode(),
        "mime_type": mime,
        "prompt": prompt,
        "model": model,
    }
