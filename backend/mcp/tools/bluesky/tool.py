import re
import requests
from datetime import datetime, timezone

from config import get_tool_settings
from services.tool_context import get_emit_log

SETTINGS_INFO = """**Beitrag posten via Bluesky (AT Protocol)**

Postet einen Beitrag auf Bluesky. Hashtags werden automatisch als klickbare Facets verlinkt.

**Voraussetzungen:**
1. Bluesky-Account anlegen auf [bsky.app](https://bsky.app)
2. **App-Passwort** erstellen: Einstellungen → Datenschutz und Sicherheit → App-Passwörter
   (kein normales Konto-Passwort verwenden!)
3. Handle (z.B. `deinname.bsky.social`) und App-Passwort hier eintragen

**Hinweis:** Bluesky blockiert keine Datacenter-IPs — kein Proxy nötig."""

SETTINGS_SCHEMA = [
    {
        "key": "username",
        "label": "Bluesky Handle",
        "type": "text",
        "placeholder": "deinname.bsky.social",
        "description": "Dein Bluesky-Handle (mit oder ohne @)"
    },
    {
        "key": "app_password",
        "label": "App-Passwort",
        "type": "password",
        "placeholder": "xxxx-xxxx-xxxx-xxxx",
        "description": "App-Passwort aus Einstellungen → Datenschutz → App-Passwörter"
    },
]

TOOL_DEFINITION = {
    "name": "post_bluesky",
    "description": (
        "Postet einen Beitrag auf Bluesky. "
        "Maximale Länge: 300 Zeichen. Hashtags werden automatisch verlinkt. "
        "Benötigt Bluesky Handle und App-Passwort in den Tool-Einstellungen."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "text": {
                "type": "string",
                "description": "Der Beitragstext (max. 300 Zeichen, Hashtags werden automatisch verlinkt)"
            }
        },
        "required": ["text"]
    }
}


def _create_hashtag_facets(text):
    facets = []
    for match in re.finditer(r'#\w+', text):
        tag = match.group()[1:]
        byte_start = len(text[:match.start()].encode('utf-8'))
        byte_end   = len(text[:match.end()].encode('utf-8'))
        facets.append({
            'index': {'byteStart': byte_start, 'byteEnd': byte_end},
            'features': [{'$type': 'app.bsky.richtext.facet#tag', 'tag': tag}]
        })
    return facets or None


def handler(text: str) -> dict:
    emit_log = get_emit_log()

    def log(msg):
        if emit_log:
            emit_log({"type": "text", "message": msg})

    # ── Eingabe-Validierung ────────────────────────────────────────────────────
    if not text or not text.strip():
        return {"success": False, "error": "Beitragstext darf nicht leer sein."}

    cfg = get_tool_settings("post_bluesky")

    username     = cfg.get("username", "").strip().lstrip("@")
    app_password = cfg.get("app_password", "").strip()

    missing = [label for label, val in [
        ("Bluesky Handle", username),
        ("App-Passwort",   app_password),
    ] if not val]
    if missing:
        return {
            "success": False,
            "error": (
                f"Fehlende Bluesky-Zugangsdaten: {', '.join(missing)}. "
                "Bitte in Einstellungen → Tools → post_bluesky eintragen."
            )
        }

    text = text.strip()
    if len(text) > 300:
        text = text[:297] + "..."
        log("[Bluesky] Beitrag auf 300 Zeichen gekürzt")

    # ── Authentifizierung ──────────────────────────────────────────────────────
    log(f"[Bluesky] Authentifiziere als @{username}...")
    try:
        auth_resp = requests.post(
            'https://bsky.social/xrpc/com.atproto.server.createSession',
            json={'identifier': username, 'password': app_password},
            timeout=15,
        )
        auth_resp.raise_for_status()
        jwt_token = auth_resp.json()['accessJwt']
    except requests.HTTPError as e:
        body = e.response.text if e.response else ""
        log(f"[Bluesky] Auth-Fehler {e.response.status_code}: {body}")
        hint = " | Hinweis: Prüfe Handle und App-Passwort." if e.response and e.response.status_code == 401 else ""
        return {"success": False, "error": f"Authentifizierung fehlgeschlagen: {body}{hint}"}
    except Exception as e:
        return {"success": False, "error": f"Verbindungsfehler bei Authentifizierung: {str(e)}"}

    # ── Beitrag posten ─────────────────────────────────────────────────────────
    log(f"[Bluesky] Poste Beitrag ({len(text)} Zeichen)...")

    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    post_data = {
        "$type": "app.bsky.feed.post",
        "text": text,
        "createdAt": now,
    }
    facets = _create_hashtag_facets(text)
    if facets:
        post_data['facets'] = facets
        log(f"[Bluesky] {len(facets)} Hashtag-Facet(s) erkannt")

    try:
        resp = requests.post(
            'https://bsky.social/xrpc/com.atproto.repo.createRecord',
            headers={'Authorization': f'Bearer {jwt_token}'},
            json={
                "repo":       username,
                "collection": "app.bsky.feed.post",
                "record":     post_data,
            },
            timeout=15,
        )
        resp.raise_for_status()
        result = resp.json()
        uri = result.get('uri', '')
        # uri format: at://did:plc:.../app.bsky.feed.post/<rkey>
        rkey = uri.split('/')[-1] if uri else ''
        post_url = f"https://bsky.app/profile/{username}/post/{rkey}" if rkey else None
        log(f"[Bluesky] Beitrag erfolgreich gepostet!")
        if post_url:
            log(f"[Bluesky] URL: {post_url}")
        return {
            "success": True,
            "uri": uri,
            "text": text,
            "url": post_url,
        }
    except requests.HTTPError as e:
        body = e.response.text if e.response else ""
        log(f"[Bluesky] Post-Fehler {e.response.status_code}: {body}")
        return {"success": False, "error": f"Bluesky API {e.response.status_code}: {body}"}
    except Exception as e:
        log(f"[Bluesky] Fehler: {e}")
        return {"success": False, "error": f"Fehler: {str(e)}"}
