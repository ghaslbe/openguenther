import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import get_tool_settings


def send_email(to, subject, body, html=False):
    """Send an email via SMTP using tool-specific settings."""
    cfg = get_tool_settings('send_email')
    smtp_server = cfg.get('smtp_server', '')
    smtp_port = int(cfg.get('smtp_port', 587))
    smtp_user = cfg.get('smtp_user', '')
    smtp_password = cfg.get('smtp_password', '')
    from_name = cfg.get('smtp_from_name', 'Guenther')
    smtp_timeout = int(cfg.get('timeout') or 30)

    if not all([smtp_server, smtp_user, smtp_password]):
        return {
            "error": "SMTP nicht konfiguriert. Bitte in den Tool-Einstellungen von 'send_email' hinterlegen."
        }

    try:
        msg = MIMEMultipart('alternative')
        msg['From'] = f"{from_name} <{smtp_user}>"
        msg['To'] = to
        msg['Subject'] = subject

        if html:
            msg.attach(MIMEText(body, 'html', 'utf-8'))
        else:
            msg.attach(MIMEText(body, 'plain', 'utf-8'))

        with smtplib.SMTP(smtp_server, smtp_port, timeout=smtp_timeout) as server:
            server.ehlo()
            if smtp_port != 25:
                server.starttls()
                server.ehlo()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)

        return {
            "success": True,
            "message": f"E-Mail erfolgreich gesendet an {to}",
            "to": to,
            "subject": subject
        }
    except Exception as e:
        return {"error": f"E-Mail konnte nicht gesendet werden: {str(e)}"}


TOOL_DEFINITION = {
    "name": "send_email",
    "description": "Sendet eine E-Mail ueber SMTP. SMTP-Server muss in den Tool-Einstellungen konfiguriert sein.",
    "input_schema": {
        "type": "object",
        "properties": {
            "to": {
                "type": "string",
                "description": "Empfaenger-E-Mail-Adresse"
            },
            "subject": {
                "type": "string",
                "description": "Betreff der E-Mail"
            },
            "body": {
                "type": "string",
                "description": "Inhalt der E-Mail"
            },
            "html": {
                "type": "boolean",
                "description": "Ob der Body HTML ist (Standard: false)",
                "default": False
            }
        },
        "required": ["to", "subject", "body"]
    }
}

SETTINGS_SCHEMA = [
    {"key": "smtp_server", "label": "SMTP Server", "type": "text", "placeholder": "smtp.gmail.com"},
    {"key": "smtp_port", "label": "SMTP Port", "type": "text", "placeholder": "587", "default": "587"},
    {"key": "smtp_user", "label": "E-Mail-Adresse / Benutzer", "type": "text", "placeholder": "deine@email.de"},
    {"key": "smtp_password", "label": "Passwort", "type": "password", "placeholder": "App-Passwort"},
    {"key": "smtp_from_name", "label": "Absendername", "type": "text", "placeholder": "Guenther", "default": "Guenther"},
]
