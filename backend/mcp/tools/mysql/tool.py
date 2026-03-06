"""
MySQL MCP Tool

Ermoeglicht Verbindung zu einer MySQL/MariaDB-Datenbank: Abfragen, Schreiben, Tabellen auflisten.

Einstellungen (Einstellungen -> MCP Tools -> mysql):
  - host     : Hostname oder IP (z.B. localhost, 192.168.1.10)
  - port     : Port (Standard: 3306)
  - database : Datenbankname
  - user     : Benutzername
  - password : Passwort
"""

from config import get_tool_settings
from services.tool_context import get_emit_log

SETTINGS_INFO = """**MySQL / MariaDB**

Verbindet sich mit einer MySQL- oder MariaDB-Datenbank und fuehrt Abfragen aus.

**Benoetigt:** `PyMySQL` (wird automatisch mit installiert).

**Sicherheit:** Verwende einen Datenbankbenutzer mit minimalen Rechten (nur SELECT fuer Lesezugriff,
zusaetzlich INSERT/UPDATE/DELETE wenn Schreibzugriff gewuenscht). Vergib niemals root-Zugangsdaten."""

SETTINGS_SCHEMA = [
    {
        "key": "host",
        "label": "Host",
        "type": "text",
        "placeholder": "localhost",
        "description": "Hostname oder IP-Adresse des MySQL-Servers",
    },
    {
        "key": "port",
        "label": "Port",
        "type": "text",
        "placeholder": "3306",
        "description": "MySQL-Port (Standard: 3306)",
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
        "placeholder": "mysql_user",
        "description": "MySQL-Benutzername",
    },
    {
        "key": "password",
        "label": "Passwort",
        "type": "password",
        "placeholder": "",
        "description": "MySQL-Passwort",
    },
]

TOOL_DEFINITION = {
    "name": "mysql",
    "description": (
        "MySQL/MariaDB-Datenbank: Abfragen ausfuehren, Daten lesen und schreiben. "
        "Aktionen: query (SELECT-Abfrage ausfuehren) | "
        "execute (INSERT/UPDATE/DELETE/DDL ausfuehren) | "
        "list_tables (alle Tabellen auflisten) | "
        "describe_table (Struktur/Spalten einer Tabelle anzeigen) | "
        "count_rows (Anzahl Zeilen zaehlen)"
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
                    "list_tables (alle Tabellen der konfigurierten DB) | "
                    "describe_table (Spalten, Typen, Keys einer Tabelle) | "
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
    return get_tool_settings("mysql")


def _connect(cfg):
    try:
        import pymysql
        import pymysql.cursors
    except ImportError:
        raise ImportError(
            "PyMySQL ist nicht installiert. "
            "Bitte 'PyMySQL' in requirements.txt eintragen und Image neu bauen."
        )

    host = cfg.get("host", "").strip() or "localhost"
    port = int(cfg.get("port", "3306") or 3306)
    database = cfg.get("database", "").strip()
    user = cfg.get("user", "").strip()
    password = cfg.get("password", "")

    if not database:
        raise ValueError("Keine Datenbank konfiguriert. Bitte in Einstellungen -> MCP Tools -> mysql eintragen.")
    if not user:
        raise ValueError("Kein Benutzername konfiguriert. Bitte in Einstellungen -> MCP Tools -> mysql eintragen.")

    conn = pymysql.connect(
        host=host,
        port=port,
        database=database,
        user=user,
        password=password,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        connect_timeout=10,
        autocommit=True,
    )
    return conn


def handler(
    action,
    sql=None,
    table=None,
    where=None,
    limit=100,
):
    emit_log = get_emit_log()

    def log(msg):
        if emit_log:
            emit_log({"type": "text", "message": f"[MySQL] {msg}"})

    def header(msg):
        if emit_log:
            emit_log({"type": "header", "message": msg})

    cfg = _cfg()
    if not cfg.get("host") and not cfg.get("database"):
        return {
            "error": (
                "MySQL nicht konfiguriert. "
                "Bitte in Einstellungen -> MCP Tools -> mysql Host, Datenbank, Benutzer und Passwort eintragen."
            )
        }

    try:
        conn = _connect(cfg)
    except ImportError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Verbindung fehlgeschlagen: {str(e)}"}

    try:
        with conn.cursor() as cursor:

            # ── list_tables ────────────────────────────────────────────────
            if action == "list_tables":
                header(f"MYSQL TABLES: {cfg.get('database', '?')}")
                cursor.execute("SHOW TABLES")
                rows = cursor.fetchall()
                tables = [list(row.values())[0] for row in rows]
                log(f"{len(tables)} Tabelle(n) gefunden")
                return {
                    "database": cfg.get("database", ""),
                    "table_count": len(tables),
                    "tables": tables,
                }

            # ── describe_table ─────────────────────────────────────────────
            elif action == "describe_table":
                if not table:
                    return {"error": "table erforderlich fuer describe_table"}
                header(f"MYSQL DESCRIBE: {table}")
                cursor.execute(f"DESCRIBE `{table}`")
                columns = cursor.fetchall()
                log(f"{len(columns)} Spalte(n)")
                return {
                    "table": table,
                    "column_count": len(columns),
                    "columns": columns,
                }

            # ── count_rows ─────────────────────────────────────────────────
            elif action == "count_rows":
                if not table:
                    return {"error": "table erforderlich fuer count_rows"}
                header(f"MYSQL COUNT: {table}")
                if where:
                    cursor.execute(f"SELECT COUNT(*) AS cnt FROM `{table}` WHERE {where}")
                else:
                    cursor.execute(f"SELECT COUNT(*) AS cnt FROM `{table}`")
                row = cursor.fetchone()
                count = row["cnt"] if row else 0
                log(f"Anzahl Zeilen: {count}")
                return {
                    "table": table,
                    "count": count,
                    "filter": where or "(kein Filter)",
                }

            # ── query ──────────────────────────────────────────────────────
            elif action == "query":
                if not sql:
                    return {"error": "sql erforderlich fuer query"}
                header("MYSQL QUERY")
                log(f"SQL: {sql[:200]}")
                # Sicherheits-Check: nur lesende Statements
                sql_upper = sql.strip().upper()
                if not any(sql_upper.startswith(kw) for kw in ("SELECT", "SHOW", "EXPLAIN", "DESC")):
                    return {
                        "error": (
                            "Nur lesende Statements (SELECT, SHOW, EXPLAIN, DESC) erlaubt bei 'query'. "
                            "Fuer schreibende Operationen 'execute' verwenden."
                        )
                    }
                cap = min(int(limit or 100), _MAX_ROWS)
                # Limit anfuegen wenn noch keines da
                if "LIMIT" not in sql_upper:
                    sql = sql.rstrip("; \t\n") + f" LIMIT {cap}"

                cursor.execute(sql)
                rows = cursor.fetchall()
                log(f"{len(rows)} Zeile(n) zurueckgegeben")
                return {
                    "row_count": len(rows),
                    "rows": rows,
                }

            # ── execute ────────────────────────────────────────────────────
            elif action == "execute":
                if not sql:
                    return {"error": "sql erforderlich fuer execute"}
                header("MYSQL EXECUTE")
                log(f"SQL: {sql[:200]}")
                cursor.execute(sql)
                affected = cursor.rowcount
                last_id = cursor.lastrowid
                log(f"{affected} Zeile(n) betroffen, last_insert_id={last_id}")
                result = {
                    "success": True,
                    "affected_rows": affected,
                }
                if last_id:
                    result["last_insert_id"] = last_id
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
