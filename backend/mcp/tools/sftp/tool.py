"""
SFTP/FTP MCP Tool

Dateien auf SFTP- oder FTP-Servern lesen, hochladen, auflisten und verwalten.

Einstellungen (Einstellungen -> MCP Tools -> sftp):
  - host      : Server-Hostname oder IP
  - port      : Port (SFTP: 22, FTP: 21)
  - username  : Benutzername
  - password  : Passwort
  - protocol  : 'sftp' oder 'ftp' (Standard: sftp)
"""

import ftplib
import io
import os

from config import get_tool_settings
from services.tool_context import get_emit_log

SETTINGS_INFO = """**SFTP / FTP**

Dateien auf einem SFTP- oder FTP-Server lesen, hochladen, auflisten und verwalten.

**SFTP (empfohlen, verschluesselt):**
- Protokoll: `sftp`
- Standard-Port: `22`
- Benoetigt: `paramiko` (wird automatisch installiert)

**FTP (unverschluesselt):**
- Protokoll: `ftp`
- Standard-Port: `21`
- Kein zusaetzliches Paket benoetigt

**Hinweis:** Bei FTP werden Zugangsdaten unverschluesselt uebertragen. SFTP wird empfohlen.

> ⚠️ **Achtung:** Dieses Tool kann Daten schreiben, bearbeiten oder loeschen. Fehlerhafte Eingaben koennen zu **Datenverlust oder ungewollten Aktionen** fuehren. Bitte mit Bedacht einsetzen."""

SETTINGS_SCHEMA = [
    {
        "key": "host",
        "label": "Host",
        "type": "text",
        "placeholder": "sftp.beispiel.de",
        "description": "Hostname oder IP-Adresse des Servers",
    },
    {
        "key": "port",
        "label": "Port",
        "type": "text",
        "placeholder": "22",
        "description": "Port (SFTP: 22, FTP: 21)",
    },
    {
        "key": "username",
        "label": "Benutzername",
        "type": "text",
        "placeholder": "meinuser",
        "description": "Login-Benutzername",
    },
    {
        "key": "password",
        "label": "Passwort",
        "type": "password",
        "placeholder": "••••••••",
        "description": "Login-Passwort",
    },
    {
        "key": "protocol",
        "label": "Protokoll",
        "type": "text",
        "placeholder": "sftp",
        "description": "sftp (verschluesselt, empfohlen) oder ftp",
    },
]

TOOL_DEFINITION = {
    "name": "sftp",
    "description": (
        "SFTP/FTP: Dateien auf einem Server verwalten. "
        "Aktionen: list_files (Verzeichnis auflisten) | "
        "read_file (Dateiinhalt lesen) | "
        "write_file (Datei schreiben/hochladen) | "
        "delete_file (Datei loeschen) | "
        "rename_file (Datei umbenennen oder verschieben) | "
        "mkdir (Verzeichnis erstellen) | "
        "stat_file (Datei-Infos abrufen)"
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": [
                    "list_files",
                    "read_file",
                    "write_file",
                    "delete_file",
                    "rename_file",
                    "mkdir",
                    "stat_file",
                ],
                "description": (
                    "Aktion: "
                    "list_files (Verzeichnis auflisten, optional path) | "
                    "read_file (Textdatei lesen, path erforderlich) | "
                    "write_file (Datei schreiben, path + content erforderlich) | "
                    "delete_file (Datei loeschen, path erforderlich) | "
                    "rename_file (umbenennen/verschieben, path + new_path erforderlich) | "
                    "mkdir (Verzeichnis erstellen, path erforderlich) | "
                    "stat_file (Groesse + Datum, path erforderlich)"
                ),
            },
            "path": {
                "type": "string",
                "description": "Pfad auf dem Server (z.B. /home/user/datei.txt oder /var/www/)",
            },
            "new_path": {
                "type": "string",
                "description": "Neuer Pfad fuer rename_file",
            },
            "content": {
                "type": "string",
                "description": "Dateiinhalt fuer write_file (Text)",
            },
            "encoding": {
                "type": "string",
                "description": "Zeichenkodierung fuer read_file (Standard: utf-8)",
            },
        },
        "required": ["action"],
    },
}


def _cfg():
    return get_tool_settings("sftp")


# ── SFTP via paramiko ──────────────────────────────────────────────────────────

def _sftp_connect(host, port, username, password):
    try:
        import paramiko
    except ImportError:
        raise RuntimeError(
            "paramiko nicht installiert. Bitte 'pip install paramiko' ausfuehren "
            "oder in requirements.txt eintragen und Container neu bauen."
        )
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, port=int(port), username=username, password=password, timeout=15)
    sftp = client.open_sftp()
    return client, sftp


