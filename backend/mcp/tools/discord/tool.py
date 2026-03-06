"""
Discord MCP Tool

Nachrichten per Webhook senden oder per Bot Token lesen/senden.

Einstellungen (Einstellungen -> MCP Tools -> discord):
  - webhook_url : Discord Webhook URL (fuer einfaches Senden, kein Bot noetig)
  - bot_token   : Discord Bot Token (fuer Lesen + erweiterte Funktionen)
"""

import requests

from config import get_tool_settings
from services.tool_context import get_emit_log

DISCORD_BASE = "https://discord.com/api/v10"

SETTINGS_INFO = """**Discord**

Sende Nachrichten per Webhook oder verwalte Channel per Bot.

**Option 1 — Webhook (nur Senden, einfach):**
Discord Server → Channel-Einstellungen → Integrationen → Webhooks → Neuer Webhook → URL kopieren.

**Option 2 — Bot Token (Lesen + Senden):**
1. [discord.com/developers/applications](https://discord.com/developers/applications) → Neue Anwendung
2. Bot → "Add Bot" → Token kopieren
3. OAuth2 → URL Generator: Scopes `bot`, Permissions `Send Messages`, `Read Message History`, `View Channels`
4. Generierten Link oeffnen → Bot zum Server einladen

Fuer einfaches Senden reicht der Webhook. Fuer `get_messages` und `get_channels` wird der Bot Token benoetigt."""

SETTINGS_SCHEMA = [
    {
        "key": "webhook_url",
        "label": "Webhook URL (optional, nur fuer send_webhook)",
        "type": "password",
        "placeholder": "https://discord.com/api/webhooks/...",
        "description": "Discord Webhook URL fuer einfaches Senden ohne Bot",
    },
    {
        "key": "bot_token",
        "label": "Bot Token (optional, fuer get_channels/get_messages)",
        "type": "password",
        "placeholder": "MTxxxxxxxxxxxxxxxxxxxxxxxx.xxxxxx.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
        "description": "Discord Bot Token aus discord.com/developers/applications",
    },
]

TOOL_DEFINITION = {
    "name": "discord",
    "description": (
        "Discord: Nachrichten senden und lesen. "
        "Aktionen: send_webhook (Nachricht per Webhook senden, kein Bot noetig) | "
        "send_message (Nachricht per Bot in Channel senden) | "
        "get_channels (Channels eines Servers auflisten) | "
        "get_messages (letzte Nachrichten eines Channels lesen)"
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": [
                    "send_webhook",
                    "send_message",
                    "get_channels",
                    "get_messages",
                ],
                "description": (
                    "Aktion: "
                    "send_webhook (Nachricht per Webhook URL senden — nur Webhook URL benoetigt) | "
                    "send_message (Nachricht per Bot in Channel senden — Bot Token + channel_id benoetigt) | "
                    "get_channels (Channels eines Servers — Bot Token + guild_id benoetigt) | "
                    "get_messages (Nachrichten lesen — Bot Token + channel_id benoetigt)"
                ),
            },
            "message": {
                "type": "string",
                "description": "Nachrichtentext",
            },
            "username": {
                "type": "string",
                "description": "Anzeigename fuer send_webhook (optional, ueberschreibt Webhook-Namen)",
            },
            "channel_id": {
                "type": "string",
                "description": "Discord Channel ID (Rechtsklick auf Channel → ID kopieren)",
            },
            "guild_id": {
                "type": "string",
                "description": "Discord Server/Guild ID (Rechtsklick auf Server → ID kopieren)",
            },
            "embed_title": {
                "type": "string",
                "description": "Titel fuer Discord Embed (optionale reichhaltige Nachricht)",
            },
            "embed_description": {
                "type": "string",
                "description": "Beschreibung fuer Discord Embed",
            },
            "embed_color": {
                "type": "integer",
                "description": "Farbe des Embeds als Dezimalzahl (z.B. 5814783 fuer Blau, 16711680 fuer Rot)",
            },
            "limit": {
                "type": "integer",
                "description": "Maximale Anzahl Nachrichten bei get_messages (Standard: 20, max: 100)",
            },
        },
        "required": ["action"],
    },
}


def _cfg():
    return get_tool_settings("discord")


def _bot_headers(token):
    return {
        "Authorization": f"Bot {token}",
        "Content-Type": "application/json",
    }


