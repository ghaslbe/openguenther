"""
Trello MCP Tool

Ermoeglicht Boards, Listen und Karten in Trello lesen, erstellen, aktualisieren und verschieben.

Einstellungen (Einstellungen -> MCP Tools -> trello):
  - api_key   : Trello API Key (trello.com/power-ups/admin)
  - api_token : Trello API Token
"""

import requests

from config import get_tool_settings
from services.tool_context import get_emit_log

TRELLO_BASE = "https://api.trello.com/1"

SETTINGS_INFO = """**Trello**

Lese und verwalte Boards, Listen und Karten in Trello.

**API Key + Token:** Auf [trello.com/power-ups/admin](https://trello.com/power-ups/admin) einen neuen Power-Up erstellen (oder vorhandenen waehlen) → API Key kopieren. Dann auf der gleichen Seite "Token generieren" → Token kopieren.

Alternativ direkt: `https://trello.com/1/authorize?expiration=never&scope=read,write&response_type=token&key=DEIN_API_KEY`

> ⚠️ **Achtung:** Dieses Tool kann Daten schreiben, bearbeiten oder loeschen. Fehlerhafte Eingaben koennen zu **Datenverlust oder ungewollten Aktionen** fuehren. Bitte mit Bedacht einsetzen."""

SETTINGS_SCHEMA = [
    {
        "key": "api_key",
        "label": "Trello API Key",
        "type": "password",
        "placeholder": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
        "description": "API Key aus trello.com/power-ups/admin",
    },
    {
        "key": "api_token",
        "label": "Trello API Token",
        "type": "password",
        "placeholder": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
        "description": "API Token (mit read+write Scope, am besten never expiring)",
    },
]

TOOL_DEFINITION = {
    "name": "trello",
    "description": (
        "Trello: Boards, Listen und Karten lesen und verwalten. "
        "Aktionen: get_boards (alle Boards auflisten) | "
        "get_lists (Listen eines Boards) | "
        "get_cards (Karten einer Liste oder eines Boards) | "
        "get_card (Details einer Karte) | "
        "create_card (neue Karte erstellen) | "
        "update_card (Karte umbenennen, beschreiben, verschieben, archivieren) | "
        "move_card (Karte in andere Liste verschieben) | "
        "create_list (neue Liste in einem Board erstellen) | "
        "add_comment (Kommentar zu einer Karte hinzufuegen) | "
        "archive_card (Karte archivieren)"
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": [
                    "get_boards",
                    "get_lists",
                    "get_cards",
                    "get_card",
                    "create_card",
                    "update_card",
                    "move_card",
                    "create_list",
                    "add_comment",
                    "archive_card",
                ],
                "description": (
                    "Aktion: "
                    "get_boards (alle Boards des Nutzers) | "
                    "get_lists (Listen eines Boards per board_id) | "
                    "get_cards (Karten einer Liste per list_id ODER eines Boards per board_id) | "
                    "get_card (Details + Checklisten einer Karte per card_id) | "
                    "create_card (neue Karte in einer Liste, benoetigt list_id + name) | "
                    "update_card (Name, Beschreibung, Faelligkeit aendern per card_id) | "
                    "move_card (Karte in andere Liste verschieben per card_id + list_id) | "
                    "create_list (neue Liste in Board per board_id + name) | "
                    "add_comment (Kommentar zu Karte per card_id + comment) | "
                    "archive_card (Karte archivieren per card_id)"
                ),
            },
            "board_id": {
                "type": "string",
                "description": "Trello Board ID (aus der Board-URL oder get_boards)",
            },
            "list_id": {
                "type": "string",
                "description": "Trello Listen-ID (aus get_lists)",
            },
            "card_id": {
                "type": "string",
                "description": "Trello Karten-ID (aus get_cards)",
            },
            "name": {
                "type": "string",
                "description": "Name der Karte oder Liste",
            },
            "description": {
                "type": "string",
                "description": "Beschreibung der Karte (Markdown unterstuetzt)",
            },
            "due": {
                "type": "string",
                "description": "Faelligkeitsdatum der Karte im Format ISO 8601, z.B. '2025-04-01T10:00:00.000Z'",
            },
            "comment": {
                "type": "string",
                "description": "Kommentartext fuer add_comment",
            },
            "label_color": {
                "type": "string",
                "description": "Label-Farbe fuer neue Karte: green, yellow, orange, red, purple, blue, sky, lime, pink, black",
            },
        },
        "required": ["action"],
    },
}


