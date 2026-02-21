# OPENguenther

**🌐 [openguenther.de](https://www.openguenther.de)**

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

## Installation auf einem Hetzner VPS (Schritt-für-Schritt für Einsteiger)

Diese Anleitung zeigt, wie du OPENguenther auf einem günstigen virtuellen Server bei Hetzner zum Laufen bringst. Du brauchst keine Linux-Vorkenntnisse — alles wird erklärt.

---

### Schritt 1 — Hetzner-Account und Server erstellen

1. Registriere dich unter **[hetzner.com/cloud](https://www.hetzner.com/cloud)**
2. Erstelle ein neues Projekt (z.B. „openguenther")
3. Klicke auf **„Server hinzufügen"** und wähle:
   - **Standort**: Frankfurt oder Nürnberg
   - **Image**: Debian 12
   - **Typ**: CX22 (2 vCPU, 4 GB RAM) reicht völlig — ca. 4 €/Monat
   - **SSH-Key**: Füge deinen öffentlichen SSH-Key ein (empfohlen) **oder** aktiviere die Root-Passwort-Option
4. Klicke auf **„Server erstellen"** — nach wenigen Sekunden hat der Server eine IP-Adresse (z.B. `123.456.789.0`)

> 💡 **SSH-Key erstellen** (falls du noch keinen hast): Auf dem Mac/Linux öffne ein Terminal und tippe `ssh-keygen -t ed25519`. Den Inhalt der Datei `~/.ssh/id_ed25519.pub` fügst du bei Hetzner ein.

---

### Schritt 2 — Mit dem Server verbinden

Öffne ein Terminal (Mac: Programme → Terminal, Windows: PowerShell oder [PuTTY](https://putty.org)) und verbinde dich:

```bash
ssh root@123.456.789.0
```

Ersetze `123.456.789.0` mit der IP-Adresse deines Servers. Beim ersten Verbinden erscheint eine Sicherheitsfrage — tippe `yes` und drücke Enter.

---

### Schritt 3 — System aktualisieren

Führe diese Befehle nacheinander aus:

```bash
apt update && apt upgrade -y
```

Das aktualisiert alle vorinstallierten Programme. Kann 1–2 Minuten dauern.

---

### Schritt 4 — Docker installieren

Docker ist das System, das OPENguenther in einer isolierten Umgebung ausführt. Installiere es mit einem einzigen Befehl:

```bash
curl -fsSL https://get.docker.com | sh
```

Warte bis die Installation abgeschlossen ist, dann überprüfe ob Docker läuft:

```bash
docker --version
```

Es sollte etwas wie `Docker version 26.x.x` erscheinen.

---

### Schritt 5 — Git installieren und Code herunterladen

```bash
apt install -y git
git clone https://github.com/ghaslbe/openguenther.git
cd openguenther
```

Jetzt befindest du dich im Projektordner.

---

### Schritt 6 — Docker-Image bauen

Dieser Befehl baut OPENguenther (dauert beim ersten Mal 3–5 Minuten):

```bash
docker build -t openguenther .
```

Du siehst viele Zeilen — das ist normal. Wenn am Ende `Successfully tagged openguenther:latest` erscheint, hat es geklappt.

---

### Schritt 7 — OPENguenther starten

```bash
docker run -d \
  --name openguenther \
  -p 3333:5000 \
  -v openguenther-data:/app/data \
  --restart unless-stopped \
  openguenther
```

Das startet OPENguenther im Hintergrund. Mit `--restart unless-stopped` startet es auch nach einem Server-Neustart automatisch wieder.

Überprüfe ob es läuft:

```bash
docker logs openguenther
```

Du solltest `Running on all addresses (0.0.0.0)` sehen.

---

### Schritt 8 — Im Browser öffnen

Öffne deinen Browser und rufe auf:

```
http://123.456.789.0:3333
```

(Ersetze `123.456.789.0` durch deine Server-IP.)

Du solltest jetzt das OPENguenther-Interface sehen! 🎉

---

### Schritt 9 — OpenRouter API Key einrichten

OPENguenther braucht einen API-Key um mit einem KI-Modell zu kommunizieren.

1. Registriere dich kostenlos unter **[openrouter.ai](https://openrouter.ai)**
2. Gehe zu **Keys** → **Create Key**
3. Kopiere den Key (beginnt mit `sk-or-v1-...`)
4. In OPENguenther: Klicke auf das **Zahnrad-Icon** (⚙️) oben links
5. Füge den Key bei **„API Key"** ein und klicke **Speichern**
6. Wähle ein Modell, z.B. `openai/gpt-4o-mini` (günstig) oder `google/gemini-2.0-flash-001` (schnell)

> 💡 **Tipp**: Bei OpenRouter kannst du ein Ausgaben-Limit setzen, damit keine unerwarteten Kosten entstehen.

---

### Schritt 10 — Fertig!

Du kannst jetzt mit OPENguenther chatten. Probiere zum Beispiel:
- *„Wie ist das Wetter in Berlin?"*
- *„Generiere ein Passwort mit 20 Zeichen"*
- *„Erstelle einen QR-Code für https://example.com"*

---

### Optionale Schritte

#### Firewall einrichten (empfohlen)

Nur Port 3333 nach außen öffnen, alles andere sperren:

```bash
apt install -y ufw
ufw allow ssh
ufw allow 3333
ufw enable
```

#### OPENguenther aktualisieren

Wenn es eine neue Version gibt:

```bash
cd openguenther
git pull
docker stop openguenther && docker rm openguenther
docker build -t openguenther .
docker run -d \
  --name openguenther \
  -p 3333:5000 \
  -v openguenther-data:/app/data \
  --restart unless-stopped \
  openguenther
```

Deine Chats und Einstellungen bleiben erhalten (sie liegen im Docker-Volume `openguenther-data`).

#### Telegram-Bot einrichten (optional)

1. Schreibe in Telegram mit **[@BotFather](https://t.me/BotFather)**: `/newbot`
2. Folge den Anweisungen und kopiere den Bot-Token
3. In OPENguenther-Einstellungen: Token eintragen, deinen Telegram-Username in die Whitelist und auf **„Gateway starten"** klicken

---

## Schnellstart (für Erfahrene)

```bash
git clone https://github.com/ghaslbe/openguenther.git && cd openguenther
docker build -t openguenther .
docker run -d --name openguenther -p 3333:5000 -v openguenther-data:/app/data --restart unless-stopped openguenther
```

Aufruf: `http://localhost:3333` — API Key in den Einstellungen eintragen.

---

### Konfiguration

Alle Einstellungen werden über das Web-Interface vorgenommen (Zahnrad-Icon ⚙️):

- **OpenRouter API Key** + Modell
- **Telegram Bot Token** + erlaubte Nutzer
- **OpenAI API Key** (optional, für Whisper Spracherkennung)
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
