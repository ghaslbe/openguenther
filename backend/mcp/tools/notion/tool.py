"""
Notion MCP Tool

Ermoeglicht Seiten lesen/erstellen, Datenbanken abfragen und Eintraege anlegen.

Einstellungen (Einstellungen -> MCP Tools -> notion):
  - api_key : Notion Integration Token (integration.token von notion.so/my-integrations)
"""

import requests

from config import get_tool_settings
from services.tool_context import get_emit_log

NOTION_BASE = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"

SETTINGS_INFO = """**Notion**

Lese und schreibe Seiten und Datenbanken in Notion.

**Integration Token:** Unter [notion.so/my-integrations](https://www.notion.so/my-integrations) eine neue Integration erstellen → Token kopieren (beginnt mit `secret_`).

**Wichtig:** Die Integration muss in jeder Notion-Seite/Datenbank explizit eingeladen werden (Seite oeffnen → Drei Punkte → Verbindungen → Integration hinzufuegen)."""

SETTINGS_SCHEMA = [
    {
        "key": "api_key",
        "label": "Notion Integration Token",
        "type": "password",
        "placeholder": "secret_xxxxxxxxxxxxxxxxxxxxxxxxxxxx",
        "description": "Integration Token aus notion.so/my-integrations",
    },
]

TOOL_DEFINITION = {
    "name": "notion",
    "description": (
        "Notion: Seiten und Datenbanken lesen, erstellen und bearbeiten. "
        "Aktionen: search (Seiten/DBs suchen) | "
        "get_page (Seiteninhalt lesen) | "
        "create_page (neue Seite erstellen) | "
        "append_text (Text an Seite anhaengen) | "
        "query_database (Datenbank-Eintraege abfragen) | "
        "create_database_entry (neuen Eintrag in Datenbank anlegen)"
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": [
                    "search",
                    "get_page",
                    "create_page",
                    "append_text",
                    "query_database",
                    "create_database_entry",
                ],
                "description": (
                    "Aktion: "
                    "search (Seiten und DBs nach Begriff suchen) | "
                    "get_page (Inhalt einer Seite per page_id lesen) | "
                    "create_page (neue Unterseite in parent_id erstellen) | "
                    "append_text (Text-Block an Seite anhaengen per page_id + text) | "
                    "query_database (Eintraege einer Datenbank per database_id abfragen) | "
                    "create_database_entry (neuen Eintrag in Datenbank per database_id anlegen)"
                ),
            },
            "query": {
                "type": "string",
                "description": "Suchbegriff fuer 'search'",
            },
            "page_id": {
                "type": "string",
                "description": "Notion Seiten-ID (aus der URL oder search)",
            },
            "database_id": {
                "type": "string",
                "description": "Notion Datenbank-ID (aus der URL oder search)",
            },
            "parent_id": {
                "type": "string",
                "description": "Eltern-Seiten-ID fuer 'create_page' (die Seite unter der die neue angelegt wird)",
            },
            "title": {
                "type": "string",
                "description": "Titel der neuen Seite oder des neuen Datenbankeintrags",
            },
            "text": {
                "type": "string",
                "description": "Text fuer 'append_text' oder als Inhalt bei 'create_page'",
            },
            "properties": {
                "type": "object",
                "description": (
                    "Eigenschaften fuer 'create_database_entry' als Objekt im Notion-Format. "
                    'Beispiel fuer Titel-Feld: {"Name": {"title": [{"text": {"content": "Mein Eintrag"}}]}} '
                    'Fuer Text: {"Status": {"rich_text": [{"text": {"content": "aktiv"}}]}} '
                    'Fuer Datum: {"Datum": {"date": {"start": "2025-04-01"}}}'
                ),
            },
            "filter": {
                "type": "object",
                "description": (
                    "Filter fuer 'query_database' im Notion-Format. "
                    'Beispiel: {"property": "Status", "select": {"equals": "Aktiv"}}'
                ),
            },
            "limit": {
                "type": "integer",
                "description": "Maximale Anzahl Ergebnisse (Standard: 20)",
            },
        },
        "required": ["action"],
    },
}


def _cfg():
    return get_tool_settings("notion")


