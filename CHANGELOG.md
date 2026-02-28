# Changelog

## [1.4.18] — 2026-02-28

### LLM Nutzungsstatistik

- Neue `usage_log`-Tabelle in SQLite: speichert pro LLM-Aufruf Timestamp, Provider, Modell, gesendete/empfangene Bytes, Prompt- und Completion-Tokens
- Byte-Messung in `call_openrouter()` — jeder Aufruf wird automatisch geloggt
- REST-API: `GET /api/usage/stats?period=today|week|month|all`, `GET /api/usage/timeline?granularity=hour|day|month`, `DELETE /api/usage/stats`
- **📊-Button in der Topbar**: öffnet Popup mit Heute- und Gesamt-Statistik pro Provider
- **Nutzungsstatistik in Einstellungen → LLM Provider**: Tabelle mit Period-Tabs (Heute/Woche/Monat/Gesamt), Anfragen, gesendete/empfangene Bytes, Tokens; Reset-Button mit Bestätigung
- i18n: neue Keys unter `settings.usage` in DE + EN

---

## [1.4.17] — 2026-02-28

### Persistente Datei-Speicherung für generierte Inhalte (PPTX)

- Generierte Dateien (PPTX) werden jetzt auf Disk gespeichert (`/app/data/files/<chat_id>/`) statt als Base64-Blob in SQLite
- DB-Eintrag enthält nur noch einen leichtgewichtigen Marker `[STORED_FILE](filename)` — kein riesiger Base64-String mehr im LLM-Kontext
- Neuer Download-Endpunkt `GET /api/chats/<id>/files/<filename>` — Download-Button im Chat nutzt Server-URL statt Data-URI
- Chat löschen bereinigt automatisch alle zugehörigen Dateien
- Fallback: Ältere Chats mit `[PPTX_DOWNLOAD]`-Marker funktionieren weiterhin (Telegram + Web)
- Neue `backend/services/file_store.py` — wiederverwendbar für künftige Dateitypen

---

## [1.4.16] — 2026-02-28

### Fix: Präsentation via Telegram als .pptx-Datei senden
- Bisher wurde die Präsentation als roher Base64-Text gesendet statt als Datei
- Telegram Gateway erkennt jetzt `[PPTX_DOWNLOAD]`-Marker und sendet die .pptx korrekt als Dokument

---

## [1.4.15] — 2026-02-28

### Fix: Provider-Test nutzt gespeicherten API Key
- "Verbindung testen" schlug mit 401 fehl, wenn der Key nicht neu eingegeben wurde — das Eingabefeld startet immer leer (aus Sicherheitsgründen)
- Backend fällt jetzt auf den gespeicherten Key zurück, wenn kein neuer Key übergeben wird

---

## [1.4.14] — 2026-02-28

### i18n: GUI Deutsch / Englisch + Mistral Provider + First-Run-Overlay

**Sprachumschalter**
- Button `DE` / `EN` in der Topbar (neben Theme-Toggle), Sprache wird in `localStorage` gespeichert (Standard: Deutsch)
- `react-i18next`: alle UI-Strings ausgelagert in `frontend/src/i18n/de.json` + `en.json`
- Übersetzte Komponenten: ChatList, ChatWindow, GuentherBox, ToolSettings, Settings, SettingsGeneral, SettingsAgents, SettingsAutoprompts, SettingsProviders, SettingsTools, SettingsMcp, SettingsTelegram — SettingsHilfe bleibt Deutsch

**First-Run-Overlay**
- Erscheint beim ersten Start wenn keine Sprache gespeichert und kein Provider konfiguriert ist
- Zweisprachig DE + EN: Sprachauswahl per Flaggen-Button, Hinweis auf OpenRouter / Ollama / LM Studio mit Link

**Einstellungen → Info**
- Haftungsausschluss vollständig in Deutsch **und** Englisch — identisch mit README (Bullet-Listen, Empfehlungen, Softwarequalitäts-Hinweis)

**Mistral als LLM Provider**
- **Mistral (Europa)** in den Provider-Einstellungen — zwischen OpenRouter und Ollama
- Base URL `https://api.mistral.ai/v1` (OpenAI-kompatibel), API Key erforderlich
- Direkte Links zu `console.mistral.ai` (API Keys) und `docs.mistral.ai`
- Bestehende Installationen: Mistral wird beim nächsten Start automatisch zu `settings.json` hinzugefügt (deaktiviert)