def handler(
    action,
    message=None,
    username=None,
    channel_id=None,
    guild_id=None,
    embed_title=None,
    embed_description=None,
    embed_color=None,
    limit=20,
):
    emit_log = get_emit_log()

    def log(msg):
        if emit_log:
            emit_log({"type": "text", "message": f"[Discord] {msg}"})

    def header(msg):
        if emit_log:
            emit_log({"type": "header", "message": msg})

    cfg = _cfg()
    webhook_url = cfg.get("webhook_url", "").strip()
    bot_token = cfg.get("bot_token", "").strip()

    try:

        # ── send_webhook ───────────────────────────────────────────────────
        if action == "send_webhook":
            if not webhook_url:
                return {"error": "Keine Webhook URL konfiguriert. Bitte in Einstellungen -> MCP Tools -> discord eintragen."}
            if not message and not embed_title:
                return {"error": "message oder embed_title erforderlich"}
            header("DISCORD WEBHOOK")
            payload = {}
            if message:
                payload["content"] = message
            if username:
                payload["username"] = username
            if embed_title or embed_description:
                embed = {}
                if embed_title:
                    embed["title"] = embed_title
                if embed_description:
                    embed["description"] = embed_description
                if embed_color is not None:
                    embed["color"] = int(embed_color)
                payload["embeds"] = [embed]
            r = requests.post(webhook_url, json=payload, timeout=15)
            r.raise_for_status()
            log("Webhook-Nachricht gesendet")
            return {"success": True, "method": "webhook"}

        # ── send_message ───────────────────────────────────────────────────
        elif action == "send_message":
            if not bot_token:
                return {"error": "Kein Bot Token konfiguriert. Bitte in Einstellungen -> MCP Tools -> discord eintragen."}
            if not channel_id:
                return {"error": "channel_id erforderlich fuer send_message"}
            if not message:
                return {"error": "message erforderlich fuer send_message"}
            header(f"DISCORD SEND: {channel_id}")
            payload = {"content": message}
            r = requests.post(
                f"{DISCORD_BASE}/channels/{channel_id}/messages",
                headers=_bot_headers(bot_token),
                json=payload,
                timeout=15,
            )
            r.raise_for_status()
            msg = r.json()
            log(f"Nachricht gesendet (id={msg.get('id')})")
            return {"success": True, "message_id": msg.get("id"), "channel_id": channel_id}

        # ── get_channels ───────────────────────────────────────────────────
        elif action == "get_channels":
            if not bot_token:
                return {"error": "Kein Bot Token konfiguriert. Bitte in Einstellungen -> MCP Tools -> discord eintragen."}
            if not guild_id:
                return {"error": "guild_id (Server-ID) erforderlich fuer get_channels"}
            header(f"DISCORD CHANNELS: {guild_id}")
            r = requests.get(
                f"{DISCORD_BASE}/guilds/{guild_id}/channels",
                headers=_bot_headers(bot_token),
                timeout=15,
            )
            r.raise_for_status()
            channels = r.json()
            # Typ 0 = Text-Channel, Typ 2 = Voice, Typ 4 = Kategorie
            text_channels = [c for c in channels if c.get("type") == 0]
            text_channels.sort(key=lambda c: c.get("position", 0))
            log(f"{len(text_channels)} Text-Channel(s)")
            return {
                "guild_id": guild_id,
                "count": len(text_channels),
                "channels": [{"id": c["id"], "name": c["name"]} for c in text_channels],
            }

        # ── get_messages ───────────────────────────────────────────────────
        elif action == "get_messages":
            if not bot_token:
                return {"error": "Kein Bot Token konfiguriert. Bitte in Einstellungen -> MCP Tools -> discord eintragen."}
            if not channel_id:
                return {"error": "channel_id erforderlich fuer get_messages"}
            header(f"DISCORD MESSAGES: {channel_id}")
            cap = min(int(limit or 20), 100)
            r = requests.get(
                f"{DISCORD_BASE}/channels/{channel_id}/messages",
                headers=_bot_headers(bot_token),
                params={"limit": cap},
                timeout=15,
            )
            r.raise_for_status()
            messages = r.json()
            log(f"{len(messages)} Nachricht(en)")
            return {
                "channel_id": channel_id,
                "count": len(messages),
                "messages": [
                    {
                        "id": m["id"],
                        "author": m.get("author", {}).get("username", "?"),
                        "content": m.get("content", ""),
                        "timestamp": m.get("timestamp"),
                    }
                    for m in messages
                ],
            }

        else:
            return {"error": f"Unbekannte Aktion: '{action}'."}

    except requests.HTTPError as e:
        try:
            detail = e.response.json()
        except Exception:
            detail = e.response.text[:200]
        log(f"HTTP {e.response.status_code}: {detail}")
        return {"error": f"Discord API Fehler ({e.response.status_code}): {detail}"}
    except Exception as e:
        log(f"Fehler: {e}")
        return {"error": str(e)}