def _sftp_action(action, host, port, username, password, path, new_path, content, encoding):
    client, sftp = _sftp_connect(host, port, username, password)
    try:
        if action == "list_files":
            target = path or "."
            entries = sftp.listdir_attr(target)
            result = []
            for e in sorted(entries, key=lambda x: x.filename):
                import stat as stat_mod
                is_dir = stat_mod.S_ISDIR(e.st_mode)
                result.append({
                    "name": e.filename,
                    "type": "dir" if is_dir else "file",
                    "size": e.st_size if not is_dir else None,
                })
            return {"path": target, "count": len(result), "entries": result}

        elif action == "read_file":
            if not path:
                return {"error": "path erforderlich"}
            with sftp.open(path, "r") as f:
                raw = f.read()
            text = raw.decode(encoding or "utf-8", errors="replace")
            return {"path": path, "size": len(raw), "content": text}

        elif action == "write_file":
            if not path:
                return {"error": "path erforderlich"}
            if content is None:
                return {"error": "content erforderlich"}
            data = content.encode(encoding or "utf-8")
            with sftp.open(path, "w") as f:
                f.write(data)
            return {"success": True, "path": path, "bytes_written": len(data)}

        elif action == "delete_file":
            if not path:
                return {"error": "path erforderlich"}
            sftp.remove(path)
            return {"success": True, "path": path}

        elif action == "rename_file":
            if not path or not new_path:
                return {"error": "path und new_path erforderlich"}
            sftp.rename(path, new_path)
            return {"success": True, "from": path, "to": new_path}

        elif action == "mkdir":
            if not path:
                return {"error": "path erforderlich"}
            sftp.mkdir(path)
            return {"success": True, "path": path}

        elif action == "stat_file":
            if not path:
                return {"error": "path erforderlich"}
            s = sftp.stat(path)
            import stat as stat_mod
            import datetime
            return {
                "path": path,
                "size": s.st_size,
                "modified": datetime.datetime.fromtimestamp(s.st_mtime).isoformat() if s.st_mtime else None,
                "is_dir": stat_mod.S_ISDIR(s.st_mode),
            }

        else:
            return {"error": f"Unbekannte Aktion: '{action}'"}
    finally:
        sftp.close()
        client.close()


# ── FTP via ftplib ─────────────────────────────────────────────────────────────

def _ftp_connect(host, port, username, password):
    ftp = ftplib.FTP()
    ftp.connect(host, int(port), timeout=15)
    ftp.login(username, password)
    return ftp


def _ftp_action(action, host, port, username, password, path, new_path, content, encoding):
    ftp = _ftp_connect(host, port, username, password)
    try:
        if action == "list_files":
            target = path or "."
            lines = []
            ftp.dir(target, lines.append)
            return {"path": target, "count": len(lines), "listing": lines}

        elif action == "read_file":
            if not path:
                return {"error": "path erforderlich"}
            buf = io.BytesIO()
            ftp.retrbinary(f"RETR {path}", buf.write)
            raw = buf.getvalue()
            text = raw.decode(encoding or "utf-8", errors="replace")
            return {"path": path, "size": len(raw), "content": text}

        elif action == "write_file":
            if not path:
                return {"error": "path erforderlich"}
            if content is None:
                return {"error": "content erforderlich"}
            data = content.encode(encoding or "utf-8")
            buf = io.BytesIO(data)
            ftp.storbinary(f"STOR {path}", buf)
            return {"success": True, "path": path, "bytes_written": len(data)}

        elif action == "delete_file":
            if not path:
                return {"error": "path erforderlich"}
            ftp.delete(path)
            return {"success": True, "path": path}

        elif action == "rename_file":
            if not path or not new_path:
                return {"error": "path und new_path erforderlich"}
            ftp.rename(path, new_path)
            return {"success": True, "from": path, "to": new_path}

        elif action == "mkdir":
            if not path:
                return {"error": "path erforderlich"}
            ftp.mkd(path)
            return {"success": True, "path": path}

        elif action == "stat_file":
            if not path:
                return {"error": "path erforderlich"}
            size = ftp.size(path)
            return {"path": path, "size": size}

        else:
            return {"error": f"Unbekannte Aktion: '{action}'"}
    finally:
        try:
            ftp.quit()
        except Exception:
            pass


# ── Handler ────────────────────────────────────────────────────────────────────

def handler(
    action,
    path=None,
    new_path=None,
    content=None,
    encoding=None,
):
    emit_log = get_emit_log()

    def log(msg):
        if emit_log:
            emit_log({"type": "text", "message": f"[SFTP] {msg}"})

    def header(msg):
        if emit_log:
            emit_log({"type": "header", "message": msg})

    cfg = _cfg()
    host = cfg.get("host", "").strip()
    username = cfg.get("username", "").strip()
    password = cfg.get("password", "").strip()
    protocol = cfg.get("protocol", "sftp").strip().lower() or "sftp"
    port = cfg.get("port", "").strip() or ("22" if protocol == "sftp" else "21")

    if not host or not username:
        return {"error": "Host und Benutzername erforderlich. Bitte in Einstellungen -> MCP Tools -> sftp eintragen."}

    header(f"{protocol.upper()} {action.upper()}: {path or '/'}")
    log(f"{protocol.upper()}://{username}@{host}:{port}")

    try:
        if protocol == "sftp":
            result = _sftp_action(action, host, port, username, password, path, new_path, content, encoding)
        elif protocol == "ftp":
            result = _ftp_action(action, host, port, username, password, path, new_path, content, encoding)
        else:
            return {"error": f"Unbekanntes Protokoll: '{protocol}'. Bitte 'sftp' oder 'ftp' verwenden."}
        log("Fertig")
        return result
    except Exception as e:
        log(f"Fehler: {e}")
        return {"error": str(e)}
