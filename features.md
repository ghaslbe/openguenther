# OPENguenther — Feature-Übersicht

> Stand: v1.3.9 (2026-02-25)

---

## Chat-Interface

- Markdown-Rendering mit Code-Highlighting
- Bilddarstellung (generierte Bilder, hochgeladene Fotos)
- Audio-Playback (TTS-Ausgabe, Telegram-Sprachnachrichten)
- HTML-Reports als iframe (z.B. SEO-Analyse direkt im Chat)
- **Kopieren-Button** auf jeder Nachricht (Zwischenablage, base64-Bilder werden durch `[Bild]` ersetzt)
- **Datei-Upload** (📎) — Bilder und Dokumente direkt im Chat hochladen
- **Spracheingabe** (Web Speech API) — Mikrofon-Button in der Eingabezeile
- **Agenten-Auswahl** — Wechsel zwischen konfigurierten Agenten per Dropdown
- **Live Tool-Anzeige** — während Guenther denkt, zeigen die drei Punkte das aktive Tool + aktuelle Lognachricht

---

## LLM & Provider

- **Multi-Provider-Support**: OpenRouter, Ollama, LM Studio oder beliebiger OpenAI-kompatibler Anbieter
- **Provider-Einstellungen**: Name, Base URL, API Key (maskiert), Enable/Disable-Toggle
- **Verbindungstest**: direkt in den Einstellungen — ruft Modellliste ab und zeigt Anzahl + Namen
- **Modelle laden**: im Standard-Modell-Feld lädt ein „Laden"-Button die verfügbaren Modelle des gewählten Providers (alphabetisch sortiert) zum Auswählen
- **SSH-Tunnel-Guide**: Anleitung für Reverse-Tunnel von lokalem Rechner zum Server (Ollama/LM Studio), inkl. dynamisch ermittelter Server-IP und vollständiger `sshd_config`-Voraussetzungen
- **Agenten-System**: beliebig viele Agenten mit eigenem Namen, Beschreibung und System-Prompt (gespeichert in `agents.json`)
- **Tool-Router**: vor jeder Anfrage wählt ein LLM-Call automatisch nur die relevanten Tools aus
- **Temperatur**: konfigurierbar (0.1 / 0.5 / 0.8)
- **LLM Timeout**: einstellbar (Standard 120 s, sinnvoll für langsame lokale Modelle)

---

## Built-in MCP Tools

| Tool | Beschreibung |
|------|-------------|
| `analyze_seo` | SEO-Analyse einer URL oder eines HTML-Codes — Score 0–100, Title/Meta/Headings/OG/JSON-LD u.v.m. als HTML-Report (iframe) + PDF-Download |
| `get_stock_price` | Aktienkurs, Tagesveränderung, Kennzahlen via Yahoo Finance (kein API-Key) |
| `get_flights_nearby` | Live-Flugzeuge in der Nähe von Koordinaten via OpenSky Network ADS-B (kein API-Key); optional Karte als Bild |
| `geocode_location` | Geokoordinaten für PLZ, Ortsnamen oder Adressen via OpenStreetMap Nominatim (kein API-Key) |
| `resolve_callsign` | Flugzeug-Rufzeichen auflösen: Airline-Name via OpenFlights + Live-Daten via adsb.one (kein API-Key) |
| `get_weather` | Wetter & Vorhersage via Open-Meteo (kein API-Key) |
| `generate_image` | Bildgenerierung via OpenRouter (Flux, Gemini Image etc.) |
| `process_image` | Bildbearbeitung via ImageMagick (blur, grayscale, rotate, resize, …) |
| `text_to_image` | Text als PNG rendern |
| `generate_qr_code` | QR-Code generieren |
| `send_email` | E-Mail via SMTP senden |
| `generate_password` | Sichere Passwörter generieren |
| `calculate` | Mathematische Ausdrücke auswerten |
| `roll_dice` | Würfeln |
| `get_current_time` | Aktuelle Uhrzeit |
| `wikipedia_search` | Wikipedia-Artikel abrufen |
| `text_to_speech` | Text in Sprache umwandeln (via ElevenLabs oder OpenRouter) |
| `run_code` | Python-Code in isolierter venv ausführen (Code-Interpreter, Selbstkorrektur-Loop) |

---

## Externe MCP Server

- Beliebige **stdio-basierte MCP Server** anbindbar (z.B. Filesystem, GitHub, eigene Tools)
- Konfiguration in den Einstellungen: Name, Command, Argumente, URL
- Einzeln aktivierbar/deaktivierbar
- Tools aus externen Servern erscheinen automatisch im Tool-Router

---

## Telegram Gateway

- **Text-Nachrichten** senden und empfangen
- **Fotos** senden (Bilder werden erkannt und als Telegram-Foto weitergeleitet)
- **Sprachnachrichten** (Voice): Transkription via OpenAI Whisper oder OpenRouter STT
- **TTS-Ausgabe**: Antworten als Audio-Datei via Telegram
- **PDF-Dokumente**: SEO-Reports werden automatisch als `seo-report.pdf` mitgeschickt
- **Nutzerverwaltung**: Whitelist erlaubter Telegram-User-IDs
- Start/Stop/Restart in den Einstellungen

---

## Sprache (STT / TTS)

- **STT im Browser**: Web Speech API (kein API-Key, läuft lokal im Browser)
- **STT via OpenAI Whisper**: zuverlässiger für Audio aus Telegram (`whisper-1`)
- **STT via OpenRouter**: beliebiges multimodales Modell (z.B. `google/gemini-2.5-flash`)
- **TTS**: Text-to-Speech via ElevenLabs oder OpenRouter-kompatible Modelle

---

## UI & Bedienung

- **Light/Dark Theme**: Toggle in der Titelleiste, Auswahl wird in `localStorage` gespeichert
- **Guenther-Terminal**: Live-Ansicht aller API-Kommunikation im DOS-Stil (Prompts, Tool Calls, Responses)
- **Einstellungen-Panel** mit Sidebar-Navigation: Allgemein, Agenten, LLM Provider, MCP Tools, MCP Server, Telegram, Hilfe, Info
- **Chat-Verwaltung**: Chats erstellen, umbenennen, löschen; Verlauf in SQLite

---

## Deployment & Infrastruktur

- **Docker**: Multi-Stage Build (Node für Frontend, Python 3.12-slim für Backend)
- **Persistenz**: `/app/data/` Volume für `settings.json`, `agents.json`, `db.sqlite`, gecachte Dateien
- **Flask + Flask-SocketIO** Backend, **React 18 + Vite** Frontend
- **Self-hosted**: läuft auf jedem Linux-Server (getestet auf Hetzner CX22, ca. 4 €/Monat)
- **Kein Cloud-Zwang**: mit Ollama oder LM Studio vollständig lokal betreibbar
