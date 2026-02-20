from mcp.registry import registry


def list_available_tools():
    """List all available MCP tools with their descriptions."""
    tools = registry.list_tools()
    tool_list = []
    for t in tools:
        tool_list.append({
            "name": t.name,
            "description": t.description,
            "builtin": t.server_id is None,
        })
    return {
        "total": len(tool_list),
        "tools": tool_list
    }


def get_help(topic="general"):
    """Provide help about Guenther and its capabilities."""
    help_texts = {
        "general": (
            "Guenther ist ein KI-Assistent mit Zugang zu verschiedenen Werkzeugen (MCP Tools). "
            "Du kannst mich bitten, Aufgaben auszufuehren die diese Tools nutzen. "
            "Beispiele:\n"
            "- 'Wie spaet ist es?' -> get_current_time\n"
            "- 'Wuerfle mit 2 Wuerfeln' -> roll_dice\n"
            "- 'Was ist 42 * 17 + 3?' -> calculate\n"
            "- 'Erstelle einen QR-Code fuer https://example.com' -> generate_qr_code\n"
            "- 'Generiere ein sicheres Passwort' -> generate_password\n"
            "- 'Was steht auf der Seite example.com?' -> fetch_website_info\n"
            "- 'Schreibe die Uhrzeit als Bild' -> get_current_time + text_to_image\n"
            "- 'Sende eine E-Mail an ...' -> send_email (SMTP muss konfiguriert sein)\n"
            "- 'Welche Tools hast du?' -> list_available_tools\n\n"
            "Im rechten Terminal-Fenster (Guenther) siehst du alle Kommunikation: "
            "Prompts, API-Calls, Tool-Aufrufe und Ergebnisse.\n\n"
            "In den Einstellungen kannst du:\n"
            "- OpenRouter API-Key und Modell konfigurieren\n"
            "- SMTP fuer E-Mail-Versand einrichten\n"
            "- Externe MCP-Server anbinden"
        ),
        "tools": "Nutze das Tool 'list_available_tools' um alle verfuegbaren Tools anzuzeigen.",
        "settings": (
            "Klicke unten links auf 'Einstellungen' um:\n"
            "- OpenRouter API-Key und LLM-Modell festzulegen\n"
            "- SMTP-Server fuer E-Mail-Versand zu konfigurieren\n"
            "- Externe MCP-Server hinzuzufuegen"
        ),
        "mcp": (
            "MCP (Model Context Protocol) ist ein Standard fuer die Kommunikation zwischen "
            "KI-Modellen und Tools. Guenther nutzt MCP intern fuer alle Werkzeuge. "
            "Externe MCP-Server koennen ueber die Einstellungen angebunden werden (stdio-Transport)."
        ),
    }
    topic_lower = topic.lower()
    text = help_texts.get(topic_lower, help_texts["general"])
    return {"topic": topic, "help": text}


LIST_TOOLS_DEFINITION = {
    "name": "list_available_tools",
    "description": "Listet alle verfuegbaren MCP-Tools mit Namen und Beschreibung auf.",
    "input_schema": {
        "type": "object",
        "properties": {},
        "required": []
    }
}

HELP_DEFINITION = {
    "name": "get_help",
    "description": "Gibt Hilfe und Erklaerungen zu Guenther und seinen Funktionen. Themen: general, tools, settings, mcp.",
    "input_schema": {
        "type": "object",
        "properties": {
            "topic": {
                "type": "string",
                "description": "Hilfe-Thema: 'general', 'tools', 'settings' oder 'mcp'",
                "default": "general"
            }
        },
        "required": []
    }
}
