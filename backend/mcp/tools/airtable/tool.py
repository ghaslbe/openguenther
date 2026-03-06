"""
Airtable MCP Tool

Ermoeglicht Datensaetze aus Airtable-Bases lesen, erstellen, aktualisieren und loeschen.

Einstellungen (Einstellungen -> MCP Tools -> airtable):
  - api_key : Airtable Personal Access Token (airtable.com/create/tokens)
"""

import requests

from config import get_tool_settings
from services.tool_context import get_emit_log

AIRTABLE_BASE = "https://api.airtable.com/v0"

SETTINGS_INFO = """**Airtable**

Lese und schreibe Datensaetze in Airtable-Bases.

**API Key:** Airtable Personal Access Token erstellen unter [airtable.com/create/tokens](https://airtable.com/create/tokens).
Scopes benoetigt: `data.records:read`, `data.records:write`, `schema.bases:read`.

**Base ID:** Steht in der Airtable-URL: `https://airtable.com/appXXXXXXXX/...` — der Teil `appXXXXXXXX` ist die Base ID.

**Tabellen-Name:** Exakter Name des Tabs/der Tabelle in der Base (gross-/kleinschreibungssensitiv)."""

SETTINGS_SCHEMA = [
    {
        "key": "api_key",
        "label": "Airtable API Key (Personal Access Token)",
        "type": "password",
        "placeholder": "patXXXXXXXXXXXXXX...",
        "description": "Personal Access Token aus airtable.com/create/tokens",
    },
]

TOOL_DEFINITION = {
    "name": "airtable",
    "description": (
        "Airtable: Datensaetze aus einer Airtable-Base lesen, erstellen, aktualisieren und loeschen. "
        "Aktionen: get_records (Datensaetze abrufen, filterbar) | "
        "create_record (neuen Datensatz anlegen) | "
        "update_record (Datensatz aktualisieren) | "
        "delete_record (Datensatz loeschen) | "
        "count_records (Anzahl zaehlen) | "
        "list_fields (verfuegbare Felder/Spalten auflisten)"
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": [
                    "get_records",
                    "create_record",
                    "update_record",
                    "delete_record",
                    "count_records",
                    "list_fields",
                ],
                "description": (
                    "Aktion: "
                    "get_records (Datensaetze abrufen) | "
                    "create_record (neuen Datensatz anlegen) | "
                    "update_record (Datensatz per ID aktualisieren) | "
                    "delete_record (Datensatz per ID loeschen) | "
                    "count_records (Anzahl der Datensaetze zaehlen) | "
                    "list_fields (Felder/Spalten der Tabelle auflisten)"
                ),
            },
            "base_id": {
                "type": "string",
                "description": "Airtable Base ID (z.B. 'appXXXXXXXXXXXXXX' — steht in der URL der Base)",
            },
            "table": {
                "type": "string",
                "description": "Name der Tabelle/des Tabs (z.B. 'Kontakte', 'Aufgaben')",
            },
            "record_id": {
                "type": "string",
                "description": "Datensatz-ID (z.B. 'recXXXXXXXXXXXXXX') — benoetigt fuer update_record und delete_record",
            },
            "fields": {
                "type": "object",
                "description": (
                    "Felder fuer create_record oder update_record als Objekt, z.B. "
                    '{"Name": "Max Mustermann", "Status": "aktiv", "Datum": "2025-03-01"}'
                ),
            },
            "filter_formula": {
                "type": "string",
                "description": (
                    "Airtable-Formel zum Filtern bei get_records, z.B. "
                    "\"AND({Status}='aktiv', {Land}='DE')\" oder "
                    "\"{Name}='Max'\" oder "
                    "\"IS_AFTER({Datum}, '2025-01-01')\""
                ),
            },
            "limit": {
                "type": "integer",
                "description": "Maximale Anzahl Datensaetze bei get_records (Standard: 100, max: 100 pro Seite)",
            },
            "sort_field": {
                "type": "string",
                "description": "Feldname nach dem sortiert werden soll (bei get_records)",
            },
            "sort_direction": {
                "type": "string",
                "enum": ["asc", "desc"],
                "description": "Sortierrichtung: 'asc' (aufsteigend) oder 'desc' (absteigend)",
            },
        },
        "required": ["action", "base_id", "table"],
    },
}


def _cfg():
    return get_tool_settings("airtable")


def _headers(api_key):
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }


