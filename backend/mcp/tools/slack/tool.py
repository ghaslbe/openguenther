"""
Slack MCP Tool

Nachrichten senden, Channels lesen und Slack-Workspace verwalten.

Einstellungen (Einstellungen -> MCP Tools -> slack):
  - bot_token : Slack Bot Token (xoxb-...)
"""

import requests

from config import get_tool_settings
from services.tool_context import get_emit_log

SLACK_BASE = "https://slack.com/api"

SETTINGS_INFO = """**Slack**

Sende Nachrichten und lese Channels in Slack.

**Bot Token:** In der [Slack App-Verwaltung](https://api.slack.com/apps) eine neue App erstellen (oder vorhandene waehlen):
1. "OAuth & Permissions" → Bot Token Scopes hinzufuegen: `chat:write`, `channels:read`, `channels:history`, `users:read`
2. App im Workspace installieren → Bot User OAuth Token kopieren (beginnt mit `xoxb-`)
3. Bot in gewuenschte Channels einladen (`/invite @BotName`)"""

SETTINGS_SCHEMA = [
    {
        "key": "bot_token",
        "label": "Slack Bot Token",
        "type": "password",
        "placeholder": "xoxb-xxxxxxxxxxxx-xxxxxxxxxxxx-xxxxxxxxxxxxxxxxxxxxxxxx",
        "description": "Bot User OAuth Token aus api.slack.com/apps (beginnt mit xoxb-)",
    },
]

TOOL_DEFINITION = {
    "name": "slack",
    "description": (
        "Slack: Nachrichten senden und lesen, Channels verwalten. "
        "Aktionen: send_message (Nachricht in Channel senden) | "
        "get_channels (alle Channels auflisten) | "
        "get_messages (letzte Nachrichten eines Channels) | "
        "reply_to_thread (auf eine Nachricht antworten)"
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": [
                    "send_message",
                    "get_channels",
                    "get_messages",
                    "reply_to_thread",
                ],
                "description": (
                    "Aktion: "
                    "send_message (Nachricht in Channel per channel + message) | "
                    "get_channels (alle Channels des Workspaces auflisten) | "
                    "get_messages (letzte Nachrichten per channel, optional limit) | "
                    "reply_to_thread (Antwort auf Thread per channel + thread_ts + message)"
                ),
            },
            "channel": {
                "type": "string",
                "description": "Channel-Name (z.B. 'general') oder Channel-ID (z.B. 'C1234567890')",
            },
            "message": {
                "type": "string",
                "description": "Nachrichtentext (unterstuetzt Slack Markdown: *fett*, _kursiv_, `code`, ```codeblock```)",
            },
            "thread_ts": {
                "type": "string",
                "description": "Timestamp der Eltern-Nachricht fuer reply_to_thread (aus get_messages)",
            },
            "limit": {
                "type": "integer",
                "description": "Maximale Anzahl Nachrichten bei get_messages (Standard: 20)",
            },
        },
        "required": ["action"],
    },
}


def _cfg():
    return get_tool_settings("slack")


def _headers(token):
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }


def _api(method, path, token, **kwargs):
    r = requests.post(f"{SLACK_BASE}/{path}", headers=_headers(token), json=kwargs, timeout=15)
    r.raise_for_status()
    data = r.json()
    if not data.get("ok"):
        raise ValueError(f"Slack Fehler: {data.get('error', 'unknown')}")
    return data


def _resolve_channel(channel, token):
    """Gibt Channel-ID zurueck — akzeptiert Name oder ID."""
    if channel.startswith("C") and len(channel) > 8:
        return channel
    # Name → ID suchen
    r = requests.get(
        f"{SLACK_BASE}/conversations.list",
        headers=_headers(token),
        params={"limit": 1000, "types": "public_channel,private_channel"},
        timeout=15,
    )
    r.raise_for_status()
    data = r.json()
    name = channel.lstrip("#")
    for ch in data.get("channels", []):
        if ch.get("name") == name:
            return ch["id"]
    return channel  # Fallback: original zurueckgeben


