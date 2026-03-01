import os
import re
import shutil

from config import DATA_DIR
from services.tool_context import get_emit_log

TOOL_DEFINITION = {
    "name": "delete_mcp_tool",
    "description": (
        "Löscht ein Custom MCP-Tool dauerhaft (Verzeichnis + Dateien) und entfernt es aus der Registry. "
        "Nur Custom Tools unter /app/data/custom_tools/ können gelöscht werden — Built-in Tools nicht. "
        "Verwende dieses Tool wenn der Nutzer ein eigenes Tool entfernen will."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "tool_name": {
                "type": "string",
                "description": "Name des zu löschenden Tools (Verzeichnisname), z.B. 'spiegelcaller'."
            }
        },
        "required": ["tool_name"]
    }
}


def handler(tool_name: str) -> dict:
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

    header(f"DELETE MCP TOOL: {safe_name}")

    if not os.path.isdir(tool_dir):
        return {"success": False, "error": f"Tool '{safe_name}' nicht gefunden."}

    # Unregister from registry
    removed = []
    try:
        from mcp.loader import _load_module
        from mcp.registry import registry

        mod = _load_module(tool_py, f'custom_tools.{safe_name}_del')
        td = getattr(mod, 'TOOL_DEFINITION', None)
        tds = getattr(mod, 'TOOL_DEFINITIONS', None)
        if td:
            registry.unregister(td['name'])
            removed.append(td['name'])
            log(f"Tool '{td['name']}' aus Registry entfernt")
        elif tds:
            for t in tds:
                registry.unregister(t['name'])
                removed.append(t['name'])
                log(f"Tool '{t['name']}' aus Registry entfernt")
    except Exception as e:
        log(f"Hinweis: Konnte Tool nicht aus Registry entfernen: {e}")

    # Delete directory
    shutil.rmtree(tool_dir)
    log(f"Verzeichnis gelöscht: {tool_dir}")
    header(f"DELETE MCP TOOL: FERTIG")

    return {
        "success": True,
        "tool_name": safe_name,
        "unregistered": removed
    }
