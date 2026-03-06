"""
PostgreSQL MCP Tool

Ermoeglicht Verbindung zu einer PostgreSQL-Datenbank: Abfragen, Schreiben, Tabellen auflisten.

Einstellungen (Einstellungen -> MCP Tools -> postgresql):
  - host     : Hostname oder IP (z.B. localhost, 192.168.1.10)
  - port     : Port (Standard: 5432)
  - database : Datenbankname
  - user     : Benutzername
  - password : Passwort
  - sslmode  : SSL-Modus (z.B. require, disable, prefer)
"""

from config import get_tool_settings
from services.tool_context import get_emit_log

SETTINGS_INFO = """**PostgreSQL**

Verbindet sich mit einer PostgreSQL-Datenbank und fuehrt Abfragen aus.

**Benoetigt:** `psycopg2-binary` (wird automatisch mit installiert).

**Sicherheit:** Verwende einen Datenbankbenutzer mit minimalen Rechten (nur SELECT fuer Lesezugriff,
zusaetzlich INSERT/UPDATE/DELETE wenn Schreibzugriff gewuenscht). Vergib niemals superuser-Zugangsdaten.

**SSL:** Fuer Remote-Server `sslmode = require` empfohlen."""

SETTINGS_SCHEMA = [
    {
        "key": "host",
        "label": "Host",
        "type": "text",
        "placeholder": "localhost",
        "description": "Hostname oder IP-Adresse des PostgreSQL-Servers",
    },
    {
        "key": "port",
        "label": "Port",
        "type": "text",
        "placeholder": "5432",
        "description": "PostgreSQL-Port (Standard: 5432)",
    },
    {
        "key": "database",
        "label": "Datenbank",
        "type": "text",
        "placeholder": "meine_datenbank",
        "description": "Name der Datenbank",
    },
    {
        "key": "user",
        "label": "Benutzername",
        "type": "text",
        "placeholder": "pg_user",
        "description": "PostgreSQL-Benutzername",
    },
    {
        "key": "password",
        "label": "Passwort",
        "type": "password",
        "placeholder": "",
        "description": "PostgreSQL-Passwort",
    },
    {
        "key": "sslmode",
        "label": "SSL-Modus",
        "type": "text",
        "placeholder": "prefer",
        "description": "SSL-Modus: disable, allow, prefer, require, verify-ca, verify-full (Standard: prefer)",
    },
]

TOOL_DEFINITION = {
    "name": "postgresql",
    "description": (
        "PostgreSQL-Datenbank: Abfragen ausfuehren, Daten lesen und schreiben. "
        "Aktionen: query (SELECT-Abfrage) | "
        "execute (INSERT/UPDATE/DELETE/DDL) | "
        "list_tables (alle Tabellen auflisten) | "
        "describe_table (Spalten und Typen anzeigen) | "
        "count_rows (Zeilen zaehlen)"
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": [
                    "query",
                    "execute",
                    "list_tables",
                    "describe_table",
                    "count_rows",
                ],
                "description": (
                    "Aktion: "
                    "query (SELECT-Statement, gibt Zeilen zurueck) | "
                    "execute (INSERT/UPDATE/DELETE/DDL, gibt betroffene Zeilen zurueck) | "
                    "list_tables (alle Tabellen des konfigurierten Schemas) | "
                    "describe_table (Spalten, Typen, Nullable einer Tabelle) | "
                    "count_rows (Anzahl Zeilen einer Tabelle, optional mit WHERE)"
                ),
            },
            "sql": {
                "type": "string",
                "description": (
                    "SQL-Statement fuer 'query' oder 'execute'. "
                    "Beispiele: "
                    "\"SELECT * FROM kontakte WHERE status = 'aktiv' LIMIT 10\" | "
                    "\"INSERT INTO aufgaben (name, datum) VALUES ('Test', '2025-03-01')\" | "
                    "\"UPDATE kontakte SET status = 'inaktiv' WHERE id = 42\""
                ),
            },
            "table": {
                "type": "string",
                "description": "Tabellenname fuer 'describe_table' und 'count_rows'",
            },
            "schema": {
                "type": "string",
                "description": "Schema-Name fuer 'list_tables' und 'describe_table' (Standard: public)",
            },
            "where": {
                "type": "string",
                "description": "Optionale WHERE-Bedingung fuer 'count_rows' (ohne das Wort WHERE), z.B. \"status = 'aktiv'\"",
            },
            "limit": {
                "type": "integer",
                "description": "Maximale Anzahl Ergebniszeilen bei 'query' (Standard: 100)",
            },
        },
        "required": ["action"],
    },
}

_MAX_ROWS = 500


def _cfg():
    return get_tool_settings("postgresql")


def _connect(cfg):
    try:
        import psycopg2
        import psycopg2.extras
    except ImportError:
        raise ImportError(
            "psycopg2-binary ist nicht installiert. "
            "Bitte 'psycopg2-binary' in requirements.txt eintragen und Image neu bauen."
        )

    host = cfg.get("host", "").strip() or "localhost"
    port = int(cfg.get("port", "5432") or 5432)
    database = cfg.get("database", "").strip()
    user = cfg.get("user", "").strip()
    password = cfg.get("password", "")
    sslmode = cfg.get("sslmode", "prefer").strip() or "prefer"

    if not database:
        raise ValueError("Keine Datenbank konfiguriert. Bitte in Einstellungen -> MCP Tools -> postgresql eintragen.")
    if not user:
        raise ValueError("Kein Benutzername konfiguriert. Bitte in Einstellungen -> MCP Tools -> postgresql eintragen.")

    conn = psycopg2.connect(
        host=host,
        port=port,
        dbname=database,
        user=user,
        password=password,
        sslmode=sslmode,
        connect_timeout=10,
    )
    conn.autocommit = True
    return conn