def handler(
    action,
    channel=None,
    message=None,
    thread_ts=None,
    limit=20,
):
    emit_log = get_emit_log()

    def log(msg):
        if emit_log:
            emit_log({"type": "text", "message": f"[Slack] {msg}"})

    def header(msg):
        if emit_log:
            emit_log({"type": "header", "message": msg})

    cfg = _cfg()
    token = cfg.get("bot_token", "").strip()
    if not token:
        return {"error": "Kein Slack Bot Token konfiguriert. Bitte in Einstellungen -> MCP Tools -> slack eintragen."}

    try:

        # ── get_channels ───────────────────────────────────────────────────
        if action == "get_channels":
            header("SLACK CHANNELS")
            r = requests.get(
                f"{SLACK_BASE}/conversations.list",
                headers=_headers(token),
                params={"limit": 200, "types": "public_channel,private_channel"},
                timeout=15,
            )
            r.raise_for_status()
            data = r.json()
            if not data.get("ok"):
                return {"error": f"Slack Fehler: {data.get('error')}"}
            channels = data.get("channels", [])
            log(f"{len(channels)} Channel(s)")
            return {
                "count": len(channels),
                "channels": [
                    {
                        "id": c["id"],
                        "name": c["name"],
                        "is_private": c.get("is_private", False),
                        "num_members": c.get("num_members", 0),
                    }
                    for c in channels
                ],
            }

        # ── send_message ───────────────────────────────────────────────────
        elif action == "send_message":
            if not channel:
                return {"error": "channel erforderlich fuer send_message"}
            if not message:
                return {"error": "message erforderlich fuer send_message"}
            header(f"SLACK SEND: #{channel}")
            channel_id = _resolve_channel(channel, token)
            data = _api("post", "chat.postMessage", token, channel=channel_id, text=message)
            log(f"Nachricht gesendet (ts={data.get('ts')})")
            return {
                "success": True,
                "channel": channel,
                "ts": data.get("ts"),
                "message": message[:100],
            }

        # ── get_messages ───────────────────────────────────────────────────
        elif action == "get_messages":
            if not channel:
                return {"error": "channel erforderlich fuer get_messages"}
            header(f"SLACK MESSAGES: #{channel}")
            channel_id = _resolve_channel(channel, token)
            cap = min(int(limit or 20), 100)
            r = requests.get(
                f"{SLACK_BASE}/conversations.history",
                headers=_headers(token),
                params={"channel": channel_id, "limit": cap},
                timeout=15,
            )
            r.raise_for_status()
            data = r.json()
            if not data.get("ok"):
                return {"error": f"Slack Fehler: {data.get('error')}"}
            messages = data.get("messages", [])
            log(f"{len(messages)} Nachricht(en)")
            return {
                "channel": channel,
                "count": len(messages),
                "messages": [
                    {
                        "ts": m.get("ts"),
                        "user": m.get("user"),
                        "text": m.get("text", ""),
                        "reply_count": m.get("reply_count", 0),
                    }
                    for m in messages
                ],
            }

        # ── reply_to_thread ────────────────────────────────────────────────
        elif action == "reply_to_thread":
            if not channel:
                return {"error": "channel erforderlich fuer reply_to_thread"}
            if not thread_ts:
                return {"error": "thread_ts erforderlich fuer reply_to_thread"}
            if not message:
                return {"error": "message erforderlich fuer reply_to_thread"}
            header(f"SLACK REPLY: #{channel}")
            channel_id = _resolve_channel(channel, token)
            data = _api("post", "chat.postMessage", token, channel=channel_id, text=message, thread_ts=thread_ts)
            log("Antwort gesendet")
            return {"success": True, "channel": channel, "thread_ts": thread_ts, "ts": data.get("ts")}

        else:
            return {"error": f"Unbekannte Aktion: '{action}'."}

    except requests.HTTPError as e:
        return {"error": f"HTTP Fehler ({e.response.status_code}): {e.response.text[:200]}"}
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        log(f"Fehler: {e}")
        return {"error": str(e)}
