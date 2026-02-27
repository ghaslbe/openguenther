import os
import re

from config import DATA_DIR
from services.tool_context import get_emit_log

TOOL_DEFINITION = {
    "name": "edit_mcp_tool",
    "description": (
        "Bearbeitet ein bestehendes Custom MCP-Tool und lädt es sofort neu. "
        "Ersetzt den kompletten Code von tool.py des angegebenen Tools. "
        "Verwende dieses Tool wenn der Nutzer ein vorhandenes eigenes Tool ändern oder aktualisieren will."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "tool_name": {
                "type": "string",
                "description": "Name des zu bearbeitenden Tools (Verzeichnisname), z.B. 'spiegelcaller'."
            },
            "code": {
                "type": "string",
                "description": (
                    "Vollständiger neuer Python-Code für tool.py. Muss enthalten: "
                    "TOOL_DEFINITION (dict mit name, description, input_schema) "
                    "und eine handler()-Funktion oder eine Funktion mit dem Tool-Namen."
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

    safe_name = re.sub(r'[^a-z0-9_]', '_', tool_name.lower().strip())
    tool_dir = os.path.join(DATA_DIR, 'custom_tools', safe_name)
    tool_py = os.path.join(tool_dir, 'tool.py')

    header(f"EDIT MCP TOOL: {safe_name}")

    if not os.path.isdir(tool_dir):
        return {"success": False, "error": f"Tool '{safe_name}' nicht gefunden. Nur Custom Tools können bearbeitet werden."}

    if 'TOOL_DEFINITION' not in code:
        return {"success": False, "error": "Code enthält kein TOOL_DEFINITION dict."}
    if 'def handler' not in code and f'def {safe_name}' not in code:
        return {"success": False, "error": "Code enthält keine handler()-Funktion."}

    # Read old tool name from registry to unregister it first
    try:
        from mcp.loader import _load_module, _register_module
        from mcp.registry import registry

        # Unregister old version
        old_mod = _load_module(tool_py, f'custom_tools.{safe_name}_old')
        old_td = getattr(old_mod, 'TOOL_DEFINITION', None)
        old_tds = getattr(old_mod, 'TOOL_DEFINITIONS', None)
        if old_td:
            registry.unregister(old_td['name'])
            log(f"Altes Tool '{old_td['name']}' aus Registry entfernt")
        elif old_tds:
            for td in old_tds:
                registry.unregister(td['name'])
                log(f"Altes Tool '{td['name']}' aus Registry entfernt")
    except Exception as e:
        log(f"Hinweis: Altes Tool konnte nicht deregistriert werden: {e}")

    # Write new code
    with open(tool_py, 'w', encoding='utf-8') as f:
        f.write(code)
    log(f"Geschrieben: {tool_py}")

    # Load new version
    try:
        from mcp.loader import _load_module, _register_module
        mod = _load_module(tool_py, f'custom_tools.{safe_name}')
        count = _register_module(mod, f'custom/{safe_name}')
        if count == 0:
            return {"success": False, "error": "Datei geschrieben, aber kein Tool konnte registriert werden."}
        log(f"Tool '{safe_name}' neu geladen ({count} Tool(s) registriert)")
        header(f"EDIT MCP TOOL: FERTIG")
        return {"success": True, "tool_name": safe_name, "registered": count}
    except Exception as e:
        return {"success": False, "error": f"Datei geschrieben, aber Fehler beim Laden: {str(e)}"}
