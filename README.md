# OPENguenther

**🌐 [openguenther.de](https://www.openguenther.de)**

> ⚠️ **Die Nutzung dieser Software geschieht vollständig auf eigenes Risiko. Der Autor übernimmt keinerlei Haftung.** Siehe [Disclaimer](#disclaimer--haftungsausschluss) unten.
>
> ⚠️ **Use of this software is entirely at your own risk. The author accepts no liability whatsoever.** See [Disclaimer](#disclaimer--haftungsausschluss) below.

Ein selbst gehosteter KI-Agent mit Chat-Interface, MCP-Tool-Unterstützung und Telegram-Integration.
A self-hosted AI agent with chat interface, MCP tool support and Telegram integration.

![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

![OPENguenther Screenshot 1](openguenther1.png)
![OPENguenther Screenshot 2](openguenther2.png)
![Telegram Integration](telegram.jpeg)

---

## Features

- **Chat interface** with Markdown rendering and image display
- **MCP Tools** (Model Context Protocol): weather, image generation, image editing, QR codes, passwords, calculator, email, website info and more
- **Guenther Terminal**: live view of all API communication in DOS style
- **Telegram Gateway**: chat via Telegram, including photos and voice messages
- **Speech recognition**: OpenAI Whisper or OpenRouter-compatible models
- **Image generation**: via OpenRouter (Flux, Gemini Image, etc.)
- **External MCP servers**: connect any stdio-based MCP server
- **Tool router**: automatic pre-selection of relevant tools per request

---

## Tech Stack

- **Backend**: Flask 3, Flask-SocketIO, SQLite, Python 3.12
- **Frontend**: React 18, Vite 6, Socket.IO-Client
- **Container**: Docker (Multi-Stage Build)
- **LLM**: OpenRouter API (any model selectable)

---

## Installation on a Hetzner VPS (Step-by-Step for Beginners)

This guide shows how to get OPENguenther running on an affordable virtual server at Hetzner. No Linux knowledge required — everything is explained.

---

### Step 1 — Create a Hetzner account and server

1. Register at **[hetzner.com/cloud](https://www.hetzner.com/cloud)**
2. Create a new project (e.g. "openguenther")
3. Click **"Add Server"** and choose:
   - **Location**: Frankfurt or Nuremberg
   - **Image**: Debian 12
   - **Type**: CX22 (2 vCPU, 4 GB RAM) is sufficient — approx. €4/month
   - **SSH Key**: paste your public SSH key (recommended) **or** enable the root password option
4. Click **"Create Server"** — within a few seconds the server will have an IP address (e.g. `123.456.789.0`)

> 💡 **Create an SSH key** (if you don't have one yet): On Mac/Linux open a terminal and type `ssh-keygen -t ed25519`. Paste the contents of `~/.ssh/id_ed25519.pub` into Hetzner.

---

### Step 2 — Connect to the server

Open a terminal (Mac: Applications → Terminal, Windows: PowerShell or [PuTTY](https://putty.org)) and connect:

```bash
ssh root@123.456.789.0
```

Replace `123.456.789.0` with your server's IP address. On first connection a security prompt appears — type `yes` and press Enter.

---

### Step 3 — Update the system

```bash
apt update && apt upgrade -y
```

This updates all pre-installed packages. May take 1–2 minutes.

---

### Step 4 — Install Docker

Docker runs OPENguenther in an isolated environment. Install it with a single command:

```bash
curl -fsSL https://get.docker.com | sh
```

Wait for the installation to finish, then verify Docker is running:

```bash
docker --version
```

You should see something like `Docker version 26.x.x`.

---

### Step 5 — Install Git and download the code

```bash
apt install -y git
git clone https://github.com/ghaslbe/openguenther.git
cd openguenther
```

You are now in the project folder.

---

### Step 6 — Build the Docker image

This command builds OPENguenther (takes 3–5 minutes the first time):

```bash
docker build -t openguenther .
```

You will see many lines — that is normal. When `Successfully tagged openguenther:latest` appears at the end, it worked.

---

### Step 7 — Start OPENguenther

```bash
docker run -d \
  --name openguenther \
  -p 3333:5000 \
  -v openguenther-data:/app/data \
  --restart unless-stopped \
  openguenther
```

This starts OPENguenther in the background. With `--restart unless-stopped` it also restarts automatically after a server reboot.

Check that it is running:

```bash
docker logs openguenther
```

You should see `Running on all addresses (0.0.0.0)`.

---

### Step 8 — Open in the browser

Open your browser and go to:

```
http://123.456.789.0:3333
```

(Replace `123.456.789.0` with your server IP.)

You should now see the OPENguenther interface! 🎉

---

### Step 9 — Set up the OpenRouter API key

OPENguenther needs an API key to communicate with an AI model.

1. Register for free at **[openrouter.ai](https://openrouter.ai)**
2. Go to **Keys** → **Create Key**
3. Copy the key (starts with `sk-or-v1-...`)
4. In OPENguenther: click the **gear icon** (⚙️) in the top left
5. Paste the key in the **"API Key"** field and click **Save**
6. Choose a model, e.g. `openai/gpt-4o-mini` (affordable) or `google/gemini-2.0-flash-001` (fast)

> 💡 **Tip**: In OpenRouter you can set a spending limit to avoid unexpected costs.

---

### Step 10 — Done!

You can now chat with OPENguenther. Try for example:
- *"What is the weather in Berlin?"*
- *"Generate a password with 20 characters"*
- *"Create a QR code for https://example.com"*

---

### Optional steps

#### Set up a firewall (recommended)

Only expose port 3333, block everything else:

```bash
apt install -y ufw
ufw allow ssh
ufw allow 3333
ufw enable
```

#### Update OPENguenther

When a new version is available:

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

Your chats and settings are preserved (they are stored in the Docker volume `openguenther-data`).

#### Set up a Telegram bot (optional)

1. Message **[@BotFather](https://t.me/BotFather)** on Telegram: `/newbot`
2. Follow the instructions and copy the bot token
3. In OPENguenther settings: enter the token, add your Telegram username to the whitelist and click **"Start Gateway"**

---

## Quick Start (for experienced users)

```bash
git clone https://github.com/ghaslbe/openguenther.git && cd openguenther
docker build -t openguenther .
docker run -d --name openguenther -p 3333:5000 -v openguenther-data:/app/data --restart unless-stopped openguenther
```

Open `http://localhost:3333` — enter your API key in the settings.

---

### Configuration

All settings are managed through the web interface (gear icon ⚙️):

- **OpenRouter API Key** + model
- **Telegram Bot Token** + allowed users
- **OpenAI API Key** (optional, for Whisper speech recognition)
- **Image generation model** (optional, e.g. `black-forest-labs/flux-1.1-pro`)
- **STT model** (optional, e.g. `google/gemini-2.5-flash`)

Data is stored persistently in a Docker volume (`/app/data`).

---

## Built-in Tools

| Tool | Description |
|------|-------------|
| `get_weather` | Weather & forecast via Open-Meteo (no API key needed) |
| `generate_image` | Image generation via OpenRouter |
| `process_image` | Image editing via ImageMagick (blur, grayscale, rotate, …) |
| `text_to_image` | Render text as PNG |
| `generate_qr_code` | Generate QR codes |
| `fetch_website_info` | Fetch website title & description |
| `send_email` | Send email via SMTP |
| `generate_password` | Generate secure passwords |
| `calculate` | Evaluate mathematical expressions |
| `roll_dice` | Roll dice |
| `get_current_time` | Get current time |

---

## Disclaimer / Haftungsausschluss

> **USE OF THIS SOFTWARE IS ENTIRELY AT YOUR OWN RISK. / DIE NUTZUNG DIESER SOFTWARE GESCHIEHT VOLLSTÄNDIG AUF EIGENES RISIKO.**

This software is provided **"as is"** without any express or implied warranty of any kind. The author accepts **no liability** for any direct, indirect, incidental, special or consequential damages arising from the use or inability to use this software — regardless of whether based on contract, tort or any other legal basis.

Diese Software wird **„wie besehen"** (as-is) ohne jegliche ausdrückliche oder stillschweigende Gewährleistung bereitgestellt. Der Autor übernimmt **keinerlei Haftung** für direkte, indirekte, zufällige, besondere oder Folgeschäden, die aus der Nutzung oder Nichtnutzung dieser Software entstehen – gleichgültig, ob diese auf Vertrag, unerlaubter Handlung oder einem anderen Rechtsgrund beruhen.

This includes but is not limited to / Dies umfasst insbesondere, aber nicht ausschließlich:

- Damages caused by AI-generated content / Schäden durch KI-generierte Inhalte
- Costs incurred through third-party API usage (OpenRouter, OpenAI, etc.) / Kosten durch API-Nutzung bei Drittanbietern
- Data loss or security incidents / Datenverlust oder Sicherheitsvorfälle
- Damages caused by faulty tool executions / Schäden durch fehlerhafte Tool-Ausführungen

**The author strongly recommends / Der Autor empfiehlt ausdrücklich:**
- Setting spending limits on API keys / API-Keys mit Ausgabelimits versehen
- Not exposing the software publicly without authentication / Software nicht ohne Authentifizierung öffentlich zugänglich machen
- Not entering sensitive data in chats / Keine sensiblen Daten in Chats eingeben

---

## License

MIT License — Copyright (c) 2025

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

**THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.**

---

> ⚠️ **Use of this software is entirely at your own risk. No liability is accepted — not for costs incurred, data loss, security incidents or any other damages of any kind.**
>
> ⚠️ **Die Nutzung dieser Software geschieht vollständig auf eigenes Risiko. Es wird keinerlei Haftung übernommen — weder für entstehende Kosten, Datenverlust, Sicherheitsvorfälle noch für sonstige Schäden jeglicher Art.**
