# Changelog

## [1.4.45] — 2026-03-06

### Trello Tool

- **`trello`**: Neues Built-in MCP Tool fuer Trello
- Aktionen: `get_boards`, `get_lists`, `get_cards`, `get_card` (mit Checklisten), `create_card`, `update_card`, `move_card`, `create_list`, `add_comment`, `archive_card`
- API Key + Token in Tool-Einstellungen konfigurierbar
- Kein zusaetzliches Package noetig (nutzt `requests`)

---

## [1.4.44] — 2026-03-06

### MongoDB Tool

- **`mongodb`**: Neues Built-in MCP Tool fuer MongoDB (lokal und Atlas)
- Aktionen: `find` (mit Filter, Projektion, Sortierung), `insert`, `update` (one/many), `delete` (one/many), `count`, `list_collections`, `aggregate` (Pipeline)
- Connection String + Datenbankname in Tool-Einstellungen konfigurierbar
- Unterstuetzt MongoDB-Filter-Syntax (`$gte`, `$regex`, `$in`, etc.) und Aggregation-Pipelines
- ObjectId und datetime werden automatisch zu Strings serialisiert
- `pymongo` in `requirements.txt` ergaenzt

---

## [1.4.43] — 2026-03-06

### PostgreSQL Tool

- **`postgresql`**: Neues Built-in MCP Tool fuer PostgreSQL-Datenbanken
- Aktionen: `query` (SELECT), `execute` (INSERT/UPDATE/DELETE/DDL), `list_tables`, `describe_table`, `count_rows`
- Verbindungsdaten (Host, Port, Datenbank, Benutzer, Passwort, SSL-Modus) in Tool-Einstellungen konfigurierbar
- Schema-Parameter fuer `list_tables` und `describe_table` (Standard: `public`)
- Sicherheits-Check: `query` erlaubt nur lesende Statements
- `psycopg2-binary` in `requirements.txt` ergaenzt

---

## [1.4.42] — 2026-03-06

### MySQL / MariaDB Tool

- **`mysql`**: Neues Built-in MCP Tool fuer MySQL/MariaDB-Datenbanken
- Aktionen: `query` (SELECT), `execute` (INSERT/UPDATE/DELETE/DDL), `list_tables`, `describe_table`, `count_rows`
- Verbindungsdaten (Host, Port, Datenbank, Benutzer, Passwort) in Tool-Einstellungen konfigurierbar
- Sicherheits-Check: `query` erlaubt nur lesende Statements (SELECT/SHOW/EXPLAIN/DESC)
- Automatisches LIMIT (max. 500 Zeilen) bei SELECT-Abfragen
- Verwendet `PyMySQL` (pure Python, keine native Abhaengigkeit)
- `PyMySQL` in `requirements.txt` ergaenzt

---

## [1.4.41] — 2026-03-06

### Airtable Tool

- **`airtable`**: Neues Built-in MCP Tool fuer Airtable-Bases
- Aktionen: `get_records` (Datensaetze abrufen, filterbar per Formel), `create_record`, `update_record`, `delete_record`, `count_records` (paginiert), `list_fields`
- API Key (Personal Access Token) in Tool-Einstellungen konfigurierbar
- Base ID und Tabellenname als Parameter pro Aufruf
- Unterstuetzt Airtable-Formeln fuer Filter (z.B. `AND({Status}='aktiv', {Land}='DE')`)
- Unterstuetzt Sortierung nach Feld und Richtung

---

## [1.4.40] — 2026-03-05

### YouTube Transcript Tool

- **`get_youtube_transcript`**: Neues Built-in MCP Tool zum Abrufen von YouTube-Transkripten
- Kein API Key erforderlich — nutzt `youtube-transcript-api` direkt
- Akzeptiert vollständige YouTube-URLs (youtube.com/watch, youtu.be, embed) oder reine Video-IDs
- Bevorzugte Sprachen konfigurierbar in Tool-Einstellungen (Standard: `de,en`), automatischer Fallback auf jede verfügbare Sprache
- Gibt Transkripttext, Segment-Anzahl, Wortanzahl und erkannte Sprache zurück