**Provider-Untertitel**
- OpenRouter: `(via USA, Modelle weltweit)` / `(via USA, models worldwide)`
- Mistral: `(Europa)` / `(Europe)`
- Ollama + LM Studio: `(lokale KI)` / `(local AI)`

---

## [1.4.10] — 2026-02-28

### Beta-Label + fetch_url Tool + README

- Topbar zeigt jetzt `beta`-Label neben der Versionsnummer
- README: Titel zu `OPENguenther (beta)` geändert
- README: Haftungsausschluss um Hinweis auf Fehler und Sicherheitslücken erweitert (DE + EN)
- README: Schnellinstallation (`curl ... | bash`) ganz oben ergänzt
- README: Features und Built-in-Tools-Tabellen vollständig aktualisiert (DE + EN)
- Neues Tool `fetch_url`: beliebige URL per GET/POST abrufen, JSON automatisch geparst, Text auf `max_chars` kürzbar

---

## [1.4.9] — 2026-02-28

### Hilfe-Updates: Autoprompts + send_telegram

- **Einstellungen → Hilfe**: neuer Abschnitt „Autoprompts" beschreibt Zeitplan-Typen, Silent-Modus, `save_to_chat`, UTC-Hinweis und Play-Button
- **Einstellungen → Hilfe**: Telegram-Gateway-Abschnitt erwähnt jetzt `send_telegram` mit Hinweis auf numerische Chat-ID
- **`get_help` MCP-Tool** (help/tool.py): neues Thema `autoprompts` abrufbar
- **`get_help` MCP-Tool**: `send_telegram` in Tool-Übersicht (general + tools) ergänzt
- **`get_help` MCP-Tool**: doppelte Einträge (`create_mcp_tool`, `edit_mcp_tool`, `delete_mcp_tool`) bereinigt
- **Autoprompts** — Silent-Modus als Standard: Agent läuft ohne Chat-Eintrag; optionale Checkbox „Ergebnis in Chat speichern" aktiviert dedizierten Chat

---

## [1.4.8] — 2026-02-28

### Autoprompts — UTC-Klarheit

- Aktuelle Server-Zeit (UTC) wird neben dem Uhrzeit-Eingabefeld angezeigt (`Aktuelle Server-Zeit: HH:MM UTC`)
- Label zeigt jetzt explizit `Uhrzeit (HH:MM, UTC)` — Scheduler läuft in UTC
- In der Autoprompt-Liste steht die Uhrzeit nun mit UTC-Suffix (z.B. `Täglich 07:15 UTC`)

---

## [1.4.7] — 2026-02-28

### Telegram-Tool + Autoprompt-Verbesserungen

- Neues Tool `send_telegram`: sendet eine Nachricht über Telegram an einen Nutzer
  - Akzeptiert `@username` (Lookup aus gespeichertem Mapping) **oder** direkte numerische Chat-ID (z.B. `5761888867`)
  - Prompt-Beispiel: „Rufe den Wetterbericht ab und sende ihn per Telegram an 5761888867"
  - `TelegramGateway` persistiert `username → telegram_chat_id` automatisch in `/app/data/telegram_users.json`
- Autoprompts — Ausführungs-Log und Status-Anzeige:
  - Nach jedem Lauf: vollständiger Agent-Log gespeichert (`last_log`, `last_status`)
  - **Erfolgreich**: grüner Link → öffnet Log-Popup mit allen Agent-Schritten
  - **Fehler**: roter Link → Fehlerdetail-Popup + grauer „Log"-Link → vollständiger Ausführungs-Log
- Fehler-Popup in Autoprompts: Hintergrund war transparent (fehlende CSS-Variable) — behoben
- Autoprompts: `'NoneType' object is not callable` bei Ausführung behoben (`emit_log=None` → No-op Lambda)

---

## [1.4.6] — 2026-02-28

### Autoprompts — geplante Prompts

- Neuer Einstellungsbereich **Autoprompts**: Prompts mit eigenem Zeitplan hinterlegen
  - Zeitplan-Typen: **Intervall** (alle X Minuten/Stunden), **Täglich** (HH:MM), **Wöchentlich** (Wochentag + HH:MM)
  - Optional: eigenen Agenten pro Autoprompt zuweisen
  - Ergebnisse landen in einem **dedizierten Chat** (einmalig erstellt, immer wiederverwendet — kein neuer Chat bei jedem Lauf)
  - ▶ Button zum sofortigen manuellen Ausführen
  - Pause/Aktiv Toggle zum temporären Deaktivieren
