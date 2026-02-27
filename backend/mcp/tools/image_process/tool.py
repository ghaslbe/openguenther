import io
import base64
import subprocess

from services.image_store import get as get_stored_image

TOOL_DEFINITION = {
    "name": "process_image",
    "description": (
        "Bearbeitet ein Bild mit ImageMagick (unscharf machen, Graustufen, rotieren, "
        "skalieren, schärfen, Helligkeit/Kontrast, spiegeln, invertieren). "
        "Das Bild wird per session_key (wenn via Telegram gesendet) oder als "
        "direkter base64-String übergeben."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "session_key": {
                "type": "string",
                "description": (
                    "Session-Key des gespeicherten Bildes (wird im System-Hinweis "
                    "bereitgestellt, wenn der Nutzer ein Bild via Telegram geschickt hat)"
                )
            },
            "image_b64": {
                "type": "string",
                "description": "Alternatives direktes Übergeben als Base64-kodierter String"
            },
            "operation": {
                "type": "string",
                "description": "Die Bildbearbeitungs-Operation",
                "enum": [
                    "blur",
                    "grayscale",
                    "rotate",
                    "resize",
                    "sharpen",
                    "brightness",
                    "contrast",
                    "flip_horizontal",
                    "flip_vertical",
                    "invert"
                ]
            },
            "radius": {
                "type": "number",
                "description": "Unschärfe-Radius für 'blur' (Standard: 5)"
            },
            "angle": {
                "type": "number",
                "description": "Rotationswinkel in Grad für 'rotate' (Standard: 90)"
            },
            "width": {
                "type": "integer",
                "description": "Neue Breite in Pixeln für 'resize'"
            },
            "height": {
                "type": "integer",
                "description": "Neue Höhe in Pixeln für 'resize'"
            },
            "factor": {
                "type": "number",
                "description": (
                    "Stärke für 'brightness' oder 'contrast' "
                    "(1.0 = original, 2.0 = doppelt, 0.5 = halb; Standard: 1.5)"
                )
            }
        },
        "required": ["operation"]
    }
}


def _imagemagick(input_bytes, *args):
    """Run ImageMagick convert: stdin → args → stdout (PNG). Raises on error."""
    cmd = ["convert", "-"] + list(args) + ["png:-"]
    result = subprocess.run(cmd, input=input_bytes, capture_output=True, timeout=30)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.decode(errors="replace").strip())
    return result.stdout


def process_image(operation, session_key=None, image_b64=None,
                  radius=5, angle=90, width=None, height=None, factor=1.5):
    # Resolve raw bytes
    raw_b64 = None
    if image_b64:
        raw_b64 = image_b64
    elif session_key:
        stored = get_stored_image(session_key)
        if not stored:
            return {"error": f"Kein Bild für Session-Key '{session_key}' gefunden."}
        raw_b64 = stored["b64"]
    else:
        return {"error": "Entweder 'session_key' oder 'image_b64' muss angegeben werden."}

    try:
        input_bytes = base64.b64decode(raw_b64)
    except Exception as e:
        return {"error": f"Base64-Dekodierung fehlgeschlagen: {e}"}

    try:
        if operation == "blur":
            r = float(radius)
            out = _imagemagick(input_bytes, "-blur", f"0x{r}")

        elif operation == "grayscale":
            out = _imagemagick(input_bytes, "-colorspace", "Gray")

        elif operation == "rotate":
            out = _imagemagick(input_bytes, "-rotate", str(float(angle)))

        elif operation == "resize":
            if width and height:
                geom = f"{int(width)}x{int(height)}!"
            elif width:
                geom = f"{int(width)}x"
            elif height:
                geom = f"x{int(height)}"
            else:
                return {"error": "Für 'resize' muss width und/oder height angegeben werden."}
            out = _imagemagick(input_bytes, "-resize", geom)

        elif operation == "sharpen":
            out = _imagemagick(input_bytes, "-sharpen", "0x1")

        elif operation == "brightness":
            pct = int(float(factor) * 100)
            out = _imagemagick(input_bytes, "-modulate", f"{pct},100,100")

        elif operation == "contrast":
            # -brightness-contrast 0,val  (val: -100..100)
            val = int((float(factor) - 1.0) * 50)
            val = max(-100, min(100, val))
            out = _imagemagick(input_bytes, "-brightness-contrast", f"0,{val}")

        elif operation == "flip_horizontal":
            out = _imagemagick(input_bytes, "-flop")

        elif operation == "flip_vertical":
            out = _imagemagick(input_bytes, "-flip")

        elif operation == "invert":
            out = _imagemagick(input_bytes, "-negate")

        else:
            return {"error": f"Unbekannte Operation: '{operation}'"}

    except subprocess.TimeoutExpired:
        return {"error": "ImageMagick Timeout (>30s)"}
    except FileNotFoundError:
        return {"error": "ImageMagick nicht gefunden. Bitte im Container installieren."}
    except Exception as e:
        return {"error": f"Bildverarbeitung fehlgeschlagen: {e}"}

    result_b64 = base64.b64encode(out).decode()
    return {
        "image_base64": result_b64,
        "mime_type": "image/png",
        "operation": operation
    }