---

## [1.4.39] — 2026-03-05

### Mastodon Built-in Tool

- **`post_mastodon`**: Neues Built-in MCP Tool zum Posten auf Mastodon via REST API
- Nur 2 Felder: Instanz-URL + Access Token (kein OAuth-Overhead)
- Nutzt `requests` statt `mastodon.py` — keine extra Dependency
- Toot wird auf 500 Zeichen gekürzt falls nötig; gibt Post-ID und URL zurück
- Sprechende Fehler für 401 (Token ungültig) und 403 (fehlende Schreibrechte)

---

## [1.4.38] — 2026-03-05

### Bluesky Built-in Tool

- **`post_bluesky`**: Neues Built-in MCP Tool zum Posten auf Bluesky (AT Protocol)
- Authentifizierung via Handle + App-Passwort (kein OAuth-Overhead)
- Hashtags werden automatisch als klickbare Facets (byte-genaue UTF-8-Offsets) verlinkt
- Beitrag wird auf 300 Zeichen gekürzt falls nötig; gibt Post-URI und URL zurück
- Nur 2 Felder in den Tool-Einstellungen nötig; kein Proxy erforderlich

---

## [1.4.37] — 2026-03-05

### Twitter/X Built-in Tool

- **`post_tweet`**: Neues Built-in MCP Tool zum Posten von Tweets via Twitter/X API v2
- OAuth 1.0a Signatur vollständig in Python ohne externe Libraries implementiert
- **4 konfigurierbare API-Schlüssel** (`api_key`, `api_secret`, `access_token`, `access_token_secret`) erscheinen automatisch als Passwortfelder in den Tool-Einstellungen via `SETTINGS_SCHEMA`
- Hilfetexte und Links zum Twitter Developer Portal direkt in `SETTINGS_INFO`
- Tweet wird auf 280 Zeichen gekürzt falls nötig; gibt Tweet-ID und URL zurück

---

## [1.4.36] — 2026-03-01

### Audio-Workflow + Tool-Fehler sichtbar + Hilfe überarbeitet

**Audio-Konvertierung & Versand**
- **`send_telegram`**: neuer optionaler Parameter `file_path` — sendet Audiodateien (MP3, WAV, OGG, FLAC, M4A, AAC, Opus) direkt per Telegram mit korrektem MIME-Type und Dateinamen
- **`[LOCAL_FILE]`-Marker**: Custom Tools können Dateien lokal speichern und `[LOCAL_FILE](/pfad)` zurückgeben — Backend liest die Datei, legt sie im Chat-Ordner ab und zeigt einen Download-Button; Dateiinhalt gelangt nie ans LLM
- **`ffmpeg` + `pydub`** im Docker-Image: Voraussetzung für Audio-Konvertierungstools
- **Binär-Upload via REST**: Binärdateien (Audio, Office) werden per `POST /api/upload` hochgeladen statt als Base64 via Socket.IO — kein stilles Verwerfen mehr bei Dateien >1 MB

**Tool-Ladefehler sichtbar**
- Schlägt ein Custom Tool beim Import fehl (z.B. fehlende Python-Library), erscheint `⚠ Tool-Ladefehler (custom/name): ...` direkt im Guenther-Terminal beim Browser-Connect
- Nach einem Reload (`/api/mcp/reload`) werden veraltete Fehlermeldungen bereinigt — behobene Tools zeigen keine alten Warnungen mehr

**Hilfe überarbeitet (Einstellungen → Hilfe)**
- Alle Sektionen jetzt **aufklappbar** (Accordion), nach Themen-Gruppen sortiert: *Provider & Modelle / Tools & Erweiterungen / Automatisierung & Integrationen*
- Neue Sektion: **Custom Tools — Dateien ausgeben** mit vollständiger Erklärung des `[LOCAL_FILE]`-Musters und einer **Prompt-Vorlage** zum direkten Einfügen in den Chat
- Neue Sektion: **Datei-Upload im Chat** (Text vs. Binär, unterstützte Formate, Serverpfad)
- `get_help` Tool: neue Topics `file_upload` und `local_file`

