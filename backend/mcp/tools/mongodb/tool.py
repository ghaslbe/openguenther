"""
MongoDB MCP Tool

Ermoeglicht Verbindung zu einer MongoDB-Datenbank: Dokumente suchen, einfuegen, aktualisieren, loeschen.

Einstellungen (Einstellungen -> MCP Tools -> mongodb):
  - connection_string : MongoDB Connection String (mongodb://... oder mongodb+srv://...)
  - database          : Datenbankname
"""

import json

from config import get_tool_settings
from services.tool_context import get_emit_log

SETTINGS_INFO = """**MongoDB**

Verbindet sich mit einer MongoDB-Datenbank (lokal oder Atlas) und fuehrt Operationen aus.

**Connection String:** z.B. `mongodb://localhost:27017` oder `mongodb+srv://user:pass@cluster.mongodb.net/`

Fuer MongoDB Atlas den Connection String aus "Connect -> Drivers" kopieren.

**Benoetigt:** `pymongo` (wird automatisch mit installiert)."""

SETTINGS_SCHEMA = [
    {
        "key": "connection_string",
        "label": "Connection String",
        "type": "password",
        "placeholder": "mongodb://localhost:27017",
        "description": "MongoDB Connection String (mongodb:// oder mongodb+srv://)",
    },
    {
        "key": "database",
        "label": "Datenbank",
        "type": "text",
        "placeholder": "meine_datenbank",
        "description": "Name der Datenbank",
    },
]

TOOL_DEFINITION = {
    "name": "mongodb",
    "description": (
        "MongoDB: Dokumente in Collections suchen, einfuegen, aktualisieren und loeschen. "
        "Aktionen: find (Dokumente suchen) | "
        "insert (Dokument einfuegen) | "
        "update (Dokumente aktualisieren) | "
        "delete (Dokumente loeschen) | "
        "count (Anzahl zaehlen) | "
        "list_collections (alle Collections auflisten) | "
        "aggregate (Aggregation-Pipeline ausfuehren)"
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": [
                    "find",
                    "insert",
                    "update",
                    "delete",
                    "count",
                    "list_collections",
                    "aggregate",
                ],
                "description": (
                    "Aktion: "
                    "find (Dokumente suchen, optional mit Filter) | "
                    "insert (ein Dokument einfuegen) | "
                    "update (Dokumente aktualisieren, update_many=true fuer alle Treffer) | "
                    "delete (Dokumente loeschen, delete_many=true fuer alle Treffer) | "
                    "count (Anzahl Dokumente zaehlen, optional mit Filter) | "
                    "list_collections (alle Collections der DB auflisten) | "
                    "aggregate (Aggregation-Pipeline, z.B. fuer Gruppierung/Statistiken)"
                ),
            },
            "collection": {
                "type": "string",
                "description": "Name der Collection (Pflicht ausser bei list_collections)",
            },
            "filter": {
                "type": "object",
                "description": (
                    "MongoDB-Filter als JSON-Objekt fuer find, update, delete, count. "
                    'Beispiele: {"status": "aktiv"} | {"alter": {"$gte": 18}} | '
                    '{"name": {"$regex": "^Max"}} | {} (alle Dokumente)'
                ),
            },
            "document": {
                "type": "object",
                "description": "Dokument fuer 'insert' als JSON-Objekt, z.B. {\"name\": \"Max\", \"status\": \"aktiv\"}",
            },
            "update": {
                "type": "object",
                "description": (
                    "Update-Operation fuer 'update' als JSON-Objekt. "
                    'Beispiele: {"$set": {"status": "inaktiv"}} | {"$inc": {"zaehler": 1}} | '
                    '{"$push": {"tags": "neu"}}'
                ),
            },
            "update_many": {
                "type": "boolean",
                "description": "Bei 'update': true = alle Treffer aktualisieren, false = nur erster Treffer (Standard: false)",
            },
            "delete_many": {
                "type": "boolean",
                "description": "Bei 'delete': true = alle Treffer loeschen, false = nur erster Treffer (Standard: false)",
            },
            "pipeline": {
                "type": "array",
                "description": (
                    "Aggregation-Pipeline fuer 'aggregate' als JSON-Array. "
                    'Beispiel: [{"$match": {"status": "aktiv"}}, {"$group": {"_id": "$land", "anzahl": {"$sum": 1}}}]'
                ),
            },
            "limit": {
                "type": "integer",
                "description": "Maximale Anzahl Dokumente bei 'find' (Standard: 100)",
            },
            "sort": {
                "type": "object",
                "description": 'Sortierung fuer find als JSON-Objekt, z.B. {"datum": -1} (absteigend) oder {"name": 1} (aufsteigend)',
            },
            "projection": {
                "type": "object",
                "description": 'Felder ein-/ausblenden fuer find, z.B. {"name": 1, "email": 1, "_id": 0}',
            },
        },
        "required": ["action"],
    },
}

_MAX_DOCS = 500


def _cfg():
    return get_tool_settings("mongodb")


def _serialize(obj):
    """Konvertiert MongoDB-Objekte (ObjectId, datetime) zu JSON-serialisierbaren Typen."""
    if isinstance(obj, dict):
        return {k: _serialize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_serialize(v) for v in obj]
    # ObjectId, datetime und andere nicht-serialisierbare Typen -> str
    try:
        json.dumps(obj)
        return obj
    except (TypeError, ValueError):
        return str(obj)


