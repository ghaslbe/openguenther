from PIL import Image, ImageDraw, ImageFont
import io
import base64


def text_to_image(text, font_size=32, bg_color='white', text_color='black', width=800):
    """Renders text as a PNG image and returns it as base64."""
    img = Image.new('RGB', (width, 100), color=bg_color)
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", font_size)
    except (IOError, OSError):
        font = ImageFont.load_default()

    # Word wrap
    lines = []
    for paragraph in text.split('\n'):
        if not paragraph:
            lines.append('')
            continue
        words = paragraph.split(' ')
        current_line = ''
        for word in words:
            test_line = (current_line + ' ' + word).strip()
            bbox = draw.textbbox((0, 0), test_line, font=font)
            if bbox[2] > width - 40 and current_line:
                lines.append(current_line)
                current_line = word
            else:
                current_line = test_line
        if current_line:
            lines.append(current_line)

    if not lines:
        lines = [text]

    line_height = font_size + 10
    height = max(80, len(lines) * line_height + 40)

    img = Image.new('RGB', (width, height), color=bg_color)
    draw = ImageDraw.Draw(img)

    y = 20
    for line in lines:
        draw.text((20, y), line, fill=text_color, font=font)
        y += line_height

    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

    return {
        "image_base64": img_base64,
        "mime_type": "image/png",
        "width": width,
        "height": height
    }


TOOL_DEFINITION = {
    "name": "text_to_image",
    "description": "Wandelt einen Text in ein Bild (PNG) um und gibt es als Base64-String zurueck.",
    "input_schema": {
        "type": "object",
        "properties": {
            "text": {
                "type": "string",
                "description": "Der Text, der als Bild dargestellt werden soll"
            },
            "font_size": {
                "type": "integer",
                "description": "Schriftgroesse in Pixeln (Standard: 32)",
                "default": 32
            },
            "bg_color": {
                "type": "string",
                "description": "Hintergrundfarbe, z.B. 'white', 'black', '#ff0000'",
                "default": "white"
            },
            "text_color": {
                "type": "string",
                "description": "Textfarbe, z.B. 'black', 'white', '#00ff00'",
                "default": "black"
            },
            "width": {
                "type": "integer",
                "description": "Bildbreite in Pixeln (Standard: 800)",
                "default": 800
            }
        },
        "required": ["text"]
    }
}

SETTINGS_INFO = """**Text als PNG rendern**

Rendert beliebigen Text als Bild — nützlich für Zitate, Beschriftungen, Platzhalter oder überall wo Text als Bild benötigt wird. Kein API-Key nötig, alles läuft lokal mit Pillow.

Die hier konfigurierten Werte sind die Standardeinstellungen. Im Chat können Schriftgröße, Farben und Breite pro Anfrage überschrieben werden."""

SETTINGS_SCHEMA = [
    {"key": "default_font_size", "label": "Standard-Schriftgroesse", "type": "text", "placeholder": "32", "default": "32"},
    {"key": "default_bg_color", "label": "Standard-Hintergrundfarbe", "type": "text", "placeholder": "white", "default": "white"},
    {"key": "default_text_color", "label": "Standard-Textfarbe", "type": "text", "placeholder": "black", "default": "black"},
    {"key": "default_width", "label": "Standard-Bildbreite (px)", "type": "text", "placeholder": "800", "default": "800"},
]