def handler(
    action,
    sql=None,
    table=None,
    schema="public",
    where=None,
    limit=100,
):
    emit_log = get_emit_log()

    def log(msg):
        if emit_log:
            emit_log({"type": "text", "message": f"[PostgreSQL] {msg}"})

    def header(msg):
        if emit_log:
            emit_log({"type": "header", "message": msg})

    cfg = _cfg()
    if not cfg.get("host") and not cfg.get("database"):
        return {
            "error": (
                "PostgreSQL nicht konfiguriert. "
                "Bitte in Einstellungen -> MCP Tools -> postgresql Host, Datenbank, Benutzer und Passwort eintragen."
            )
        }

    try:
        conn = _connect(cfg)
    except ImportError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Verbindung fehlgeschlagen: {str(e)}"}

    schema = schema or "public"

    try:
        import psycopg2.extras
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:

            # ── list_tables ────────────────────────────────────────────────
            if action == "list_tables":
                header(f"POSTGRESQL TABLES: {cfg.get('database', '?')} / {schema}")
                cursor.execute(
                    """
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = %s
                      AND table_type = 'BASE TABLE'
                    ORDER BY table_name
                    """,
                    (schema,),
                )
                rows = cursor.fetchall()
                tables = [row["table_name"] for row in rows]
                log(f"{len(tables)} Tabelle(n) in Schema '{schema}' gefunden")
                return {
                    "database": cfg.get("database", ""),
                    "schema": schema,
                    "table_count": len(tables),
                    "tables": tables,
                }

            # ── describe_table ─────────────────────────────────────────────
            elif action == "describe_table":
                if not table:
                    return {"error": "table erforderlich fuer describe_table"}
                header(f"POSTGRESQL DESCRIBE: {schema}.{table}")
                cursor.execute(
                    """
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns
                    WHERE table_schema = %s AND table_name = %s
                    ORDER BY ordinal_position
                    """,
                    (schema, table),
                )
                columns = [dict(row) for row in cursor.fetchall()]
                log(f"{len(columns)} Spalte(n)")
                return {
                    "table": f"{schema}.{table}",
                    "column_count": len(columns),
                    "columns": columns,
                }

            # ── count_rows ─────────────────────────────────────────────────
            elif action == "count_rows":
                if not table:
                    return {"error": "table erforderlich fuer count_rows"}
                header(f"POSTGRESQL COUNT: {schema}.{table}")
                qualified = f'"{schema}"."{table}"'
                if where:
                    cursor.execute(f"SELECT COUNT(*) AS cnt FROM {qualified} WHERE {where}")
                else:
                    cursor.execute(f"SELECT COUNT(*) AS cnt FROM {qualified}")
                row = cursor.fetchone()
                count = row["cnt"] if row else 0
                log(f"Anzahl Zeilen: {count}")
                return {
                    "table": f"{schema}.{table}",
                    "count": count,
                    "filter": where or "(kein Filter)",
                }

            # ── query ──────────────────────────────────────────────────────
            elif action == "query":
                if not sql:
                    return {"error": "sql erforderlich fuer query"}
                header("POSTGRESQL QUERY")
                log(f"SQL: {sql[:200]}")
                sql_upper = sql.strip().upper()
                if not any(sql_upper.startswith(kw) for kw in ("SELECT", "SHOW", "EXPLAIN", "WITH", "TABLE")):
                    return {
                        "error": (
                            "Nur lesende Statements (SELECT, SHOW, EXPLAIN, WITH, TABLE) erlaubt bei 'query'. "
                            "Fuer schreibende Operationen 'execute' verwenden."
                        )
                    }
                cap = min(int(limit or 100), _MAX_ROWS)
                if "LIMIT" not in sql_upper:
                    sql = sql.rstrip("; \t\n") + f" LIMIT {cap}"

                cursor.execute(sql)
                rows = [dict(row) for row in cursor.fetchall()]
                log(f"{len(rows)} Zeile(n) zurueckgegeben")
                return {
                    "row_count": len(rows),
                    "rows": rows,
                }

            # ── execute ────────────────────────────────────────────────────
            elif action == "execute":
                if not sql:
                    return {"error": "sql erforderlich fuer execute"}
                header("POSTGRESQL EXECUTE")
                log(f"SQL: {sql[:200]}")
                cursor.execute(sql)
                affected = cursor.rowcount
                log(f"{affected} Zeile(n) betroffen")
                result = {
                    "success": True,
                    "affected_rows": affected,
                }
                return result

            else:
                return {
                    "error": (
                        f"Unbekannte Aktion: '{action}'. "
                        "Gueltige Aktionen: query, execute, list_tables, describe_table, count_rows"
                    )
                }

    except Exception as e:
        log(f"Fehler: {e}")
        return {"error": str(e)}
    finally:
        conn.close()