---

## [1.4.35] — 2026-03-01

### Datei-Upload: Binärdateien + Office-Formate

- **Audio-Upload**: MP3, WAV, OGG, FLAC, M4A, AAC, OPus werden als Binärdatei erkannt, als Data-URL gelesen und serverseitig in `/app/data/uploads/` gespeichert — LLM erhält den lokalen Dateipfad
- **Office-Upload**: XLS, XLSX, DOC, DOCX ebenfalls als Binär-Upload (gleiches Handling) — MCP-Tools können auf den Pfad zugreifen
- **Telegram Audio**: `_extract_audio` gibt nun `(bytes, mime_type, filename)` zurück; `_send_audio` verwendet korrekte MIME-Type + Dateinamen statt hartcodiertem `voice.mp3 / audio/mpeg`
- **Icons**: Audio = 🎵, Office-Dokumente = 📄, Text = 📎 (im Anhang-Badge + Chat-Nachricht)

---

## [1.4.34] — 2026-03-01

### Deployment-Fix: rsync --delete

- rsync-Befehl im Deploy-Workflow um `--delete` ergänzt — entfernt veraltete Dateien/Verzeichnisse auf dem Server, die lokal nicht mehr existieren
- Ohne `--delete` blieben alte Tool-Verzeichnisse (`create_tool/`, `edit_tool/`, diverse `*_tool.py`) dauerhaft auf dem Server und wurden ins Docker-Image gebacken

---

## [1.4.33] — 2026-03-01

### `build_mcp_tool` — SyntaxError behoben

- **Root cause**: `USAGE = """..."""` im gen-Prompt und `"""Docstring"""` in `_FlexMod` (test_runner) beendeten den äußeren `f"""..."""`-String vorzeitig → SyntaxError beim Import
- Tool war seit v1.4.29 (Einführung der USAGE-Konstante) **nie ladbar** — durch noch vorhandene alte `create_tool/`-Verzeichnisse auf dem Server bisher unbemerkt
- Fix: `"""` → `'''` im Prompt-Beispiel, Docstring → `# Kommentar` im test_runner

---

## [1.4.32] — 2026-03-01

### `build_mcp_tool` — Max. Korrektur-Loops konfigurierbar

- Neues Einstellungsfeld **„Max. Korrektur-Loops"** in Einstellungen → MCP Tools → `build_mcp_tool`
- Leer lassen = 15 (Standard); z.B. `5` für einfache Tools, `25` für komplexe
- Wert wird beim Start im Guenther-Terminal geloggt: `Modell: … | Max. Loops: …`

---

## [1.4.31] — 2026-03-01

### Markdown-Tabellen im Chat

- `remark-gfm` Plugin für ReactMarkdown installiert → GFM-Tabellen, Strikethrough, etc. werden korrekt gerendert
- CSS für `.message-content table/th/td`: Rahmen, Padding, alternierende Zeilenfarben (dark + light Theme)

---

## [1.4.30] — 2026-03-01

### Stop-Button für laufende Generierung

- **Stop-Button** erscheint im Chat während `isLoading=true` — ersetzt den Senden-Button
- Klick sendet `cancel_generation` via WebSocket ans Backend
- Backend: `threading.Event` pro SID in `_cancel_flags` — wird in `run_agent()` zwischen Iterationen und nach Tool-Calls geprüft
- Bei Abbruch: kein `assistant`-Eintrag gespeichert, `agent_end` mit `cancelled: True` emittiert
- Styling: `.btn-stop` in App.css (rot, analog zu `.btn-send`)
- i18n: `chat.stop` in DE (`Stopp`) + EN (`Stop`)

---

## [1.4.29] — 2026-03-01

### `build_mcp_tool` — Plan-Phase + Verifikation

