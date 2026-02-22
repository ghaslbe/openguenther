# Changelog

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