def _cfg():
    return get_tool_settings("trello")


def _auth(cfg):
    return {
        "key": cfg.get("api_key", "").strip(),
        "token": cfg.get("api_token", "").strip(),
    }


def _get(path, auth, **params):
    r = requests.get(f"{TRELLO_BASE}{path}", params={**auth, **params}, timeout=15)
    r.raise_for_status()
    return r.json()


def _post(path, auth, **data):
    r = requests.post(f"{TRELLO_BASE}{path}", params=auth, json=data, timeout=15)
    r.raise_for_status()
    return r.json()


def _put(path, auth, **data):
    r = requests.put(f"{TRELLO_BASE}{path}", params=auth, json=data, timeout=15)
    r.raise_for_status()
    return r.json()


def handler(
    action,
    board_id=None,
    list_id=None,
    card_id=None,
    name=None,
    description=None,
    due=None,
    comment=None,
    label_color=None,
):
    emit_log = get_emit_log()

    def log(msg):
        if emit_log:
            emit_log({"type": "text", "message": f"[Trello] {msg}"})

    def header(msg):
        if emit_log:
            emit_log({"type": "header", "message": msg})

    cfg = _cfg()
    auth = _auth(cfg)

    if not auth["key"] or not auth["token"]:
        return {
            "error": (
                "Trello API Key oder Token nicht konfiguriert. "
                "Bitte in Einstellungen -> MCP Tools -> trello eintragen."
            )
        }

    try:

        # ── get_boards ─────────────────────────────────────────────────────
        if action == "get_boards":
            header("TRELLO BOARDS")
            boards = _get("/members/me/boards", auth, fields="id,name,url,closed,shortUrl")
            active = [b for b in boards if not b.get("closed")]
            log(f"{len(active)} aktive Board(s) gefunden")
            return {
                "count": len(active),
                "boards": [
                    {"id": b["id"], "name": b["name"], "url": b.get("shortUrl", b.get("url", ""))}
                    for b in active
                ],
            }

        # ── get_lists ──────────────────────────────────────────────────────
        elif action == "get_lists":
            if not board_id:
                return {"error": "board_id erforderlich fuer get_lists"}
            header(f"TRELLO LISTS: {board_id}")
            lists = _get(f"/boards/{board_id}/lists", auth, filter="open", fields="id,name,pos")
            lists.sort(key=lambda l: l.get("pos", 0))
            log(f"{len(lists)} Liste(n) gefunden")
            return {
                "board_id": board_id,
                "count": len(lists),
                "lists": [{"id": l["id"], "name": l["name"]} for l in lists],
            }

        # ── get_cards ──────────────────────────────────────────────────────
        elif action == "get_cards":
            if list_id:
                header(f"TRELLO CARDS (Liste): {list_id}")
                cards = _get(f"/lists/{list_id}/cards", auth, fields="id,name,desc,due,url,labels,idList")
                source = f"liste {list_id}"
            elif board_id:
                header(f"TRELLO CARDS (Board): {board_id}")
                cards = _get(f"/boards/{board_id}/cards", auth, filter="open", fields="id,name,desc,due,url,labels,idList")
                source = f"board {board_id}"
            else:
                return {"error": "list_id oder board_id erforderlich fuer get_cards"}

            log(f"{len(cards)} Karte(n) aus {source}")
            return {
                "count": len(cards),
                "cards": [
                    {
                        "id": c["id"],
                        "name": c["name"],
                        "desc": c.get("desc", ""),
                        "due": c.get("due"),
                        "labels": [l.get("color") for l in c.get("labels", [])],
                        "url": c.get("url", ""),
                    }
                    for c in cards
                ],
            }

        # ── get_card ───────────────────────────────────────────────────────
        elif action == "get_card":
            if not card_id:
                return {"error": "card_id erforderlich fuer get_card"}
            header(f"TRELLO CARD: {card_id}")
            card = _get(f"/cards/{card_id}", auth, checklists="all", fields="id,name,desc,due,url,labels,idList,idBoard")
            checklists = [
                {
                    "name": cl["name"],
                    "items": [
                        {"name": item["name"], "done": item["state"] == "complete"}
                        for item in cl.get("checkItems", [])
                    ],
                }
                for cl in card.get("checklists", [])
            ]
            log(f"Karte: {card.get('name')}")
            return {
                "id": card["id"],
                "name": card["name"],
                "desc": card.get("desc", ""),
                "due": card.get("due"),
                "labels": [l.get("color") for l in card.get("labels", [])],
                "url": card.get("url", ""),
                "list_id": card.get("idList"),
                "board_id": card.get("idBoard"),
                "checklists": checklists,
            }

        # ── create_card ────────────────────────────────────────────────────
        elif action == "create_card":
            if not list_id:
                return {"error": "list_id erforderlich fuer create_card"}
            if not name:
                return {"error": "name erforderlich fuer create_card"}
            header(f"TRELLO CREATE CARD: {name}")
            data = {"idList": list_id, "name": name}
            if description:
                data["desc"] = description
            if due:
                data["due"] = due
            card = _post("/cards", auth, **data)
            log(f"Karte erstellt: {card.get('id')}")
            return {
                "success": True,
                "id": card["id"],
                "name": card["name"],
                "url": card.get("url", ""),
                "list_id": list_id,
            }

        # ── update_card ────────────────────────────────────────────────────
        elif action == "update_card":
            if not card_id:
                return {"error": "card_id erforderlich fuer update_card"}
            header(f"TRELLO UPDATE CARD: {card_id}")
            data = {}
            if name:
                data["name"] = name
            if description is not None:
                data["desc"] = description
            if due is not None:
                data["due"] = due
            if not data:
                return {"error": "Mindestens eines von name, description oder due angeben"}
            card = _put(f"/cards/{card_id}", auth, **data)
            log(f"Karte aktualisiert: {card.get('name')}")
            return {
                "success": True,
                "id": card["id"],
                "name": card["name"],
                "url": card.get("url", ""),
            }

        # ── move_card ──────────────────────────────────────────────────────
        elif action == "move_card":
            if not card_id:
                return {"error": "card_id erforderlich fuer move_card"}
            if not list_id:
                return {"error": "list_id (Ziel-Liste) erforderlich fuer move_card"}
            header(f"TRELLO MOVE CARD: {card_id} -> {list_id}")
            card = _put(f"/cards/{card_id}", auth, idList=list_id, pos="bottom")
            log(f"Karte '{card.get('name')}' verschoben")
            return {
                "success": True,
                "id": card["id"],
                "name": card["name"],
                "new_list_id": list_id,
            }

        # ── create_list ────────────────────────────────────────────────────
        elif action == "create_list":
            if not board_id:
                return {"error": "board_id erforderlich fuer create_list"}
            if not name:
                return {"error": "name erforderlich fuer create_list"}
            header(f"TRELLO CREATE LIST: {name}")
            lst = _post("/lists", auth, idBoard=board_id, name=name, pos="bottom")
            log(f"Liste erstellt: {lst.get('id')}")
            return {
                "success": True,
                "id": lst["id"],
                "name": lst["name"],
                "board_id": board_id,
            }

        # ── add_comment ────────────────────────────────────────────────────
        elif action == "add_comment":
            if not card_id:
                return {"error": "card_id erforderlich fuer add_comment"}
            if not comment:
                return {"error": "comment erforderlich fuer add_comment"}
            header(f"TRELLO COMMENT: {card_id}")
            result = _post(f"/cards/{card_id}/actions/comments", auth, text=comment)
            log("Kommentar hinzugefuegt")
            return {
                "success": True,
                "card_id": card_id,
                "comment_id": result.get("id"),
            }

        # ── archive_card ───────────────────────────────────────────────────
        elif action == "archive_card":
            if not card_id:
                return {"error": "card_id erforderlich fuer archive_card"}
            header(f"TRELLO ARCHIVE CARD: {card_id}")
            card = _put(f"/cards/{card_id}", auth, closed=True)
            log(f"Karte archiviert: {card.get('name')}")
            return {
                "success": True,
                "id": card["id"],
                "name": card["name"],
                "archived": True,
            }

        else:
            return {
                "error": (
                    f"Unbekannte Aktion: '{action}'. "
                    "Gueltige Aktionen: get_boards, get_lists, get_cards, get_card, "
                    "create_card, update_card, move_card, create_list, add_comment, archive_card"
                )
            }

    except requests.HTTPError as e:
        try:
            detail = e.response.text[:300]
        except Exception:
            detail = str(e)
        log(f"HTTP {e.response.status_code}: {detail}")
        return {"error": f"Trello API Fehler ({e.response.status_code}): {detail}"}
    except Exception as e:
        log(f"Fehler: {e}")
        return {"error": str(e)}
