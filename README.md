# OPENguenther

Ein selbst gehosteter KI-Agent mit Chat-Interface, MCP-Tool-Unterstützung und Telegram-Integration.

![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

---

## Features

- **Chat-Interface** mit Markdown-Rendering und Bilddarstellung
- **MCP-Tools** (Model Context Protocol): Wetter, Bildgenerierung, Bildbearbeitung, QR-Codes, Passwörter, Rechner, E-Mail, Webseiten-Info u.v.m.
- **Guenther-Terminal**: Live-Ansicht aller API-Kommunikation im DOS-Stil
- **Telegram-Gateway**: Chatten via Telegram, inkl. Foto- und Sprachnachrichten
- **Spracherkennung**: OpenAI Whisper oder OpenRouter-kompatible Modelle
- **Bildgenerierung**: via OpenRouter (Flux, Gemini Image, etc.)
- **Externe MCP-Server**: beliebige stdio-basierte MCP-Server anbindbar
- **Tool-Router**: automatische Vorauswahl relevanter Tools pro Anfrage

## Tech-Stack

- **Backend**: Flask 3, Flask-SocketIO, SQLite, Python 3.12
- **Frontend**: React 18, Vite 6, Socket.IO-Client
- **Container**: Docker (Multi-Stage Build)
- **LLM**: OpenRouter API (beliebiges Modell wählbar)

## Schnellstart

### Voraussetzungen

- Docker
- OpenRouter API Key → https://openrouter.ai

### Starten

```bash
docker build -t openguenther .
docker run -d \
  --name openguenther \
  -p 3333:5000 \
  -v openguenther-data:/app/data \
  --restart unless-stopped \
  openguenther
```

Aufruf im Browser: `http://localhost:3333`

### Konfiguration

Alle Einstellungen werden über das Web-Interface vorgenommen (Zahnrad-Icon):

- **OpenRouter API Key** + Modell
- **Telegram Bot Token** + erlaubte Nutzer
- **OpenAI API Key** (optional, für Whisper STT)
- **Bildgenerierungs-Modell** (optional, z.B. `black-forest-labs/flux-1.1-pro`)
- **STT-Modell** (optional, z.B. `google/gemini-2.5-flash`)

Daten werden persistent in einem Docker-Volume gespeichert (`/app/data`).

## Built-in Tools

| Tool | Beschreibung |
|------|-------------|
| `get_weather` | Wetter & Vorhersage via Open-Meteo (kein API-Key) |
| `generate_image` | Bildgenerierung via OpenRouter |
| `process_image` | Bildbearbeitung via ImageMagick (blur, grayscale, rotate, …) |
| `text_to_image` | Text als PNG rendern |
| `generate_qr_code` | QR-Code generieren |
| `fetch_website_info` | Website-Titel & Description abrufen |
| `send_email` | E-Mail via SMTP senden |
| `generate_password` | Sichere Passwörter generieren |
| `calculate` | Mathematische Ausdrücke auswerten |
| `roll_dice` | Würfeln |
| `get_current_time` | Aktuelle Uhrzeit |

---

## Disclaimer / Haftungsausschluss

> **DIE NUTZUNG DIESER SOFTWARE GESCHIEHT VOLLSTÄNDIG AUF EIGENES RISIKO.**

Diese Software wird **„wie besehen"** (as-is) ohne jegliche ausdrückliche oder stillschweigende Gewährleistung bereitgestellt. Der Autor übernimmt **keinerlei Haftung** für direkte, indirekte, zufällige, besondere oder Folgeschäden, die aus der Nutzung oder Nichtnutzung dieser Software entstehen – gleichgültig, ob diese auf Vertrag, unerlaubter Handlung oder einem anderen Rechtsgrund beruhen.

Dies umfasst insbesondere, aber nicht ausschließlich:

- Schäden durch KI-generierte Inhalte
- Kosten durch API-Nutzung bei Drittanbietern (OpenRouter, OpenAI, etc.)
- Datenverlust oder Sicherheitsvorfälle
- Schäden durch fehlerhafte Tool-Ausführungen

**Der Autor empfiehlt ausdrücklich:**
- API-Keys mit minimalen Berechtigungen und Ausgabelimits zu versehen
- Die Software nicht ohne Authentifizierung öffentlich zugänglich zu machen
- Keine sensiblen Daten in Chats einzugeben

---

## License

MIT License — Copyright (c) 2025

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

**THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.**
