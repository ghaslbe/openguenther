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
            "Guenther ist ein KI-Assistent mit Zugang zu verschiedenen Werkzeugen (MCP Tools).\n\n"
            "VERFUEGBARE TOOLS:\n"
            "- 'Wie spaet ist es?' -> get_current_time\n"
            "- 'Wuerfle mit 2W6' -> roll_dice\n"
            "- 'Was ist 42 * 17 + 3?' -> calculate\n"
            "- 'Erstelle einen QR-Code fuer https://example.com' -> generate_qr_code\n"
            "- 'Generiere ein sicheres Passwort' -> generate_password\n"
            "- 'Was steht auf der Seite example.com?' -> fetch_website_info\n"
            "- 'Schreibe die Uhrzeit als Bild' -> text_to_image\n"
            "- 'Sende eine E-Mail an ...' -> send_email (SMTP konfigurieren)\n"
            "- 'Generiere ein Bild von ...' -> generate_image (Bildgenerierungs-Modell noetig)\n"
            "- 'Analysiere dieses Bild ...' -> process_image (Vision-Modell noetig)\n"
            "- 'Wie ist das Wetter in Berlin?' -> get_weather\n"
            "- 'Was ist ein Schwarzes Loch?' -> wikipedia_search\n"
            "- 'Welche Tools hast du?' -> list_available_tools\n"
            "- 'Konvertiere diese CSV zu JSON' -> run_code (Code-Interpreter)\n"
            "- 'Erstelle ein neues Tool namens X' -> create_mcp_tool\n"
            "- 'Bearbeite das Tool X, es soll jetzt...' -> edit_mcp_tool\n"
            "- 'Loesche das Tool X' -> delete_mcp_tool\n"
            "- 'Sende eine Telegram-Nachricht an @nutzer' -> send_telegram\n\n"
            "AGENTEN-SYSTEM:\n"
            "In Einstellungen -> Agenten kannst du eigene Agenten mit individuellem System-Prompt "
            "erstellen. Beim Start eines neuen Chats waehle einen Agenten aus — er bestimmt dann "
            "das Verhalten fuer den gesamten Chat. Der Agenten-Name erscheint statt 'Guenther' "
            "in den Nachrichten.\n\n"
            "DATEI-UPLOAD:\n"
            "Das Bueroklammer-Symbol (📎) neben dem Eingabefeld erlaubt das Hochladen von "
            "Textdateien (CSV, JSON, XML, TXT usw.). Der Inhalt wird dem LLM als Kontext "
            "mitgegeben — es kann die Daten dann direkt an run_code uebergeben.\n\n"
            "TOOL-ROUTER:\n"
            "Vor jedem Agent-Lauf filtert ein leichtgewichtiger LLM-Call die relevanten Tools "
            "heraus (spart Tokens). Im Guenther-Terminal als 'TOOL-ROUTER' sichtbar.\n\n"
            "GUENTHER TERMINAL (rechte Seite):\n"
            "Zeigt alle Kommunikation live: System-Prompt, API-Requests/Responses, "
            "Tool-Calls und Ergebnisse. JSON wird mit Syntax-Highlighting dargestellt "
            "und grosse Bloecke sind einklappbar.\n\n"
            "AUTOPROMPTS:\n"
            "In Einstellungen -> Autoprompts kannst du Prompts hinterlegen, die automatisch zu "
            "festgelegten Zeiten ausgefuehrt werden (wie Cron-Jobs). Zeitplan-Typen: Intervall "
            "(alle X Minuten), taeglich (HH:MM UTC), woechentlich (Wochentag + Uhrzeit UTC). "
            "Per Default laeuft der Agent still — kein Chat wird angelegt. Mit 'Ergebnis in Chat "
            "speichern' landet die Antwort in einem dedizierten Chat im Verlauf. Der Play-Button "
            "fuehrt den Autoprompt sofort aus (unabhaengig vom Zeitplan).\n\n"
            "TELEGRAM GATEWAY:\n"
            "Guenther kann als Telegram-Bot betrieben werden (Einstellungen -> Telegram Gateway). "
            "Bilder (QR-Codes, text_to_image) werden als echte Foto-Nachrichten gesendet. "
            "Mit send_telegram kann Guenther aktiv Nachrichten senden (z.B. aus Autoprompts).\n\n"
            "In den Einstellungen kannst du:\n"
            "- OpenRouter API-Key und Standard-Modell konfigurieren\n"
            "- Pro Tool ein eigenes Modell festlegen (z.B. guenstiges Modell fuer einfache Tools)\n"
            "- Spracheingabe (STT) und Sprachausgabe (TTS) Modelle waehlen\n"
            "- SMTP fuer E-Mail-Versand einrichten\n"
            "- Telegram Bot-Token und erlaubte Nutzer konfigurieren\n"
            "- Externe MCP-Server anbinden"
        ),
        "tools": (
            "Nutze das Tool 'list_available_tools' um alle verfuegbaren Tools anzuzeigen.\n\n"
            "EINGEBAUTE TOOLS:\n"
            "- get_current_time: Aktuelle Uhrzeit mit Zeitzone\n"
            "- text_to_image: Text als PNG rendern (Pillow, konfigurierbare Schrift/Farben)\n"
            "- roll_dice: Wuerfeln (n Wuerfel mit m Seiten)\n"
            "- calculate: Sichere Mathe-Auswertung (AST-basiert, kein eval)\n"
            "- generate_qr_code: QR-Code als PNG generieren\n"
            "- generate_password: Sichere Passwoerter erstellen\n"
            "- fetch_website_info: Website-Titel und Description abrufen\n"
            "- send_email: E-Mail via SMTP senden (SMTP-Einstellungen erforderlich)\n"
            "- generate_image: Bild per KI generieren (Bildgenerierungs-Modell konfigurieren)\n"
            "- process_image: Bild analysieren oder bearbeiten (Vision-Modell)\n"
            "- get_weather: Aktuelles Wetter und Vorhersage abrufen\n"
            "- wikipedia_search: Wikipedia durchsuchen — findet auch Ortsteile & Weiterleitungen (de/en/...)\n"
            "- text_to_speech: Text vorlesen via ElevenLabs (API Key in Tool-Einstellungen)\n"
            "- run_code: Python-Code via LLM generieren und ausfuehren (Datenverarbeitung, Konvertierung)\n"
            "- create_mcp_tool: Neues Custom Tool anlegen und sofort registrieren\n"
            "- edit_mcp_tool: Bestehendes Custom Tool bearbeiten und neu laden\n"
            "- delete_mcp_tool: Custom Tool dauerhaft loeschen und aus Registry entfernen\n"
            "- send_telegram: Telegram-Nachricht an @username oder numerische Chat-ID senden\n"
            "- list_available_tools: Alle Tools auflisten\n"
            "- get_help: Diese Hilfe anzeigen\n\n"
            "PRO-TOOL MODELL-OVERRIDE:\n"
            "In den Einstellungen -> Aktive Tools -> Einstellungen kannst du fuer jedes Tool "
            "ein eigenes OpenRouter-Modell festlegen. Wenn alle vom Tool-Router ausgewaehlten "
            "Tools dasselbe Modell konfiguriert haben, wird dieses verwendet — sonst das Standard-Modell. "
            "So kann man z.B. fuer get_current_time ein guenstiges Modell wie "
            "mistralai/ministral-8b angeben."
        ),
        "settings": (
            "Klicke unten links auf 'Einstellungen' um:\n\n"
            "OPENROUTER:\n"
            "- API-Key: OpenRouter-Key (sk-or-v1-...)\n"
            "- Chat-Modell: Standard-LLM fuer alle Anfragen (z.B. openai/gpt-4o-mini)\n"
            "- STT-Modell: Fuer Spracheingabe via OpenRouter (leer = Chat-Modell)\n"
            "- TTS-Modell: Fuer Sprachausgabe (leer = Chat-Modell)\n"
            "- Bildgenerierungs-Modell: z.B. black-forest-labs/flux-1.1-pro\n"
            "- OpenAI Whisper: Alternativ whisper-1 fuer zuverlaessigere STT\n\n"
            "AKTIVE TOOLS:\n"
            "- Jedes Tool hat einen 'Einstellungen'-Button\n"
            "- Dort kann ein tool-spezifisches OpenRouter-Modell gesetzt werden\n"
            "- Tools mit SMTP-/Schrift-/etc. Einstellungen zeigen weitere Felder\n\n"
            "EXTERNE MCP-SERVER:\n"
            "- Stdio-basierte MCP-Server (JSON-RPC 2.0) hinzufuegen\n"
            "- 'MCP Tools neu laden' verbindet alle konfigurierten Server\n\n"
            "TELEGRAM GATEWAY:\n"
            "- Bot-Token von @BotFather eintragen\n"
            "- Erlaubte Nutzer (Whitelist) konfigurieren\n"
            "- Gateway starten/stoppen/neu starten"
        ),
        "mcp": (
            "MCP (Model Context Protocol) ist ein Standard fuer die Kommunikation zwischen "
            "KI-Modellen und Tools. Guenther nutzt MCP intern fuer alle Werkzeuge.\n\n"
            "INTERNER ABLAUF:\n"
            "1. Nutzer sendet Nachricht\n"
            "2. Tool-Router (leichtgewichtiger LLM-Call) waehlt relevante Tools aus\n"
            "3. Modell-Override: Falls Tools ein spezifisches Modell konfiguriert haben, wird es genutzt\n"
            "4. Agent-Loop: Nachricht + gefilterte Tools an OpenRouter\n"
            "5. LLM antwortet mit Text oder tool_calls\n"
            "6. Bei tool_calls: Tools ausfuehren, Ergebnis zurueck an LLM, wiederholen\n"
            "7. Finale Antwort speichern und senden\n\n"
            "EXTERNE MCP-SERVER:\n"
            "Ueber Einstellungen koennen externe MCP-Server (stdio-Transport) angebunden werden. "
            "Guenther verbindet sich per JSON-RPC 2.0 und registriert deren Tools automatisch."
        ),
        "telegram": (
            "Der Telegram-Gateway erlaubt die Nutzung von Guenther als Telegram-Bot.\n\n"
            "SETUP:\n"
            "1. Bot bei @BotFather erstellen, Token erhalten\n"
            "2. In Einstellungen -> Telegram Gateway den Token eintragen\n"
            "3. Erlaubte Nutzer (ohne @) eintragen (Whitelist)\n"
            "4. Gateway starten\n\n"
            "FEATURES:\n"
            "- /new <Name>: Neue Chat-Session starten\n"
            "- /start: Willkommensnachricht\n"
            "- Bilder (QR-Codes, text_to_image) werden als Foto gesendet\n"
            "- Sprachnachrichten werden per STT transkribiert\n"
            "- Polling-basiert (kein Webhook noetig)\n"
            "- Nachrichten auf 4096 Zeichen gekuerzt (Telegram-Limit)\n\n"
            "SEND_TELEGRAM TOOL:\n"
            "Guenther kann aktiv Telegram-Nachrichten senden — z.B. aus Autoprompts heraus.\n"
            "Empfaenger: '@username' (Nutzer muss dem Bot mind. einmal geschrieben haben) "
            "oder direkte numerische Chat-ID (z.B. '5761888867').\n"
            "Beispiel-Prompt: 'Ruf den Wetterbericht ab und sende ihn an @mama75.'"
        ),
        "autoprompts": (
            "Autoprompts sind geplante Aufgaben die Guenther automatisch ausfuehrt — aehnlich wie Cron-Jobs.\n\n"
            "KONFIGURATION (Einstellungen -> Autoprompts):\n"
            "- Name: Bezeichnung des Autoprompts\n"
            "- Prompt: Die Aufgabe die Guenther ausfuehren soll\n"
            "- Zeitplan: Intervall, Taeglich oder Woechentlich\n"
            "- Agent: Optional einen eigenen Agenten auswaehlen\n"
            "- 'Ergebnis in Chat speichern': Aktiviert -> Antwort landet in dediziertem Chat\n\n"
            "ZEITPLAN-TYPEN:\n"
            "- Intervall: Alle X Minuten, z.B. alle 60 min oder alle 2h\n"
            "- Taeglich: Einmal pro Tag zu einer bestimmten Uhrzeit (UTC)\n"
            "- Woechentlich: Einmal pro Woche (Wochentag + Uhrzeit UTC)\n"
            "Hinweis: Alle Zeiten sind UTC. Die aktuelle Server-Zeit wird im Formular angezeigt.\n\n"
            "AUSFUEHRUNGSMODUS:\n"
            "- Still (Standard): Agent laeuft im Hintergrund, kein Chat-Eintrag wird erstellt.\n"
            "  Ideal fuer Autoprompts die z.B. per send_telegram Ergebnisse weiterleiten.\n"
            "- 'Ergebnis in Chat speichern': Ein dedizierter Chat wird beim ersten Lauf angelegt\n"
            "  und bei jedem weiteren Lauf wiederverwendet.\n\n"
            "JETZT AUSFUEHREN:\n"
            "Der Play-Button (▶) fuehrt den Autoprompt sofort aus — unabhaengig vom Zeitplan.\n"
            "Nach dem Lauf erscheint 'Erfolgreich' (klickbar -> Log-Popup) oder 'Fehler' "
            "(klickbar -> Fehlermeldung) + 'Log' (alle Agent-Schritte).\n\n"
            "BEISPIEL-PROMPTS:\n"
            "'Ruf den Wetterbericht fuer Muenchen ab und sende ihn per Telegram an @mama75.'\n"
            "'Hole die aktuellen Schlagzeilen von tagesschau.de und speichere sie im Chat.'\n"
            "'Pruefe ob example.com erreichbar ist und informiere mich per Telegram falls nicht.'"
        ),
        "wikipedia": (
            "Das wikipedia_search Tool sucht Wikipedia-Artikel und liefert deren Inhalt.\n\n"
            "FUNKTIONSWEISE:\n"
            "1. Direkter Titel-Lookup: Prueft ob ein Artikel mit dem exakten Begriff existiert\n"
            "2. Weiterleitungen werden automatisch verfolgt (z.B. 'Thannenmais' -> 'Reisbach')\n"
            "3. Falls der Begriff nur im Artikeltext (nicht in der Einleitung) vorkommt,\n"
            "   wird der vollstaendige Artikel durchsucht und die relevante Textstelle\n"
            "   als 'erwaehnung_im_artikel' zurueckgegeben\n"
            "4. Fallback: Volltextsuche mit Relevanz-Scoring wenn kein direkter Artikel gefunden\n"
            "5. Automatischer Fallback auf Englisch wenn keine deutschen Ergebnisse\n\n"
            "PARAMETER:\n"
            "- query: Suchbegriff (Pflicht)\n"
            "- language: Sprache, Standard 'de' (auch 'en', 'fr', 'es', etc.)\n"
            "- results: 1-5 Ergebnisse, Standard 1\n\n"
            "RUECKGABEFELDER:\n"
            "- titel: Artikeltitel\n"
            "- zusammenfassung: Artikel-Einleitung (bis 3000 Zeichen)\n"
            "- erwaehnung_im_artikel: Textstelle wo der Suchbegriff vorkommt (bei Weiterleitungen)\n"
            "- weiterleitung_von: Original-Suchbegriff wenn Weiterleitung gefolgt wurde\n"
            "- hinweis: Erklaerung wenn kein direkter Artikel gefunden\n"
            "- url: Link zum Wikipedia-Artikel\n\n"
            "BEISPIELE:\n"
            "- 'Albert Einstein' -> direkter Artikel\n"
            "- 'Thannenmais' -> Weiterleitung zu 'Reisbach' + Erwaehnung im Artikeltext\n"
            "- 'Quantenverschraenkung' -> Artikel mit Einleitung"
        ),
        "code": (
            "Das run_code Tool generiert Python-Code via LLM und fuehrt ihn aus.\n\n"
            "ANWENDUNGSFAELLE:\n"
            "- Dateikonvertierung: CSV -> JSON, JSON -> XML, usw.\n"
            "- Datenanalyse: Statistiken, Duplikate finden, Felder extrahieren\n"
            "- Textverarbeitung: Formatierung, Bereinigung, Umstrukturierung\n"
            "- Berechnungen mit komplexeren Daten\n\n"
            "ABLAUF:\n"
            "1. LLM-Anfrage: Das Tool beschreibt dem LLM die Aufgabe und die Eingabedaten\n"
            "2. Code-Generierung: LLM liefert Python-Skript (nur Standardbibliothek)\n"
            "3. Ausfuehrung: Skript laeuft in isoliertem Temp-Verzeichnis (Timeout: 30s)\n"
            "4. Rueckgabe: stdout als Ergebnis\n\n"
            "PARAMETER:\n"
            "- task: Was der Code tun soll (Pflicht)\n"
            "- input_data: Eingabedaten als String, z.B. CSV-Inhalt (optional)\n"
            "  Das Skript liest diese via sys.stdin\n\n"
            "DATEI-UPLOAD:\n"
            "Lade eine Datei per 📎 hoch, beschreibe die gewuenschte Konvertierung — "
            "das LLM ruft run_code automatisch mit dem Dateiinhalt als input_data auf.\n\n"
            "TERMINAL-LOGGING:\n"
            "Im Guenther-Terminal sieht man: LLM-Prompt, generierten Code, "
            "Ausfuehrungs-Output und eventuelle Fehler.\n\n"
            "EIGENES MODELL:\n"
            "In Einstellungen -> MCP Tools -> run_code -> Einstellungen kann ein "
            "separates Modell fuer die Code-Generierung festgelegt werden."
        ),
        "custom_tools": (
            "Guenther kann neue MCP-Tools direkt im Chat erstellen, bearbeiten und loeschen.\n\n"
            "TOOL ERSTELLEN:\n"
            "'Erstelle ein neues Tool namens spiegelcaller. Es soll spiegel.de 10x aufrufen und die Antwortzeiten zurueckgeben.'\n"
            "-> Guenther ruft create_mcp_tool auf:\n"
            "   tool_name: 'spiegelcaller'\n"
            "   code: vollstaendiger Python-Code mit TOOL_DEFINITION + handler()\n"
            "Das Tool wird sofort in die Registry geladen — kein Neustart noetig.\n\n"
            "TOOL BEARBEITEN:\n"
            "'Bearbeite spiegelcaller, es soll jetzt stern.de 20x aufrufen und die Zeiten als Tabelle ausgeben.'\n"
            "-> Guenther ruft edit_mcp_tool auf:\n"
            "   tool_name: 'spiegelcaller'\n"
            "   code: neuer vollstaendiger Python-Code\n"
            "Das alte Tool wird deregistriert, der neue Code sofort geladen.\n\n"
            "TOOL LOESCHEN:\n"
            "'Loesche das Tool spiegelcaller.'\n"
            "-> Guenther ruft delete_mcp_tool auf:\n"
            "   tool_name: 'spiegelcaller'\n"
            "Das Verzeichnis wird geloescht, das Tool aus der Registry entfernt.\n\n"
            "PERSISTENZ:\n"
            "Custom Tools liegen in /app/data/custom_tools/ (persistentes Docker-Volume).\n"
            "Sie ueberleben Container-Neustarts und werden beim Start automatisch geladen.\n\n"
            "PFLICHTSTRUKTUR fuer tool.py:\n"
            "TOOL_DEFINITION = {'name': '...', 'description': '...', 'input_schema': {...}}\n"
            "def handler(<params>):\n"
            "    return {...}  # JSON-serialisierbares dict\n\n"
            "Detaillierte Anleitung: Einstellungen -> Hilfe -> 'Custom Tools'"
        ),
        "agents": (
            "Das Agenten-System erlaubt eigene KI-Persoenlichkeiten mit individuellem System-Prompt.\n\n"
            "ANLEGEN:\n"
            "Einstellungen -> Agenten -> 'Neuen Agenten erstellen'\n"
            "- Name: z.B. 'Poet', 'Analyst', 'Code-Reviewer'\n"
            "- Beschreibung: Kurzzusammenfassung (optional)\n"
            "- System-Prompt: Die eigentliche Anweisung ans LLM\n\n"
            "VERWENDEN:\n"
            "Beim '+' (neuer Chat) erscheint ein Dropdown 'Agent:' wenn mindestens "
            "ein Agent angelegt ist. Ausgewaehlt oder leer (= Standard-Guenther).\n\n"
            "ANZEIGE:\n"
            "- Der Agenten-Name erscheint statt 'Guenther' in den Chat-Nachrichten\n"
            "- In der Chat-Liste wird ein farbiges Badge mit dem Agenten-Namen angezeigt\n\n"
            "WICHTIG:\n"
            "Der Agent-Prompt gilt fuer den gesamten Chat. Tools und Modell bleiben unveraendert — "
            "nur der System-Prompt wird ersetzt. Ohne Agent gilt der Standard-Guenther-Prompt."
        ),
        "voice": (
            "Guenther unterstuetzt Spracheingabe (STT) fuer Telegram-Sprachnachrichten.\n\n"
            "STT-OPTIONEN:\n"
            "- OpenRouter STT-Modell: z.B. google/gemini-2.5-flash (in Einstellungen konfigurierbar)\n"
            "- OpenAI Whisper: whisper-1, zuverlaessiger fuer Audio (eigener API-Key noetig)\n"
            "- Leer lassen = Chat-Modell wird fuer STT verwendet\n\n"
            "BILDGENERIERUNG:\n"
            "- generate_image Tool nutzt das konfigurierte Bildgenerierungs-Modell\n"
            "- Empfohlen: google/gemini-2.5-flash-image-preview oder black-forest-labs/flux-1.1-pro\n\n"
            "PRO-TOOL MODELL:\n"
            "Jedes Tool kann ein eigenes Modell haben (Einstellungen -> Aktive Tools -> Einstellungen). "
            "Guenstige Modelle fuer einfache Tools sparen Kosten."
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
    "description": "Gibt Hilfe und Erklaerungen zu Guenther und seinen Funktionen. Themen: general, tools, settings, mcp, telegram, autoprompts, voice, wikipedia, code, agents, custom_tools.",
    "input_schema": {
        "type": "object",
        "properties": {
            "topic": {
                "type": "string",
                "description": "Hilfe-Thema: 'general', 'tools', 'settings', 'mcp', 'telegram', 'autoprompts', 'voice', 'wikipedia', 'code', 'agents' oder 'custom_tools'",
                "default": "general"
            }
        },
        "required": []
    }
}

# Multi-tool convention for the loader
TOOL_DEFINITIONS = [LIST_TOOLS_DEFINITION, HELP_DEFINITION]
HANDLERS = {
    'list_available_tools': list_available_tools,
    'get_help': get_help,
}