- **Phase 0 — Plan**: vor der Code-Generierung erstellt das LLM einen strukturierten Plan (Tool-Name, Parameter, Libraries, Handler-Signatur, Vorgehensweise) und gibt ihn in der Guenther-Console aus
- **Plan als Leitfaden**: der generierte Plan wird als Kontext an die Code-Generierung übergeben — konsistentere Ergebnisse, weniger Fehlläufe
- **Phase 5 — Plan-Verifikation**: nach dem Deploy wird geprüft ob Tool-Name, Handler-Signatur und Libraries dem Plan entsprechen (✓/⚠/~ pro Punkt in der Console)
- Bessere Sichtbarkeit in der Console: jede Phase klar beschriftet, Plan-Output mit allen Details vor der Code-Generierung

---

## [1.4.27] — 2026-03-01

### `build_mcp_tool` — Intelligenter Tool-Builder mit LLM + venv + Selbstkorrektur

`create_mcp_tool` und `edit_mcp_tool` wurden durch ein einzelnes, deutlich mächtigeres Tool ersetzt:

- **Natürlichsprachliche Beschreibung** → vollständiger `tool.py`-Code per LLM
- **Venv-Test-Loop**: Code wird in einer isolierten venv getestet — openguenther-interne Imports werden gemockt
- **Selbstkorrektur**: bei pip-Fehlern, Import-Fehlern oder Strukturproblemen wird der Code + Fehlermeldung ans LLM zurückgegeben → Korrektur → erneut testen (max. 15 Iterationen)
- **Auto-pip-Install**: benötigte Pakete werden nach erfolgreichem Test automatisch ins System-Python installiert
- **Edit-Modus**: wenn `tool_name` eines bestehenden Custom Tools angegeben wird, wird der bestehende Code als Kontext mitgeschickt
- **`create_mcp_tool` + `edit_mcp_tool` entfernt** (ersetzt durch `build_mcp_tool`)

---

## [1.4.26] — 2026-03-01

### Custom Tools: ZIP Download & Upload

**ZIP-Download einzelner Custom Tools**
- Jedes installierte Custom Tool kann als ZIP-Datei heruntergeladen werden (Backup / Teilen)
- Neuer Abschnitt „Custom Tools" ganz unten in Einstellungen → MCP Tools
- Download-Button pro Tool → ZIP mit `<name>/tool.py` und allen Dateien im Tool-Ordner

**ZIP-Upload / Installation von Custom Tools**
- „ZIP Upload"-Button öffnet Dateiauswahl (`.zip`)
- Vor dem Upload erscheint ein obligatorischer Sicherheits-Warndialog — Upload nur nach Bestätigung
- Sicherheits-Prüfung: alle ZIP-Member werden auf Path-Traversal (`../`) und Absolut-Pfade geprüft
- `tool.py` muss im ZIP vorhanden sein, sonst Fehler
- Tool wird nach `/app/data/custom_tools/<name>/` installiert (bestehende Version wird überschrieben)

**Neue Endpoints**
- `GET /api/custom-tools` — Liste aller installierten Custom Tools
- `GET /api/custom-tools/<name>/download` — ZIP-Download eines Tools
- `POST /api/custom-tools/upload` — ZIP-Upload + Installation

---

## [1.4.25] — 2026-03-01

### Tool-Einstellungen: Beschreibungen + Export-Sicherheit

**MCP-Tool-Beschreibungen immer sichtbar**
- Beim Aufklappen eines Tools wird jetzt immer eine Beschreibung angezeigt — entweder die detaillierte `SETTINGS_INFO` (für konfigurierbare Tools wie Pinecone, TTS, E-Mail, etc.) oder als Fallback der kurze Tool-Beschreibungstext
- Beschreibungen werden als **Markdown** gerendert (fett, Links, Listen)
- Kurztext verschwindet beim Aufklappen nicht mehr

**MCP-Server-Export: keine API-Keys**
- Beim JSON-Export von MCP-Servern werden Env-Variablen-Werte geleert (API-Keys bleiben nicht im Export)
- Variablen-Namen bleiben erhalten als Hinweis, welche Env-Vars beim Import gesetzt werden müssen

