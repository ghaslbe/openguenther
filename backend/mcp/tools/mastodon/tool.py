import requests

from config import get_tool_settings
from services.tool_context import get_emit_log

SETTINGS_INFO = """**Toot posten via Mastodon API**

Postet einen Toot auf einer Mastodon-Instanz via REST API.

**Voraussetzungen:**
1. Mastodon-Account auf einer beliebigen Instanz (z.B. mastodon.social)
2. **Access Token** erstellen: Einstellungen → Entwicklung → Neue Anwendung
   → Rechte `write:statuses` aktivieren → Token kopieren
3. **Instanz-URL** und **Access Token** hier eintragen

**Hinweis:** Mastodon blockiert keine Datacenter-IPs — kein Proxy nötig.

> ⚠️ **Achtung:** Dieses Tool kann Daten schreiben, bearbeiten oder loeschen. Fehlerhafte Eingaben koennen zu **Datenverlust oder ungewollten Aktionen** fuehren. Bitte mit Bedacht einsetzen."""

SETTINGS_SCHEMA = [
    {
        "key": "api_base_url",
        "label": "Instanz-URL",
        "type": "text",
        "placeholder": "https://mastodon.social",
        "description": "URL deiner Mastodon-Instanz (ohne abschließenden Slash)"
    },
    {
        "key": "access_token",
        "label": "Access Token",
        "type": "password",
        "placeholder": "...",
        "description": "Access Token aus Einstellungen → Entwicklung → Neue Anwendung"
    },
]

TOOL_DEFINITION = {
    "name": "post_mastodon",
    "description": (
        "Postet einen Toot auf Mastodon. "
        "Maximale Länge: 500 Zeichen. "
        "Benötigt Instanz-URL und Access Token in den Tool-Einstellungen."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "text": {
                "type": "string",
                "description": "Der Toot-Text (max. 500 Zeichen)"
            }
        },
        "required": ["text"]
    }
}


def handler(text: str) -> dict:
    emit_log = get_emit_log()

    def log(msg):
        if emit_log:
            emit_log({"type": "text", "message": msg})

    # ── Eingabe-Validierung ────────────────────────────────────────────────────
    if not text or not text.strip():
        return {"success": False, "error": "Toot-Text darf nicht leer sein."}

    cfg = get_tool_settings("post_mastodon")

    api_base_url = cfg.get("api_base_url", "").strip().rstrip("/")
    access_token = cfg.get("access_token", "").strip()

    missing = [label for label, val in [
        ("Instanz-URL",  api_base_url),
        ("Access Token", access_token),
    ] if not val]
    if missing:
        return {
            "success": False,
            "error": (
                f"Fehlende Mastodon-Zugangsdaten: {', '.join(missing)}. "
                "Bitte in Einstellungen → Tools → post_mastodon eintragen."
            )
        }

    text = text.strip()
    if len(text) > 500:
        text = text[:497] + "..."
        log("[Mastodon] Toot auf 500 Zeichen gekürzt")

    # ── Toot posten ────────────────────────────────────────────────────────────
    log(f"[Mastodon] Poste Toot auf {api_base_url} ({len(text)} Zeichen)...")

    try:
        resp = requests.post(
            f"{api_base_url}/api/v1/statuses",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"status": text},
            timeout=15,
        )
        resp.raise_for_status()
        result = resp.json()
        post_url = result.get("url", "")
        post_id  = result.get("id", "")
        log(f"[Mastodon] Toot erfolgreich gepostet! ID: {post_id}")
        if post_url:
            log(f"[Mastodon] URL: {post_url}")
        return {
            "success": True,
            "id":   post_id,
            "text": text,
            "url":  post_url or None,
        }
    except requests.HTTPError as e:
        body = e.response.text if e.response else ""
        code = e.response.status_code if e.response else "?"
        log(f"[Mastodon] HTTP {code}: {body}")
        hint = ""
        if e.response and e.response.status_code == 401:
            hint = " | Hinweis: Access Token ungültig oder abgelaufen."
        elif e.response and e.response.status_code == 403:
            hint = " | Hinweis: Token hat keine write:statuses-Berechtigung."
        return {"success": False, "error": f"Mastodon API {code}: {body}{hint}"}
    except requests.ConnectionError:
        return {"success": False, "error": f"Verbindung zu {api_base_url} fehlgeschlagen. Instanz-URL prüfen."}
    except Exception as e:
        log(f"[Mastodon] Fehler: {e}")
        return {"success": False, "error": f"Fehler: {str(e)}"}
