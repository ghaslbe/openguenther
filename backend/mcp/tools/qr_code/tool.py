import qrcode
import io
import base64


def generate_qr_code(text, size=10):
    """Generate a QR code image from text."""
    qr = qrcode.QRCode(version=1, box_size=size, border=4)
    qr.add_data(text)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

    return {
        "image_base64": img_base64,
        "mime_type": "image/png",
        "text_encoded": text
    }


TOOL_DEFINITION = {
    "name": "generate_qr_code",
    "description": "Erzeugt einen QR-Code als Bild (PNG) aus einem Text oder einer URL.",
    "input_schema": {
        "type": "object",
        "properties": {
            "text": {
                "type": "string",
                "description": "Der Text oder die URL, die als QR-Code kodiert werden soll"
            },
            "size": {
                "type": "integer",
                "description": "Groesse der QR-Code-Bloecke in Pixeln (Standard: 10)",
                "default": 10
            }
        },
        "required": ["text"]
    }
}