---

## [1.4.24] — 2026-03-01

### Tool-Beschreibungen in Einstellungen + JSON Export/Import

**Tool-Beschreibungen (SETTINGS_INFO)**
- Jedes konfigurierbare MCP-Tool kann jetzt eine Beschreibung in den Einstellungen anzeigen — erscheint als Info-Box wenn das Tool aufgeklappt wird
- `SETTINGS_INFO`-Konstante in `tool.py` — vom Loader automatisch erkannt, via API übertragen, im Frontend angezeigt
- Hinweise mit API-Key-Links und Modell-Empfehlungen für: Pinecone, TTS (ElevenLabs), E-Mail, Präsentationen, Bildgenerierung, Code-Interpreter

**JSON Export/Import für Agenten, Autoprompts und MCP-Server**
- Agenten, Autoprompts und externe MCP-Server können jetzt als JSON exportiert und importiert werden
- Export-Button im jeweiligen Einstellungs-Bereich → lädt Datei mit Zeitstempel herunter
- Import-Button öffnet Dateiauswahl → importiert alle gültigen Einträge (neue UUIDs, Namens-Deduplication mit „(importiert)")
- Envelope-Format: `{"type": "openguenther_*", "version": 1, "exported_at": "...", "data": [...]}`
- Versionsnummer wird beim Import geprüft — neuere Versionen werden abgelehnt (Vorwärts-Kompatibilitätsschutz)
- Neue Endpoints: `GET/POST /api/agents/export|import`, `GET/POST /api/autoprompts/export|import`, `GET/POST /api/mcp-servers/export|import`

---

## [1.4.23] — 2026-03-01

### Per-Chat LLM-Nutzungsstatistik

- Das Chat-Info-Popup (📊) zeigt jetzt die Nutzungsstatistik **nur des aktuell geöffneten Chats** — statt globaler Daten
- `usage_log`-Tabelle bekommt eine `chat_id`-Spalte (Migration, ältere Einträge haben `NULL`)
- Alle LLM-Aufrufe (Chat, Telegram, Webhooks, Autoprompts) schreiben die `chat_id` mit — via Thread-lokalem Kontext, ohne tiefe Parameteränderungen
- Neuer Endpoint `GET /api/chats/<id>/usage` für Chat-spezifische Statistiken
- Globale Nutzungsstatistik weiterhin verfügbar unter Einstellungen → LLM Provider

---

## [1.4.22] — 2026-03-01

### Chat-Info-Popup, Pinecone-Tool, CSS-Fixes, MCP-Tool-Sektionen

**Chat-Info-Popup**
- Das 📊-Popup in der Topbar zeigt jetzt Chat-Informationen statt nur Nutzungsstatistiken
- Angezeigt: Chat-ID (mit Kopier-Button), Titel, Erstellungs- und Änderungsdatum, Nachrichten-Anzahl (User/Assistent), aktiver Agent, vorhandene Dateien (mit Download-Link)
- LLM-Nutzungsstatistik bleibt erhalten und wird darunter angezeigt
- Wenn kein Chat geöffnet ist: entsprechender Hinweis

**Pinecone Vector-DB MCP-Tool**
- Neues eingebautes MCP-Tool zur Verwaltung einer Pinecone Vector-Datenbank
- Aktionen: `list_indexes`, `create_index`, `describe_index`, `delete_index`, `upsert`, `query`, `delete_vectors`
- Upsert und Query unterstützen automatisches Text-Embedding über den konfigurierten Provider
- Konfigurierbar: Pinecone API-Key, Embedding-Modell; Provider- und Modell-Override per Agent

**MCP-Tools: Getrennte Bereiche Built-in / Extern**
- MCP-Tools-Einstellungen zeigen Built-in- und externe Tools jetzt in zwei separaten Sektionen
- Jede Sektion ist alphabetisch sortiert
- Typ-Badge (Built-in/Extern) entfernt, da durch Sektionsüberschrift ersetzt
- Hinweis in MCP-Server-Einstellungen: externe Tools erscheinen nach dem Laden unter „MCP Tools"

**CSS-Fixes Settings**
- Alle `<select>`-Elemente in `.settings-section` werden jetzt automatisch einheitlich gestylt (betrifft Autoprompts, Agenten, Telegram, MCP)
- Alle `<textarea>`-Elemente in `.settings-section` erhalten einheitliches Styling — Inline-Styles in SettingsTelegram entfernt
- `input[type="time"]` (Autoprompts Zeitplanung) und `input[type="number"]`/`[type="password"]` in `.tool-field-row` (MCP-Tool-Einstellungen) korrekt gestylt

---

## [1.4.21] — 2026-03-01

### Webhook-System

- Externe Systeme können OpenGuenther jetzt per HTTP-Aufruf triggern (Home Automation, Skripte, andere Apps)
- Jeder Webhook hat einen eigenen Bearer-Token (`wh_` + 32 Hex-Zeichen, automatisch generiert)
- Optional: feste Chat-ID (Kontext bleibt erhalten) oder `null` (neuer Chat pro Aufruf)
- Optional: Agent-Zuweisung pro Webhook
- Antwort kommt synchron zurück: `{"chat_id": X, "response": "..."}`
- CRUD-API: `GET/POST /api/webhooks`, `PUT/DELETE /api/webhooks/<id>`
- Öffentlicher Trigger-Endpunkt: `POST /webhook/<id>` (kein `/api/`-Prefix)
- Fehlerbehandlung: 401 bei falschem Token, 400 bei fehlender Message, 404 bei unbekannter ID
- Einstellungen → Webhooks: Liste, Inline-Bearbeitung, cURL-Beispiel mit Kopier-Button

---

## [1.4.20] — 2026-02-28

### Eigener LLM-Provider + Modell pro Agent

- Jeder Agent kann jetzt optional einen eigenen Provider und ein eigenes Modell verwenden — unabhängig von der globalen Standard-Einstellung
- Provider-Dropdown (nur aktive Provider) + Modell-Freitextfeld im Agenten-Formular (Einstellungen → Agenten)
- Konfigurierter Override wird als `monospace`-Badge in der Agenten-Liste angezeigt
- Priorität: Tool-Override > Agent-Override > Globale Einstellung

---

## [1.4.19] — 2026-02-28

### Externe MCP Server: npx-Support + Env-Variablen + Bugfixes

**Neue Features**
- **Umgebungsvariablen pro MCP Server**: KEY=VALUE-Paare (eine pro Zeile) direkt in den Einstellungen hinterlegen — ermöglicht API-Key-basierte MCP Server wie Firecrawl
- **Bearbeiten bestehender MCP Server**: Inline-Edit-Formular pro Server (Name, Command, Argumente, Env-Vars)
- **Node.js 20 im Docker-Image**: `npx`-basierte MCP Server (der Standard auf mcpmarket.com) funktionieren jetzt out-of-the-box
- **Reload-Button direkt in MCP Server-Einstellungen**: Tools neu laden ohne in den Tools-Tab zu wechseln
- **Externe MCP Server werden beim Container-Start automatisch geladen**
- **mcpmarket.com-Hinweis** als Infokasten in den MCP Server-Einstellungen

**Bugfixes**
- MCP Client liest jetzt alle Antwort-Zeilen bis zur passenden Request-ID — behebt "No response from MCP server" bei Servern die Notifications vor dem Ergebnis senden (z.B. Firecrawl)
- Tool-Router-Aufrufe wurden in der Nutzungsstatistik als "unknown" angezeigt — `provider_id` wird jetzt korrekt weitergegeben
- Mistral-Links in Provider-Einstellungen korrigiert und Nutzungs-Link ergänzt (`admin.mistral.ai`)
- Usage-Popup und Stats-Buttons hatten transparenten Hintergrund (`--bg-secondary` existiert nicht)

---

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
