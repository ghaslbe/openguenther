import os
import re
import shutil
import py_compile
import tempfile

from config import DATA_DIR
from services.tool_context import get_emit_log

TOOL_DEFINITION = {
    "name": "create_mcp_tool",
    "description": (
        "Legt ein neues Custom MCP-Tool an und registriert es sofort in der Registry — "
        "kein Neustart nötig. "
        "Übergib den vollständigen Python-Code für tool.py (mit TOOL_DEFINITION und handler-Funktion). "
        "Verwende dieses Tool wenn der Nutzer ein neues eigenes Tool/Funktion/Fähigkeit für Guenther erstellen will."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "tool_name": {
                "type": "string",
                "description": (
                    "Verzeichnis- und Dateiname des Tools, z.B. 'spiegelcaller'. "
                    "Nur Kleinbuchstaben, Ziffern und Unterstriche."
                )
            },
            "code": {
                "type": "string",
                "description": (
                    "Vollständiger Python-Code für tool.py. Muss enthalten: "
                    "TOOL_DEFINITION (dict mit name, description, input_schema) "
                    "und eine handler()-Funktion oder eine Funktion mit dem Tool-Namen. "
                    "Darf beliebige Standardbibliotheks-Imports enthalten (requests ist verfügbar). "
                    "Beispiel:\n"
                    "TOOL_DEFINITION = {\"name\": \"my_tool\", \"description\": \"...\", "
                    "\"input_schema\": {\"type\": \"object\", \"properties\": {}, \"required\": []}}\n"
                    "def handler():\n    return {\"result\": \"ok\"}"
                )
            }
        },
        "required": ["tool_name", "code"]
    }
}


def handler(tool_name: str, code: str) -> dict:
    emit_log = get_emit_log()

    def log(msg):
        if emit_log:
            emit_log({"type": "text", "message": msg})

    def header(msg):
        if emit_log:
            emit_log({"type": "header", "message": msg})

    # Sanitize tool_name
    safe_name = re.sub(r'[^a-z0-9_]', '_', tool_name.lower().strip())
    if not safe_name:
        return {"success": False, "error": "Ungültiger Tool-Name"}

    tool_dir = os.path.join(DATA_DIR, 'custom_tools', safe_name)
    tool_py = os.path.join(tool_dir, 'tool.py')
    init_py = os.path.join(tool_dir, '__init__.py')

    header(f"CREATE MCP TOOL: {safe_name}")

    # Validate that code contains TOOL_DEFINITION and a handler
    if 'TOOL_DEFINITION' not in code:
        return {"success": False, "error": "Code enthält kein TOOL_DEFINITION dict."}
    if 'def handler' not in code and f'def {safe_name}' not in code:
        return {"success": False, "error": "Code enthält keine handler()-Funktion."}

    # Syntax check BEFORE writing anything to disk
    try:
        with tempfile.NamedTemporaryFile(suffix='.py', mode='w', encoding='utf-8', delete=False) as tmp:
            tmp.write(code)
            tmp_path = tmp.name
        py_compile.compile(tmp_path, doraise=True)
        os.unlink(tmp_path)
    except py_compile.PyCompileError as e:
        os.unlink(tmp_path)
        return {"success": False, "error": f"Syntax-Fehler im Code: {str(e)}"}

    # Write files
    os.makedirs(tool_dir, exist_ok=True)
    with open(tool_py, 'w', encoding='utf-8') as f:
        f.write(code)
    with open(init_py, 'w', encoding='utf-8') as f:
        pass

    log(f"Geschrieben: {tool_py}")

    # Load into registry immediately — rollback on any error
    try:
        from mcp.loader import _load_module, _register_module
        mod = _load_module(tool_py, f'custom_tools.{safe_name}')
        count = _register_module(mod, f'custom/{safe_name}')
        if count == 0:
            shutil.rmtree(tool_dir)
            log(f"Rollback: Verzeichnis {tool_dir} gelöscht")
            return {
                "success": False,
                "error": "Code hat keine Fehler, aber kein Tool konnte registriert werden. "
                         "TOOL_DEFINITION oder handler-Funktion prüfen."
            }
        log(f"Tool '{safe_name}' erfolgreich registriert ({count} Tool(s))")
        header(f"CREATE MCP TOOL: FERTIG")
        return {
            "success": True,
            "tool_name": safe_name,
            "path": tool_py,
            "registered": count
        }
    except Exception as e:
        shutil.rmtree(tool_dir, ignore_errors=True)
        log(f"Rollback: Verzeichnis {tool_dir} gelöscht")
        return {
            "success": False,
            "error": f"Fehler beim Laden des Tools (Rollback durchgeführt): {str(e)}"
        }