- Backend: `APScheduler` (BackgroundScheduler) für cron-artige Ausführung
- Backend: `backend/services/autoprompt.py` + `backend/routes/autoprompts.py`
- Persistenz: `/app/data/autoprompts.json` (liegt im Docker-Volume)
- `requirements.txt`: `apscheduler==3.10.4` ergänzt

---

## [1.4.5] — 2026-02-27

### Robusteres Custom-Tool-Management

- `create_mcp_tool`: Syntax-Check via `py_compile` **vor** dem Schreiben — bei Fehler wird nichts auf Disk geschrieben
- `create_mcp_tool`: Rollback bei Ladefehler — Verzeichnis wird automatisch gelöscht
- `edit_mcp_tool`: Syntax-Check vor dem Überschreiben — alte Datei bleibt unberührt
- `edit_mcp_tool`: Rollback bei Ladefehler — alte `tool.py` wird wiederhergestellt
- `/new` im Chat-Eingabefeld startet eine neue Session (identisch zum `+` Button)

---

## [1.4.4] — 2026-02-27

### Präsentations-Generator (`generate_presentation`)

- Neues Built-in Tool `generate_presentation`: erstellt professionelle PowerPoint-Präsentationen (.pptx)
  - Eingabe: Thema (Text) oder optionaler Quelltext als inhaltliche Basis
  - LLM generiert Folienstruktur als JSON, slidegen.py baut die PPTX daraus
  - 8 Layouts: `hero`, `cards`, `two-column`, `steps`, `icon-list`, `pyramid`, `feature`, `statement`
  - Zwei Farbthemen: `dark` (dunkel/orange) und `purple` (dunkel/lila)
  - Nutzt Standard-Provider + Modell; Override via Tool-Einstellungen konfigurierbar
  - Download-Button direkt im Chat (📊) — vollständig clientseitig, kein Server-Roundtrip
- `requirements.txt`: `python-pptx` und `lxml` ergänzt

---

## [1.4.2] — 2026-02-27

### Custom Tools vollständig via Chat verwaltbar

- Neues Tool `edit_mcp_tool`: bestehendes Custom Tool durch neuen Code ersetzen und sofort neu laden (altes Tool wird sauber deregistriert)
- Neues Tool `delete_mcp_tool`: Custom Tool dauerhaft löschen und aus der Registry entfernen
- `get_help`: neues Topic `custom_tools` mit vollständiger Anleitung für create/edit/delete
- Einstellungen → Hilfe: Abschnitt „Custom Tools" komplett überarbeitet — zeigt alle drei Operationen mit Beispiel-Prompts

## [1.4.1] — 2026-02-27

### Custom Tool Erstellung via Chat

- Neues Built-in Tool `create_mcp_tool`: Guenther kann auf Zuruf neue MCP-Tools anlegen
  - Nimmt `tool_name` + vollständigen Python-Code als Parameter
  - Schreibt `tool.py` + `__init__.py` nach `/app/data/custom_tools/<name>/`
  - Registriert das neue Tool sofort in der Registry — kein Reload, kein Neustart nötig
  - Validiert `TOOL_DEFINITION` und Handler-Funktion vor dem Schreiben
- Einstellungen → Hilfe: neuer Abschnitt „Custom Tools" mit Verzeichnisstruktur, Minimal-Beispiel und Schritt-für-Schritt-Anleitung

---

## [1.4.0] — 2026-02-27

### Tool-Architektur: Subdirectories + Auto-Discovery
- Jedes Built-in MCP Tool lebt jetzt in einem eigenen Unterordner (`backend/mcp/tools/<name>/tool.py`)
- Neuer Auto-Loader (`backend/mcp/loader.py`) scannt beide Verzeichnisse und registriert Tools automatisch
- **Custom Tools**: eigene Python-Tools in `/app/data/custom_tools/<name>/tool.py` ablegen → nach Neustart automatisch aktiv, ohne Code-Änderung
- `app.py` ohne manuelle Tool-Imports — vollständig über Loader gesteuert
- `CUSTOM_TOOL_GUIDE.md`: vollständige Schnittstellenbeschreibung für eigene Tools