def _connect(cfg):
    try:
        from pymongo import MongoClient
    except ImportError:
        raise ImportError(
            "pymongo ist nicht installiert. "
            "Bitte 'pymongo' in requirements.txt eintragen und Image neu bauen."
        )

    conn_str = cfg.get("connection_string", "").strip()
    database = cfg.get("database", "").strip()

    if not conn_str:
        raise ValueError("Kein Connection String konfiguriert. Bitte in Einstellungen -> MCP Tools -> mongodb eintragen.")
    if not database:
        raise ValueError("Keine Datenbank konfiguriert. Bitte in Einstellungen -> MCP Tools -> mongodb eintragen.")

    client = MongoClient(conn_str, serverSelectionTimeoutMS=10000)
    db = client[database]
    return client, db


def handler(
    action,
    collection=None,
    filter=None,
    document=None,
    update=None,
    update_many=False,
    delete_many=False,
    pipeline=None,
    limit=100,
    sort=None,
    projection=None,
):
    emit_log = get_emit_log()

    def log(msg):
        if emit_log:
            emit_log({"type": "text", "message": f"[MongoDB] {msg}"})

    def header(msg):
        if emit_log:
            emit_log({"type": "header", "message": msg})

    cfg = _cfg()
    if not cfg.get("connection_string") and not cfg.get("database"):
        return {
            "error": (
                "MongoDB nicht konfiguriert. "
                "Bitte in Einstellungen -> MCP Tools -> mongodb Connection String und Datenbank eintragen."
            )
        }

    try:
        client, db = _connect(cfg)
    except ImportError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Verbindung fehlgeschlagen: {str(e)}"}

    filter = filter or {}
    sort_list = list(sort.items()) if sort else None

    try:

        # ── list_collections ───────────────────────────────────────────────
        if action == "list_collections":
            header(f"MONGODB COLLECTIONS: {cfg.get('database', '?')}")
            names = db.list_collection_names()
            names.sort()
            log(f"{len(names)} Collection(s) gefunden")
            return {
                "database": cfg.get("database", ""),
                "collection_count": len(names),
                "collections": names,
            }

        # Alle weiteren Aktionen benoetigen eine Collection
        if not collection:
            return {"error": "collection erforderlich fuer diese Aktion"}

        coll = db[collection]

        # ── find ───────────────────────────────────────────────────────────
        if action == "find":
            header(f"MONGODB FIND: {collection}")
            log(f"Filter: {json.dumps(filter)[:200]}")
            cap = min(int(limit or 100), _MAX_DOCS)
            cursor = coll.find(filter, projection=projection or None)
            if sort_list:
                cursor = cursor.sort(sort_list)
            cursor = cursor.limit(cap)
            docs = [_serialize(doc) for doc in cursor]
            log(f"{len(docs)} Dokument(e) gefunden")
            return {
                "collection": collection,
                "count": len(docs),
                "documents": docs,
            }

        # ── insert ─────────────────────────────────────────────────────────
        elif action == "insert":
            if not document:
                return {"error": "document erforderlich fuer insert"}
            header(f"MONGODB INSERT: {collection}")
            result = coll.insert_one(document)
            inserted_id = str(result.inserted_id)
            log(f"Dokument eingefuegt: {inserted_id}")
            return {
                "success": True,
                "inserted_id": inserted_id,
                "collection": collection,
            }

        # ── update ─────────────────────────────────────────────────────────
        elif action == "update":
            if not update:
                return {"error": "update erforderlich fuer update (z.B. {\"$set\": {\"status\": \"aktiv\"}})"}
            header(f"MONGODB UPDATE: {collection}")
            log(f"Filter: {json.dumps(filter)[:200]}, Update: {json.dumps(update)[:200]}")
            if update_many:
                result = coll.update_many(filter, update)
            else:
                result = coll.update_one(filter, update)
            log(f"{result.modified_count} Dokument(e) aktualisiert (matched: {result.matched_count})")
            return {
                "success": True,
                "matched_count": result.matched_count,
                "modified_count": result.modified_count,
                "collection": collection,
            }

        # ── delete ─────────────────────────────────────────────────────────
        elif action == "delete":
            header(f"MONGODB DELETE: {collection}")
            log(f"Filter: {json.dumps(filter)[:200]}, many={delete_many}")
            if delete_many:
                result = coll.delete_many(filter)
            else:
                result = coll.delete_one(filter)
            log(f"{result.deleted_count} Dokument(e) geloescht")
            return {
                "success": True,
                "deleted_count": result.deleted_count,
                "collection": collection,
            }

        # ── count ──────────────────────────────────────────────────────────
        elif action == "count":
            header(f"MONGODB COUNT: {collection}")
            count = coll.count_documents(filter)
            log(f"Anzahl Dokumente: {count}")
            return {
                "collection": collection,
                "count": count,
                "filter": filter,
            }

        # ── aggregate ──────────────────────────────────────────────────────
        elif action == "aggregate":
            if not pipeline:
                return {"error": "pipeline erforderlich fuer aggregate (JSON-Array mit Stage-Objekten)"}
            header(f"MONGODB AGGREGATE: {collection}")
            log(f"Pipeline: {json.dumps(pipeline)[:300]}")
            results = [_serialize(doc) for doc in coll.aggregate(pipeline)]
            log(f"{len(results)} Ergebnis(se)")
            return {
                "collection": collection,
                "count": len(results),
                "results": results,
            }

        else:
            return {
                "error": (
                    f"Unbekannte Aktion: '{action}'. "
                    "Gueltige Aktionen: find, insert, update, delete, count, list_collections, aggregate"
                )
            }

    except Exception as e:
        log(f"Fehler: {e}")
        return {"error": str(e)}
    finally:
        client.close()
