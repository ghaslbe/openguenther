import secrets
import string


def generate_password(length=16, include_special=True, include_numbers=True, include_uppercase=True):
    """Generate a secure random password."""
    length = max(4, min(length, 128))

    chars = string.ascii_lowercase
    required = [secrets.choice(string.ascii_lowercase)]

    if include_uppercase:
        chars += string.ascii_uppercase
        required.append(secrets.choice(string.ascii_uppercase))
    if include_numbers:
        chars += string.digits
        required.append(secrets.choice(string.digits))
    if include_special:
        chars += "!@#$%&*+-=?"
        required.append(secrets.choice("!@#$%&*+-=?"))

    remaining = length - len(required)
    password_chars = required + [secrets.choice(chars) for _ in range(remaining)]

    # Shuffle
    password = list(password_chars)
    secrets.SystemRandom().shuffle(password)

    return {
        "password": ''.join(password),
        "length": length,
        "includes_special": include_special,
        "includes_numbers": include_numbers,
        "includes_uppercase": include_uppercase
    }


TOOL_DEFINITION = {
    "name": "generate_password",
    "description": "Generiert ein sicheres zufaelliges Passwort mit konfigurierbarer Laenge und Zeichentypen.",
    "input_schema": {
        "type": "object",
        "properties": {
            "length": {
                "type": "integer",
                "description": "Laenge des Passworts (Standard: 16, Min: 4, Max: 128)",
                "default": 16
            },
            "include_special": {
                "type": "boolean",
                "description": "Sonderzeichen einschliessen (Standard: true)",
                "default": True
            },
            "include_numbers": {
                "type": "boolean",
                "description": "Zahlen einschliessen (Standard: true)",
                "default": True
            },
            "include_uppercase": {
                "type": "boolean",
                "description": "Grossbuchstaben einschliessen (Standard: true)",
                "default": True
            }
        },
        "required": []
    }
}