def _headers(api_key):
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Notion-Version": NOTION_VERSION,
    }


def _extract_text(rich_text_list):
    return "".join(t.get("plain_text", "") for t in (rich_text_list or []))


def _extract_page_title(page):
    props = page.get("properties", {})
    for prop in props.values():
        if prop.get("type") == "title":
            return _extract_text(prop.get("title", []))
    title = page.get("properties", {}).get("title", {})
    return _extract_text(title.get("title", [])) if title else page.get("id", "?")


def handler(
    action,
    query=None,
    page_id=None,
    database_id=None,
    parent_id=None,
    title=None,
    text=None,
    properties=None,
    filter=None,
    limit=20,
):
    emit_log = get_emit_log()

    def log(msg):
        if emit_log:
            emit_log({"type": "text", "message": f"[Notion] {msg}"})

    def header(msg):
        if emit_log:
            emit_log({"type": "header", "message": msg})

    cfg = _cfg()
    api_key = cfg.get("api_key", "").strip()
    if not api_key:
        return {"error": "Kein Notion Token konfiguriert. Bitte in Einstellungen -> MCP Tools -> notion eintragen."}

    hdrs = _headers(api_key)
    cap = min(int(limit or 20), 100)

    try:

        # ── search ─────────────────────────────────────────────────────────
        if action == "search":
            header("NOTION SEARCH")
            payload = {"page_size": cap}
            if query:
                payload["query"] = query
            r = requests.post(f"{NOTION_BASE}/search", headers=hdrs, json=payload, timeout=15)
            r.raise_for_status()
            results = r.json().get("results", [])
            log(f"{len(results)} Ergebnis(se)")
            items = []
            for res in results:
                obj_type = res.get("object")
                item = {"id": res["id"], "type": obj_type}
                if obj_type == "page":
                    item["title"] = _extract_page_title(res)
                    item["url"] = res.get("url", "")
                elif obj_type == "database":
                    item["title"] = _extract_text(res.get("title", []))
                    item["url"] = res.get("url", "")
                items.append(item)
            return {"count": len(items), "results": items}

        # ── get_page ───────────────────────────────────────────────────────
        elif action == "get_page":
            if not page_id:
                return {"error": "page_id erforderlich fuer get_page"}
            pid = page_id.replace("-", "")
            header(f"NOTION GET PAGE: {pid}")
            # Seiten-Metadaten
            r = requests.get(f"{NOTION_BASE}/pages/{pid}", headers=hdrs, timeout=15)
            r.raise_for_status()
            page = r.json()
            page_title = _extract_page_title(page)
            # Block-Inhalt
            r2 = requests.get(f"{NOTION_BASE}/blocks/{pid}/children", headers=hdrs, params={"page_size": 100}, timeout=15)
            r2.raise_for_status()
            blocks = r2.json().get("results", [])
            content_parts = []
            for block in blocks:
                btype = block.get("type", "")
                bdata = block.get(btype, {})
                rich = bdata.get("rich_text", [])
                if rich:
                    content_parts.append(_extract_text(rich))
            log(f"Seite: {page_title} ({len(blocks)} Bloecke)")
            return {
                "id": pid,
                "title": page_title,
                "url": page.get("url", ""),
                "content": "\n".join(content_parts),
                "block_count": len(blocks),
            }

        # ── create_page ────────────────────────────────────────────────────
        elif action == "create_page":
            if not parent_id:
                return {"error": "parent_id erforderlich fuer create_page"}
            if not title:
                return {"error": "title erforderlich fuer create_page"}
            header(f"NOTION CREATE PAGE: {title}")
            pid = parent_id.replace("-", "")
            payload = {
                "parent": {"page_id": pid},
                "properties": {
                    "title": {"title": [{"text": {"content": title}}]}
                },
            }
            if text:
                payload["children"] = [
                    {
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {"rich_text": [{"type": "text", "text": {"content": text}}]},
                    }
                ]
            r = requests.post(f"{NOTION_BASE}/pages", headers=hdrs, json=payload, timeout=15)
            r.raise_for_status()
            page = r.json()
            log(f"Seite erstellt: {page['id']}")
            return {"success": True, "id": page["id"], "url": page.get("url", ""), "title": title}

        # ── append_text ────────────────────────────────────────────────────
        elif action == "append_text":
            if not page_id:
                return {"error": "page_id erforderlich fuer append_text"}
            if not text:
                return {"error": "text erforderlich fuer append_text"}
            pid = page_id.replace("-", "")
            header(f"NOTION APPEND: {pid}")
            paragraphs = [p for p in text.split("\n") if p.strip()]
            children = [
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {"rich_text": [{"type": "text", "text": {"content": p}}]},
                }
                for p in paragraphs
            ]
            r = requests.patch(f"{NOTION_BASE}/blocks/{pid}/children", headers=hdrs, json={"children": children}, timeout=15)
            r.raise_for_status()
            log(f"{len(children)} Block(e) angehaengt")
            return {"success": True, "appended_blocks": len(children)}

        # ── query_database ─────────────────────────────────────────────────
        elif action == "query_database":
            if not database_id:
                return {"error": "database_id erforderlich fuer query_database"}
            did = database_id.replace("-", "")
            header(f"NOTION QUERY DB: {did}")
            payload = {"page_size": cap}
            if filter:
                payload["filter"] = filter
            r = requests.post(f"{NOTION_BASE}/databases/{did}/query", headers=hdrs, json=payload, timeout=15)
            r.raise_for_status()
            results = r.json().get("results", [])
            log(f"{len(results)} Eintrag/Eintraege")
            entries = []
            for res in results:
                entry = {"id": res["id"], "url": res.get("url", ""), "properties": {}}
                for pname, pval in res.get("properties", {}).items():
                    ptype = pval.get("type")
                    if ptype == "title":
                        entry["properties"][pname] = _extract_text(pval.get("title", []))
                    elif ptype == "rich_text":
                        entry["properties"][pname] = _extract_text(pval.get("rich_text", []))
                    elif ptype == "select":
                        sel = pval.get("select")
                        entry["properties"][pname] = sel.get("name") if sel else None
                    elif ptype == "multi_select":
                        entry["properties"][pname] = [s.get("name") for s in pval.get("multi_select", [])]
                    elif ptype == "number":
                        entry["properties"][pname] = pval.get("number")
                    elif ptype == "checkbox":
                        entry["properties"][pname] = pval.get("checkbox")
                    elif ptype == "date":
                        d = pval.get("date")
                        entry["properties"][pname] = d.get("start") if d else None
                    elif ptype == "url":
                        entry["properties"][pname] = pval.get("url")
                    elif ptype == "email":
                        entry["properties"][pname] = pval.get("email")
                    elif ptype == "phone_number":
                        entry["properties"][pname] = pval.get("phone_number")
                    else:
                        entry["properties"][pname] = f"({ptype})"
                entries.append(entry)
            return {"count": len(entries), "entries": entries}

        # ── create_database_entry ──────────────────────────────────────────
        elif action == "create_database_entry":
            if not database_id:
                return {"error": "database_id erforderlich fuer create_database_entry"}
            did = database_id.replace("-", "")
            header(f"NOTION CREATE ENTRY: {did}")
            props = properties or {}
            if title and not any(
                v.get("type") == "title" or "title" in v
                for v in props.values()
            ):
                # Automatisch Titel setzen wenn nicht in properties
                props = {"Name": {"title": [{"text": {"content": title}}]}, **props}
            payload = {"parent": {"database_id": did}, "properties": props}
            r = requests.post(f"{NOTION_BASE}/pages", headers=hdrs, json=payload, timeout=15)
            r.raise_for_status()
            page = r.json()
            log(f"Eintrag erstellt: {page['id']}")
            return {"success": True, "id": page["id"], "url": page.get("url", "")}

        else:
            return {"error": f"Unbekannte Aktion: '{action}'."}

    except requests.HTTPError as e:
        try:
            detail = e.response.json()
        except Exception:
            detail = e.response.text[:300]
        log(f"HTTP {e.response.status_code}: {detail}")
        return {"error": f"Notion API Fehler ({e.response.status_code}): {detail}"}
    except Exception as e:
        log(f"Fehler: {e}")
        return {"error": str(e)}