---

## [1.3.9] — 2026-02-25

### SEO-Report als PDF
- **PDF-Download-Button** im Web-Chat: unter jedem SEO-Report erscheint „📄 PDF herunterladen" — Backend konvertiert via WeasyPrint und liefert `seo-report.pdf`
- **Telegram**: SEO-Report wird automatisch als `seo-report.pdf`-Dokument mitgeschickt (light-themed, A4, druckfertig)
- Neuer Backend-Endpoint `POST /api/tools/html-to-pdf` (WeasyPrint)
- Dockerfile: WeasyPrint-Systempakete ergänzt (`libpango`, `libcairo2` etc.)

---

## [1.3.8] — 2026-02-25

### SEO-Analyse-Tool (`analyze_seo`)
- Neues Built-in MCP Tool: SEO-Analyse für URLs oder direkt übergebenen HTML-Code
- Prüft: Title (Länge), Meta Description (Länge), H1 (Anzahl), Heading-Hierarchie, Bild-Alt-Texte, Canonical, HTML-lang, Open Graph (title/description/image), Twitter Card, Viewport, Robots-Meta, JSON-LD
- Ausgabe als visueller HTML-Report mit Gesamt-Score (0–100), Farbkodierung (grün/gelb/rot) und konkreten Empfehlungen — direkt im Chat-Fenster als iframe gerendert
- `fetch_website_info` entfernt (durch `analyze_seo` ersetzt)

---

## [1.3.7] — 2026-02-25