def handler(
    action,
    base_id,
    table,
    record_id=None,
    fields=None,
    filter_formula=None,
    limit=100,
    sort_field=None,
    sort_direction="asc",
):
    emit_log = get_emit_log()

    def log(msg):
        if emit_log:
            emit_log({"type": "text", "message": f"[Airtable] {msg}"})

    def header(msg):
        if emit_log:
            emit_log({"type": "header", "message": msg})

    cfg = _cfg()
    api_key = cfg.get("api_key", "").strip()
    if not api_key:
        return {
            "error": (
                "Kein Airtable API Key konfiguriert. "
                "Bitte in Einstellungen -> MCP Tools -> airtable eintragen."
            )
        }

    base_id = base_id.strip()
    table = table.strip()
    url_base = f"{AIRTABLE_BASE}/{base_id}/{table}"

    try:

        # ── get_records ────────────────────────────────────────────────────
        if action == "get_records":
            header(f"AIRTABLE GET: {table}")
            params = {"pageSize": min(int(limit or 100), 100)}
            if filter_formula:
                params["filterByFormula"] = filter_formula
            if sort_field:
                params["sort[0][field]"] = sort_field
                params["sort[0][direction]"] = sort_direction or "asc"

            r = requests.get(url_base, headers=_headers(api_key), params=params, timeout=30)
            r.raise_for_status()
            data = r.json()
            records = data.get("records", [])
            log(f"{len(records)} Datensatz/-saetze geladen")
            return {
                "count": len(records),
                "table": table,
                "records": [
                    {"id": rec["id"], "fields": rec.get("fields", {})}
                    for rec in records
                ],
            }

        # ── create_record ──────────────────────────────────────────────────
        elif action == "create_record":
            if not fields:
                return {"error": "fields erforderlich (Objekt mit Feldnamen und Werten)"}
            header(f"AIRTABLE CREATE: {table}")
            r = requests.post(
                url_base,
                headers=_headers(api_key),
                json={"fields": fields},
                timeout=30,
            )
            r.raise_for_status()
            rec = r.json()
            log(f"Datensatz erstellt: {rec.get('id')}")
            return {
                "success": True,
                "id": rec.get("id"),
                "fields": rec.get("fields", {}),
                "created_time": rec.get("createdTime"),
            }

        # ── update_record ──────────────────────────────────────────────────
        elif action == "update_record":
            if not record_id:
                return {"error": "record_id erforderlich fuer update_record"}
            if not fields:
                return {"error": "fields erforderlich (Objekt mit zu aendernden Feldern)"}
            header(f"AIRTABLE UPDATE: {table} / {record_id}")
            r = requests.patch(
                f"{url_base}/{record_id}",
                headers=_headers(api_key),
                json={"fields": fields},
                timeout=30,
            )
            r.raise_for_status()
            rec = r.json()
            log(f"Datensatz aktualisiert: {record_id}")
            return {
                "success": True,
                "id": rec.get("id"),
                "fields": rec.get("fields", {}),
            }

        # ── delete_record ──────────────────────────────────────────────────
        elif action == "delete_record":
            if not record_id:
                return {"error": "record_id erforderlich fuer delete_record"}
            header(f"AIRTABLE DELETE: {table} / {record_id}")
            r = requests.delete(
                f"{url_base}/{record_id}",
                headers=_headers(api_key),
                timeout=30,
            )
            r.raise_for_status()
            data = r.json()
            deleted = data.get("deleted", False)
            log(f"Datensatz {'geloescht' if deleted else 'nicht geloescht'}: {record_id}")
            return {
                "success": deleted,
                "deleted_id": record_id,
            }

        # ── count_records ──────────────────────────────────────────────────
        elif action == "count_records":
            header(f"AIRTABLE COUNT: {table}")
            params = {"fields[]": "_id_placeholder_"}  # minimale Daten laden
            if filter_formula:
                params["filterByFormula"] = filter_formula

            total = 0
            offset = None
            while True:
                p = {"pageSize": 100}
                if filter_formula:
                    p["filterByFormula"] = filter_formula
                if offset:
                    p["offset"] = offset
                r = requests.get(url_base, headers=_headers(api_key), params=p, timeout=30)
                r.raise_for_status()
                data = r.json()
                total += len(data.get("records", []))
                offset = data.get("offset")
                if not offset:
                    break

            log(f"Anzahl Datensaetze: {total}")
            return {
                "count": total,
                "table": table,
                "filter": filter_formula or "(kein Filter)",
            }

        # ── list_fields ────────────────────────────────────────────────────
        elif action == "list_fields":
            header(f"AIRTABLE FIELDS: {table}")
            # Einen Datensatz holen um Felder zu ermitteln
            r = requests.get(
                url_base,
                headers=_headers(api_key),
                params={"pageSize": 1},
                timeout=30,
            )
            r.raise_for_status()
            data = r.json()
            records = data.get("records", [])
            if not records:
                return {"fields": [], "note": "Tabelle ist leer — keine Felder erkennbar"}
            field_names = list(records[0].get("fields", {}).keys())
            log(f"{len(field_names)} Felder gefunden")
            return {
                "table": table,
                "field_count": len(field_names),
                "fields": field_names,
            }

        else:
            return {
                "error": (
                    f"Unbekannte Aktion: '{action}'. "
                    "Gueltige Aktionen: get_records, create_record, update_record, "
                    "delete_record, count_records, list_fields"
                )
            }

    except requests.HTTPError as e:
        try:
            detail = e.response.json()
        except Exception:
            detail = e.response.text[:500]
        log(f"HTTP {e.response.status_code}: {detail}")
        return {"error": f"Airtable API Fehler ({e.response.status_code}): {detail}"}
    except Exception as e:
        log(f"Fehler: {e}")
        return {"error": str(e)}
