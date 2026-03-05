import base64
import hashlib
import hmac
import json
import random
import string
import time
import urllib.error
import urllib.parse
import urllib.request

from config import get_tool_settings
from services.tool_context import get_emit_log

SETTINGS_INFO = """**Tweet posten via Twitter/X API v2**

Postet einen Tweet über die Twitter/X API mit OAuth 1.0a Authentifizierung.

**Voraussetzungen:**
1. [developer.twitter.com](https://developer.twitter.com) → Neues Projekt/App anlegen
2. App-Berechtigungen auf **Read and Write** setzen
3. Unter *Keys and Tokens* die vier Schlüssel kopieren:
   - **API Key** (Consumer Key)
   - **API Secret** (Consumer Secret)
   - **Access Token**
   - **Access Token Secret**

Alle vier Werte sind erforderlich. Der Account muss über den Access Token verifiziert sein."""

SETTINGS_SCHEMA = [
    {
        "key": "api_key",
        "label": "API Key (Consumer Key)",
        "type": "password",
        "placeholder": "NU6D9tc7s15cr3...",
        "description": "Twitter API Key aus dem Developer Portal"
    },
    {
        "key": "api_secret",
        "label": "API Secret (Consumer Secret)",
        "type": "password",
        "placeholder": "xrdEA3aG7GBSU...",
        "description": "Twitter API Secret Key"
    },
    {
        "key": "access_token",
        "label": "Access Token",
        "type": "password",
        "placeholder": "1307368632-...",
        "description": "Access Token für den postenden Account"
    },
    {
        "key": "access_token_secret",
        "label": "Access Token Secret",
        "type": "password",
        "placeholder": "o3u4zgv...",
        "description": "Access Token Secret"
    },
]

TOOL_DEFINITION = {
    "name": "post_tweet",
    "description": (
        "Postet einen Tweet auf Twitter/X. "
        "Maximale Länge: 280 Zeichen. "
        "Benötigt konfigurierte Twitter-API-Zugangsdaten in den Tool-Einstellungen."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "text": {
                "type": "string",
                "description": "Der Tweet-Text (max. 280 Zeichen)"
            }
        },
        "required": ["text"]
    }
}


def _generate_nonce():
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(32))


def handler(text: str) -> dict:
    emit_log = get_emit_log()

    def log(msg):
        if emit_log:
            emit_log({"type": "text", "message": msg})

    # ── Eingabe-Validierung ────────────────────────────────────────────────────
    if not text or not text.strip():
        return {"success": False, "error": "Tweet-Text darf nicht leer sein."}

    cfg = get_tool_settings("post_tweet")

    api_key            = cfg.get("api_key", "").strip()
    api_secret         = cfg.get("api_secret", "").strip()
    access_token       = cfg.get("access_token", "").strip()
    access_token_secret = cfg.get("access_token_secret", "").strip()

    missing = [label for label, val in [
        ("API Key",             api_key),
        ("API Secret",          api_secret),
        ("Access Token",        access_token),
        ("Access Token Secret", access_token_secret),
    ] if not val]
    if missing:
        return {
            "success": False,
            "error": (
                f"Fehlende Twitter-Zugangsdaten: {', '.join(missing)}. "
                "Bitte in Einstellungen → Tools → post_tweet eintragen."
            )
        }

    text = text.strip()
    if len(text) > 280:
        text = text[:277] + "..."
        log("[Twitter] Tweet auf 280 Zeichen gekürzt")

    url = "https://api.twitter.com/2/tweets"
    oauth_timestamp = str(int(time.time()))
    oauth_nonce = _generate_nonce()

    params = {
        "oauth_consumer_key":     api_key,
        "oauth_nonce":            oauth_nonce,
        "oauth_signature_method": "HMAC-SHA1",
        "oauth_timestamp":        oauth_timestamp,
        "oauth_token":            access_token,
        "oauth_version":          "1.0",
    }

    # Signatur-Basis: Keys NICHT extra encodieren (identisch zum Original)
    param_string = "&".join(
        f"{k}={urllib.parse.quote(str(v), safe='')}"
        for k, v in sorted(params.items())
    )
    base_string = "&".join([
        "POST",
        urllib.parse.quote(url, safe=""),
        urllib.parse.quote(param_string, safe=""),
    ])

    signing_key = "&".join([
        urllib.parse.quote(api_secret, safe=""),
        urllib.parse.quote(access_token_secret, safe=""),
    ])

    signature = base64.b64encode(
        hmac.new(
            signing_key.encode("utf-8"),
            base_string.encode("utf-8"),
            hashlib.sha1,
        ).digest()
    ).decode("utf-8")

    params["oauth_signature"] = signature
    auth_header = "OAuth " + ", ".join(
        f'{k}="{urllib.parse.quote(str(v), safe="")}"'
        for k, v in params.items()
    )

    log(f"[Twitter] Poste Tweet ({len(text)} Zeichen)...")
    log(f"[Twitter] Timestamp: {oauth_timestamp} | Nonce: {oauth_nonce[:8]}...")

    body = json.dumps({"text": text}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Authorization":  auth_header,
            "Content-Type":   "application/json",
            "User-Agent":     "OpenGuenther/1.0",
            "Content-Length": str(len(body)),
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            tweet_id = result.get("data", {}).get("id", "")
            log(f"[Twitter] Tweet erfolgreich gepostet! ID: {tweet_id}")
            return {
                "success": True,
                "tweet_id": tweet_id,
                "text": text,
                "url": f"https://x.com/i/web/status/{tweet_id}" if tweet_id else None,
            }
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace")
        log(f"[Twitter] HTTP {e.code} {e.reason}")
        log(f"[Twitter] Response: {error_body}")
        return {
            "success": False,
            "error": f"Twitter API Fehler {e.code} ({e.reason}): {error_body}"
        }
    except urllib.error.URLError as e:
        log(f"[Twitter] Verbindungsfehler: {e.reason}")
        return {"success": False, "error": f"Verbindungsfehler: {e.reason}"}
    except Exception as e:
        log(f"[Twitter] Unerwarteter Fehler: {e}")
        return {"success": False, "error": f"Fehler: {str(e)}"}
