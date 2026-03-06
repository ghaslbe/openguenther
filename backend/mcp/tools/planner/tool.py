"""
Planner MCP Tool

Erstellt einen strukturierten Ausfuehrungsplan fuer ein Ziel
auf Basis der aktuell verfuegbaren MCP-Tools.
"""

from mcp.registry import registry
from services.tool_context import get_emit_log

TOOL_DEFINITION = {
    "name": "plan_task",
    "description": (
        "Erstellt einen strukturierten Schritt-fuer-Schritt-Ausfuehrungsplan fuer ein Ziel. "
        "Listet alle verfuegbaren Tools auf und gibt einen Planungs-Scaffold zurueck. "
        "Immer als ersten Schritt aufrufen bevor komplexe Aufgaben ausgefuehrt werden."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "goal": {
                "type": "string",
                "description": "Das Ziel oder die Aufgabe, fuer die ein Plan erstellt werden soll",
            },
            "context": {
                "type": "string",
                "description": "Optionaler Zusatzkontext oder Einschraenkungen (z.B. 'nur auf Deutsch', 'max. 3 Schritte')",
            },
        },
        "required": ["goal"],
    },
    "always_enabled": True,
}


def handler(goal, context=None):
    emit_log = get_emit_log()

    def log(msg):
        if emit_log:
            emit_log({"type": "text", "message": f"[Planner] {msg}"})

    def header(msg):
        if emit_log:
            emit_log({"type": "header", "message": msg})

    header("PLAN ERSTELLEN")
    log(f"Ziel: {goal}")

    # Alle verfuegbaren Tools aus dem Registry holen
    all_tools = registry.list_tools()
    tool_lines = []
    for t in sorted(all_tools, key=lambda x: x.name):
        # Erste Zeile der Description (kurz halten)
        desc = t.description.split(".")[0].strip()
        source = "built-in" if t.server_id is None else f"extern ({t.server_id})"
        tool_lines.append(f"  - {t.name} [{source}]: {desc}")

    tool_list = "\n".join(tool_lines)
    log(f"{len(all_tools)} Tools verfuegbar")

    context_block = f"\n\nZusatzkontext: {context}" if context else ""

    return {
        "goal": goal,
        "available_tools_count": len(all_tools),
        "instruction": (
            f"AUFGABE: {goal}{context_block}\n\n"
            f"VERFUEGBARE TOOLS ({len(all_tools)}):\n{tool_list}\n\n"
            "ANWEISUNG:\n"
            "Erstelle jetzt einen konkreten, nummerierten Ausfuehrungsplan:\n"
            "- Welche Tools werden in welcher Reihenfolge aufgerufen?\n"
            "- Was sind die Eingaben fuer jeden Schritt?\n"
            "- Was ist das erwartete Ergebnis jedes Schritts?\n\n"
            "Praesentiiere den Plan zuerst, dann fuehre jeden Schritt der Reihe nach aus. "
            "Berichte nach jedem Schritt kurz das Ergebnis, bevor du mit dem naechsten Schritt beginnst. "
            "Passe den Plan an, wenn ein Schritt fehlschlaegt oder unerwartete Ergebnisse liefert."
        ),
    }