### Provider-Einstellungen & Fehlerbehebung
- **Modelle laden**: Dropdown-Liste der verfügbaren Modelle beim Standard-Modell-Feld — alphabetisch sortiert, Textfeld bleibt editierbar
- **Sidebar**: „Provider" → „LLM Provider"
- **OpenRouter-Links**: Direktlinks zu „API Keys" und „Verbrauch" in der OpenRouter-Karte
- **Fehlertext**: Fehlermeldungen bei LLM-Anfragen zeigen jetzt den echten Provider-Namen (z.B. „LM Studio 400: ...") statt immer „OpenRouter"
- **Version**: package.json auf 1.3.7 aktualisiert

---

## [1.3.6] — 2026-02-25

### UX-Verbesserungen

- **Denk-Indikator**: Zeigt jetzt aktives Tool (z.B. `get_flights_nearby`) und Live-Lognachricht direkt hinter den drei Punkten an
- **Kopieren-Button**: Jede Chat-Nachricht hat einen Kopieren-Button (zwei Quadrate) — base64-Bilder werden dabei durch `[Bild]` ersetzt
- **Provider-Test**: Neben „Speichern" gibt es bei jedem Provider einen „Verbindung testen"-Button der die Modellliste abruft (Anzahl + Namen)
- **SSH-Tunnel-Guide**: In den Einstellungen bei Ollama und LM Studio erscheint eine Anleitung zum SSH-Reverse-Tunnel inkl. dynamisch ermittelter Server-IP (via ipify.org) und vollständiger sshd_config-Voraussetzungen (`AllowTcpForwarding yes`, `GatewayPorts yes`)
- **Agenten-Formular**: Feldbezeichnungen (Name, Kurzbeschreibung, System-Prompt) stehen jetzt sichtbar über den Eingabefeldern
- **LLM-Kontext**: base64-Bilder aus eigenen Nachrichten werden vor dem Senden an das LLM entfernt (reduziert Token-Verbrauch)

---

## [1.3.5] — 2026-02-25

### Flugkarte (`get_flights_nearby` + `show_map`)
- Neuer optionaler Parameter `show_map: true` in `get_flights_nearby`
- Rendert eine OpenStreetMap-Karte mit allen Flugzeugen als PNG (kein API-Key nötig)
- Roter Punkt = Suchmittelpunkt, blaue Punkte = Flugzeuge in der Luft, graue Punkte = am Boden
- Callsigns werden direkt auf der Karte beschriftet
- Zoom-Level wird automatisch aus dem Suchradius berechnet
- Nutzt `staticmap` Bibliothek (OSM-Tile-Server)

---

## [1.3.4] — 2026-02-25

### Callsign-Tool (`resolve_callsign`)
- Neues Built-in MCP Tool: Flugzeug-Rufzeichen auflösen (z.B. `DLH1MH` → Lufthansa)
- Airline-Lookup via OpenFlights `airlines.dat` (ICAO-Code → Name, Land, IATA, Rufzeichen-Klartextname) — gecacht in `/app/data/`
- Live-Daten via adsb.one (kein API-Key): Position, Höhe, Geschwindigkeit, Kurs, Squawk — falls Flugzeug gerade in der Luft
- Graceful Fallback wenn Flugzeug am Boden oder Callsign unbekannt

---

## [1.3.3] — 2026-02-25

### Geocoding-Tool (`geocode_location`)
- Neues Built-in MCP Tool: Geokoordinaten (Breitengrad/Längengrad) für Postleitzahlen, Ortsnamen und Adressen
- Nutzt OpenStreetMap Nominatim — kostenlos, kein API-Key nötig, weltweit
- Gibt beste Übereinstimmung + weitere Treffer zurück (Postleitzahl, Ort, Bundesland, Land)
- Logging im Guenther-Terminal

### Flugdaten-Tool (`get_flights_nearby`)
- Neues Built-in MCP Tool: Live-Flugzeuge in einem Radius um beliebige Geokoordinaten
- Nutzt OpenSky Network ADS-B Daten — kostenlos, kein API-Key nötig
- Zeigt Callsign, Herkunftsland, Höhe (m + ft), Geschwindigkeit, Kurs, Vertikalrate
- Sortierung nach Entfernung, konfigurierbarer Radius (max. 500 km) und Ergebnislimit
- Tipp: Kombination mit `geocode_location` → PLZ eingeben → Koordinaten → Flüge

---

## [1.3.2] — 2026-02-23

### Aktienkurs-Tool (`get_stock_price`)
- Neues Built-in MCP Tool: aktueller Kurs, Tagesveränderung, Hoch/Tief, 52-Wochen-Range, Marktkapitalisierung und Volumen
- Kein API-Key nötig (Yahoo Finance via `yfinance`)
- Weltweit: US-Aktien (`AAPL`, `NVDA`), Deutsche Aktien (`BMW.DE`, `SAP.DE`), Indizes (`^DAX`, `^SPX`), Krypto (`BTC-USD`)
- Logging im Guenther-Terminal

---

## [1.3.1] — 2026-02-23

### Light/Dark Theme
- **Theme-Toggle** in der Titelleiste: kleiner `LIGHT`/`DARK`-Button oben rechts
- Auswahl wird in `localStorage` gespeichert und nach Reload wiederhergestellt
- **Light-Theme**: heller Grau-Blau-Hintergrund, dunkler Text, tieferes Blau als Akzent
- **Dark-Theme**: wie gehabt (dunkles Blau/Violett)
- Titelleiste und Sidebar folgen dem gewählten Theme
- Guenther-Terminal bleibt in beiden Themes schwarz mit grünem Text

---

## [1.3.0] — 2026-02-22

### Agenten-System
- Neue Sektion in Einstellungen → **Agenten**: Agenten mit eigenem System-Prompt anlegen, bearbeiten, löschen
- Beim Start eines neuen Chats erscheint ein **Agent-Picker-Dropdown** (nur wenn Agenten vorhanden)
- Der Agenten-Name wird im Chat statt "Guenther" angezeigt (Nachrichten + Typing-Indicator)
- Chat-Liste zeigt **farbiges Badge** mit Agenten-Namen beim jeweiligen Chat
- `agent_id` wird in der SQLite-Tabelle `chats` gespeichert (Auto-Migration)
- Backend: `GET/POST /api/agents`, `PUT/DELETE /api/agents/<id>`, Agenten-Config in `agents.json`

### Code-Interpreter Tool (`run_code`)
- Neues Built-in MCP Tool: generiert Python-Code via LLM, führt ihn in isoliertem Temp-Verzeichnis aus
- Ideal für Datenkonvertierung (CSV→JSON, JSON→XML usw.), Web-Scraping, Analysen und Berechnungen
- Eingabedaten werden via stdin übergeben; beliebige pip-Pakete erlaubt (requests, pandas, bs4 usw.)
- **venv-Isolation**: Abhängigkeiten werden automatisch in einer temporären venv installiert
- **Selbstkorrektur-Loop**: Bei leerem oder fehlerhaftem Output schickt das Tool Code + Problem zurück ans LLM (bis zu 2 Korrekturversuche)
- **User-Agent**: LLM wird explizit angewiesen, bei HTTP-Anfragen immer einen realistischen Browser-User-Agent zu setzen
- Timeout: 60 Sekunden; Temp-Verzeichnis wird immer aufgeräumt (try/finally)
- Optional: separates Code-Generierungs-Modell in Tool-Einstellungen konfigurierbar
- Vollständiges Terminal-Logging: LLM-Prompt, generierter Code, Ausführungs-Output, Fehler

### Datei-Upload im Chat
- **📎 Button** neben dem Eingabefeld öffnet Datei-Auswahl (CSV, JSON, XML, TXT, TSV, YAML, LOG)
- FileReader liest Inhalt client-seitig; blauer Badge zeigt Dateiname (mit ✕ zum Entfernen)
- Dateiinhalt wird beim Senden in den Message-Kontext eingefügt — LLM kann ihn an `run_code` übergeben
- Senden-Button auch ohne Text aktiv wenn Datei angehängt

### Hilfe-System erweitert
- `get_help` kennt zwei neue Topics: `code` (run_code-Tool-Doku) und `agents` (Agenten-System)
- `general`-Hilfe ergänzt um: Agenten-System, Datei-Upload, `run_code`-Hinweis
- `tools`-Hilfe: `text_to_speech` und `run_code` ergänzt

---

## [1.2.0] — 2026-02-22

### ElevenLabs Text-to-Speech
- Neues `text_to_speech` MCP-Tool: wandelt Text in Sprache um via ElevenLabs API
- Konfigurierbar in Settings → Tools: API Key, Voice ID, Modell (z.B. `eleven_multilingual_v2`)
- Audio wird als Base64 data-URI in die Antwort eingebettet und direkt im Chat abgespielt
- `<audio>`-Player mit `autoplay` — startet automatisch nach Tool-Aufruf

### Spracheingabe per Mikrofon (Web GUI)
- Mikrofon-Button neben dem Senden-Button (nur in Browsern mit Web Speech API, z.B. Chrome/Edge)
- Pulsierender roter Ring + springende Punkte als Aufnahme-Visualisierung
- Transkript fließt live ins Eingabefeld; nach Ende der Aufnahme springt Fokus ins Textfeld
- Sprache: `de-DE`; funktioniert nur auf `https://` oder `localhost` (Browser-Einschränkung)
- Fix: Recognition wird beim Absenden gestoppt, damit das Eingabefeld leer bleibt

### TTS via Telegram
- Wenn `text_to_speech` von Telegram aus aufgerufen wird, schickt der Bot das Audio via `sendAudio` zurück
- Erscheint als abspielbares MP3 direkt in der Telegram-App

### Bildgenerierung verbessert
- Fix: API-Response-Parsing korrigiert (`image_url.url` statt `url`)
- Bildgenerierungs-Request und Response-Größe werden im Terminal geloggt
- `agent_overridable=False` für `generate_image`: Provider/Modell-Override wird in der UI ausgeblendet
- Tool-Schema-Key umbenannt: `model` → `image_model`

### Konfigurierbarer Timeout
- Globaler LLM-Timeout in Settings konfigurierbar (`llm_timeout`, Standard: 120s)
- Jedes Tool kann eigenen Timeout setzen (Feld `timeout` im Tool-Settings-Schema)

---

## [1.1.0] — 2026-02-22

### Settings-Redesign + Multi-Provider Support
- **Vollbild-Settings-Panel** mit Sidebar-Navigation (Allgemein / Provider / Tools / MCP / Telegram) — ersetzt das alte Popup-Modal
- **Multi-Provider-Unterstützung**: OpenRouter, Ollama, LM Studio — alle OpenAI-API-kompatibel
  - Jeder Provider hat eigene Base URL, API Key, Enabled-Toggle
  - Standard-Provider frei wählbar
- **Pro-Tool Provider+Modell-Override**: Jedes Tool kann einen eigenen Provider + Modell verwenden; wenn alle ausgewählten Tools übereinstimmen, wird der Override aktiviert
- **Tool-Accordion** in den Einstellungen: Tool-Einstellungen inline aufklappbar, kein Popup mehr
- **Versionsnummer** in der Topbar: `v1.1.0` + Git-Short-Hash (lokal), `v1.1.0` (Docker-Build ohne git)

### Technisch
- `config.py`: `providers`-Dict + `default_provider` in DEFAULT_SETTINGS; Auto-Migration von `openrouter_api_key`
- `openrouter.py`: `call_openrouter()` hat `base_url` Parameter
- `agent.py`: Provider-Auflösung aus Settings; `_pick_provider_and_model_for_tools()`
- `routes/settings.py`: `GET/PUT /api/providers/<id>` Endpoints; API-Keys maskiert
- `app.py`: `_MODEL_OVERRIDE_FIELD` entfernt; `list_mcp_tools()` gibt `current_provider`/`current_model`/`settings_schema` zurück
- `vite.config.js`: `__APP_VERSION__` via `define` zur Build-Zeit injiziert

---

## [1.0.x] — 2026-01 bis 2026-02

### Temperatur & Terminal-Clear (137e9b7)
- Temperatur-Dropdown in den Einstellungen (0.1 / 0.5 / 0.8)
- CLS-Button im Guenther-Terminal zum Leeren der Logs

### Wikipedia-Tool (1cf39a5 – 4eba6d9)
- Neues `wikipedia_search` MCP-Tool: sucht Wikipedia-Artikel auf Deutsch
- Verbesserte Relevanz-Erkennung: Redirect-Detection, Scoring, Volltext-Fallback wenn Intro leer

### Per-Tool Modell-Override (3ba1cfe)
- Jedes Tool kann ein eigenes OpenRouter-Modell verwenden (z.B. günstiges Modell für einfache Tools)
- Override nur aktiv wenn alle ausgewählten Tools dasselbe Modell wollen

### Weather-Tool (8580c08)
- `get_weather` MCP-Tool via Open-Meteo API (kostenlos, kein Key nötig)
- Gibt Temperatur, Wetterlage, Wind für beliebige Stadt zurück

### Bildverarbeitung + Telegram-Bilder (2bb642e)
- `process_image` Tool: empfängt Bilder aus Telegram, verarbeitet via ImageMagick
- `generate_image` Tool: Bildgenerierung via OpenRouter (z.B. FLUX, Gemini)
- Telegram: QR-Codes, text_to_image und generierte Bilder werden als echte Fotos gesendet

### Voice Input + STT/TTS (21d42ad)
- Spracheingabe im Chat via Browser-Mikrofon (MediaRecorder API)
- Speech-to-Text: wahlweise via OpenRouter (multimodal) oder OpenAI Whisper
- Whisper-Integration als zuverlässigeres STT-Backend mit eigenem API Key

### Telegram Gateway (89567d1)
- Telegram-Bot als Eingangskanal (Polling, kein Webhook nötig)
- Whitelist: nur freigeschaltete Usernames dürfen schreiben
- `/new <Name>` zum Starten neuer Chat-Sessions
- Bilder werden als `sendPhoto` übermittelt

### Weitere Fixes & Verbesserungen
- Fehler-Reporting: OpenRouter-Fehlermeldungen werden aus dem JSON-Body extrahiert (statt HTTP-Status)
- Base64-Bild-Regex robuster (`[^)]+` statt strikter Zeichenklasse)
- `ToolSettings`-Modal: korrekte Input-Borders und Trennlinie
- `get_help` Tool: alle aktuellen Features dokumentiert, Wikipedia-Abschnitt ergänzt

---

## [1.0.0] — 2026-01 (80d99e7)

### Initiales Release
- Flask-Backend + React-Frontend als Docker-Container
- Chat-Interface mit OpenRouter LLM-Anbindung
- Guenther-Terminal (DOS-Box-Optik) mit JSON-Syntax-Highlighting und Einklappmöglichkeit
- MCP-Tool-System mit 10 Built-in-Tools:
  - `get_current_time`, `roll_dice`, `calculate`, `generate_password`
  - `text_to_image` (Pillow), `generate_qr_code`
  - `fetch_website_info`, `send_email` (SMTP)
  - `list_available_tools`, `get_help`
- Tool-Router (Pre-Filter): LLM wählt relevante Tools vor dem Agent-Loop aus
- Externe MCP-Server via stdio (JSON-RPC 2.0) anbindbar
- Bild-Rendering im Chat (Base64 data URIs)
- Tool-spezifische Einstellungen mit generischem Schema-System
- SQLite-Persistenz für Chats + Messages
- Docker-Volume für Settings + DB
- Resizable Guenther-Terminal
