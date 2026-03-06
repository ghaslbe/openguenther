import base64
import io
import threading
import time
import re
import json
import logging

import requests as http_requests

from models import create_chat, add_message, get_chat, update_chat_title
from services.agent import run_agent
from services import image_store, file_store
from services.openrouter import transcribe_audio
from services.whisper import transcribe_with_whisper
from config import get_settings, DATA_DIR, TELEGRAM_USERS_FILE

logger = logging.getLogger(__name__)

TELEGRAM_API = "https://api.telegram.org/bot{token}/{method}"
TELEGRAM_FILE_URL = "https://api.telegram.org/file/bot{token}/{file_path}"


def _load_tg_users():
    """Load persisted username -> telegram_chat_id mapping."""
    try:
        with open(TELEGRAM_USERS_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _save_tg_users(mapping):
    import os
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(TELEGRAM_USERS_FILE, 'w') as f:
        json.dump(mapping, f)


def get_telegram_chat_id(username):
    """Look up the Telegram numeric chat_id for a given @username."""
    username = username.lstrip('@')
    return _load_tg_users().get(username)


class TelegramGateway:
    def __init__(self, socketio):
        self.socketio = socketio
        self._thread = None
        self._stop_event = threading.Event()
        self._user_sessions = {}  # username -> chat_id
        self._user_agents = {}    # username -> agent_id or None

    def start(self, token):
        if self._thread and self._thread.is_alive():
            self.stop()
        self._stop_event.clear()
        self._register_commands(token)
        self._thread = threading.Thread(
            target=self._poll_loop,
            args=(token,),
            daemon=True,
            name="telegram-gateway"
        )
        self._thread.start()
        logger.info("Telegram gateway started")

    def stop(self):
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)
        self._thread = None
        logger.info("Telegram gateway stopped")

    def is_running(self):
        return self._thread is not None and self._thread.is_alive()

    def _api_post(self, token, method, **kwargs):
        url = TELEGRAM_API.format(token=token, method=method)
        try:
            r = http_requests.post(url, json=kwargs, timeout=10)
            return r.json()
        except Exception as e:
            logger.error(f"Telegram API error ({method}): {e}")
            return None

    def _send_message(self, token, chat_id, text):
        if len(text) > 4096:
            text = text[:4090] + "\n[...]"
        self._api_post(token, "sendMessage", chat_id=chat_id, text=text)

    def _send_audio(self, token, chat_id, audio_bytes, mime_type="audio/mpeg", filename="audio.mp3", caption=None):
        url = TELEGRAM_API.format(token=token, method="sendAudio")
        try:
            files = {"audio": (filename, io.BytesIO(audio_bytes), mime_type)}
            data = {"chat_id": chat_id}
            if caption:
                data["caption"] = caption[:1024]
            r = http_requests.post(url, files=files, data=data, timeout=30)
            return r.json()
        except Exception as e:
            logger.error(f"Telegram sendAudio error: {e}")
            return None

    def _send_photo(self, token, chat_id, image_bytes, caption=None):
        url = TELEGRAM_API.format(token=token, method="sendPhoto")
        try:
            files = {"photo": ("image.png", io.BytesIO(image_bytes), "image/png")}
            data = {"chat_id": chat_id}
            if caption:
                data["caption"] = caption[:1024]
            r = http_requests.post(url, files=files, data=data, timeout=30)
            return r.json()
        except Exception as e:
            logger.error(f"Telegram sendPhoto error: {e}")
            return None

    def _send_document(self, token, chat_id, file_bytes, filename, mime_type='application/pdf'):
        url = TELEGRAM_API.format(token=token, method="sendDocument")
        try:
            files = {"document": (filename, io.BytesIO(file_bytes), mime_type)}
            data = {"chat_id": chat_id}
            r = http_requests.post(url, files=files, data=data, timeout=30)
            return r.json()
        except Exception as e:
            logger.error(f"Telegram sendDocument error: {e}")
            return None

    def _send_typing(self, token, chat_id):
        """Send a single typing action indicator."""
        self._api_post(token, "sendChatAction", chat_id=chat_id, action="typing")

    def _start_typing_loop(self, token, chat_id):
        """
        Start a background thread that sends 'typing' every 4 seconds.
        Returns a threading.Event — set it to stop the loop.
        """
        stop_event = threading.Event()

        def loop():
            while not stop_event.wait(4):
                self._send_typing(token, chat_id)

        # Send immediately before first 4s wait
        self._send_typing(token, chat_id)
        t = threading.Thread(target=loop, daemon=True)
        t.start()
        return stop_event

    def _register_commands(self, token):
        commands = [
            {"command": "start",  "description": "Guenther starten"},
            {"command": "agents", "description": "Verfügbare Agenten anzeigen"},
            {"command": "agent",  "description": "Agent auswählen, z.B. /agent Orchestrator"},
            {"command": "new",    "description": "Neue Chat-Session starten"},
        ]
        self._api_post(token, "setMyCommands", commands=commands)

    def _get_updates(self, token, offset):
        url = TELEGRAM_API.format(token=token, method="getUpdates")
        try:
            r = http_requests.get(
                url,
                params={
                    "offset": offset,
                    "timeout": 25,
                    "allowed_updates": ["message", "callback_query"]
                },
                timeout=30
            )
            return r.json()
        except Exception as e:
            logger.error(f"getUpdates error: {e}")
            return None

    def _download_telegram_photo(self, token, file_id):
        """
        Download a photo from Telegram.
        Returns (bytes, mime_type) or (None, None) on error.
        """
        result = self._api_post(token, "getFile", file_id=file_id)
        if not result or not result.get("ok"):
            logger.error(f"getFile failed: {result}")
            return None, None

        file_path = result["result"]["file_path"]
        url = TELEGRAM_FILE_URL.format(token=token, file_path=file_path)
        try:
            r = http_requests.get(url, timeout=30)
            if not r.ok:
                logger.error(f"Photo download failed: {r.status_code}")
                return None, None
            mime = "image/jpeg"
            if file_path.lower().endswith(".png"):
                mime = "image/png"
            return r.content, mime
        except Exception as e:
            logger.error(f"Photo download error: {e}")
            return None, None

    def _send_message_md(self, token, chat_id, text, reply_markup=None):
        """Send a message with Markdown parse_mode."""
        if len(text) > 4096:
            text = text[:4090] + "\n[...]"
        payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
        if reply_markup:
            payload["reply_markup"] = reply_markup
        url = TELEGRAM_API.format(token=token, method="sendMessage")
        try:
            http_requests.post(url, json=payload, timeout=10)
        except Exception as e:
            logger.error(f"sendMessage (md) error: {e}")

    def _handle_agents_command(self, token, telegram_chat_id):
        from config import get_agents
        agents = get_agents()
        if not agents:
            self._send_message(token, telegram_chat_id, "Keine Agenten konfiguriert.")
            return
        lines = ["🤖 *Verfügbare Agenten:*\n"]
        for a in agents:
            lines.append(f"*{a['name']}*")
            if a.get("description"):
                lines.append(f"_{a['description']}_")
            lines.append("")
        keyboard = [[{"text": f"🤖 {a['name']}", "callback_data": f"agent:{a['id']}"}] for a in agents]
        keyboard.append([{"text": "✖ Kein Agent", "callback_data": "agent:off"}])
        self._send_message_md(
            token, telegram_chat_id,
            "\n".join(lines),
            reply_markup={"inline_keyboard": keyboard}
        )

    def _select_agent_by_input(self, token, telegram_chat_id, username, arg):
        from config import get_agents, get_agent
        if arg.lower() == "off":
            self._user_agents[username] = None
            self._send_message(token, telegram_chat_id, "✅ Kein Agent aktiv.")
            return
        agents = get_agents()
        agent = None
        try:
            idx = int(arg) - 1
            if 0 <= idx < len(agents):
                agent = agents[idx]
        except ValueError:
            agent = next((a for a in agents if a["name"].lower() == arg.lower()), None)
        if not agent:
            self._send_message(token, telegram_chat_id, f'Agent "{arg}" nicht gefunden. /agents für die Liste.')
            return
        t = threading.Thread(
            target=self._start_agent_session,
            args=(token, telegram_chat_id, username, agent["id"], None),
            daemon=True
        )
        t.start()

    def _handle_callback_query(self, token, query):
        query_id = query["id"]
        data = query.get("data", "")
        from_user = query.get("from", {})
        username = from_user.get("username", "")
        telegram_chat_id = query["message"]["chat"]["id"]
        # Always answer to dismiss loading indicator
        self._api_post(token, "answerCallbackQuery", callback_query_id=query_id)
        # Auth check
        settings = get_settings()
        allowed_users = settings.get("telegram", {}).get("allowed_users", [])
        if not username or username not in allowed_users:
            return
        if data.startswith("agent:"):
            agent_id = data[6:]
            if agent_id == "off":
                self._user_agents[username] = None
                self._send_message(token, telegram_chat_id, "✅ Kein Agent aktiv. Neue Nachrichten ohne Agent.")
            else:
                t = threading.Thread(
                    target=self._start_agent_session,
                    args=(token, telegram_chat_id, username, agent_id, None),
                    daemon=True
                )
                t.start()

    def _start_agent_session(self, token, telegram_chat_id, username, agent_id, custom_title):
        from config import get_agent
        agent_cfg = get_agent(agent_id)
        if not agent_cfg:
            self._send_message(token, telegram_chat_id, "Agent nicht gefunden.")
            return
        self._user_agents[username] = agent_id
        title = custom_title or f"Telegram: @{username} ({agent_cfg['name']})"
        chat_id = create_chat(title)
        self._user_sessions[username] = chat_id
        self.socketio.emit("chat_created", {"chat_id": chat_id, "title": title, "agent_id": agent_id})
        # Get agent greeting
        typing_stop = self._start_typing_loop(token, telegram_chat_id)
        try:
            add_message(chat_id, "user", "Hallo")
            messages = [{"role": "user", "content": "Hallo"}]
            settings = get_settings()

            def emit_log(entry):
                e = entry if isinstance(entry, dict) else {"type": "text", "message": str(entry)}
                self.socketio.emit("guenther_log", e)

            response = run_agent(
                messages, settings, emit_log,
                system_prompt=agent_cfg.get("system_prompt") or None,
                agent_provider_id=agent_cfg.get("provider_id") or None,
                agent_model=agent_cfg.get("model") or None,
                chat_id=chat_id,
                no_tools=True
            )
            response = file_store.extract_and_store(response, chat_id)
            add_message(chat_id, "assistant", response)
            self.socketio.emit("agent_response", {"chat_id": chat_id, "content": response})
            clean = self._clean_text_for_telegram(response)
            if clean:
                self._send_message(token, telegram_chat_id, clean)
        except Exception as e:
            logger.error(f"Agent greeting error: {e}", exc_info=True)
            self._send_message(token, telegram_chat_id, f"Fehler beim Agent-Start: {e}")
        finally:
            typing_stop.set()

    def _poll_loop(self, token):
        offset = 0
        logger.info("Telegram polling loop started")
        while not self._stop_event.is_set():
            result = self._get_updates(token, offset)
            if not result or not result.get("ok"):
                if self._stop_event.wait(5):
                    break
                continue
            for update in result.get("result", []):
                offset = update["update_id"] + 1
                try:
                    if "callback_query" in update:
                        self._handle_callback_query(token, update["callback_query"])
                    else:
                        self._handle_update(token, update)
                except Exception as e:
                    logger.error(
                        f"Error handling update {update.get('update_id')}: {e}",
                        exc_info=True
                    )
        logger.info("Telegram polling loop stopped")

    def _handle_update(self, token, update):
        msg = update.get("message")
        if not msg:
            return

        telegram_chat_id = msg["chat"]["id"]
        from_user = msg.get("from", {})
        username = from_user.get("username", "")

        settings = get_settings()
        telegram_cfg = settings.get("telegram", {})
        allowed_users = telegram_cfg.get("allowed_users", [])

        # Persist username -> telegram_chat_id mapping for send_telegram tool
        if username:
            tg_users = _load_tg_users()
            if tg_users.get(username) != telegram_chat_id:
                tg_users[username] = telegram_chat_id
                _save_tg_users(tg_users)

        # Whitelist check
        if not username or username not in allowed_users:
            display = f"@{username}" if username else "(kein Username)"
            self._send_message(
                token, telegram_chat_id,
                f"Dein Telegram-Username {display} ist nicht freigeschaltet. "
                f"Bitte kontaktiere den Administrator."
            )
            return

        # Reject unsupported media types (but allow photos + voice/audio)
        unsupported = ("video", "document", "sticker", "animation")
        if any(k in msg for k in unsupported):
            self._send_message(
                token, telegram_chat_id,
                "Aktuell werden nur Text-Nachrichten, Fotos und Sprachnachrichten unterstützt."
            )
            return

        # ── Voice / Audio message → STT → treat as text ──
        if "voice" in msg or "audio" in msg:
            file_info = msg.get("voice") or msg.get("audio")
            file_id = file_info["file_id"]
            # Telegram voice = ogg/opus, audio = varies (use mime_type if available)
            mime_type = file_info.get("mime_type", "audio/ogg")
            audio_format = mime_type.split("/")[-1].split(";")[0]  # e.g. 'ogg', 'mpeg', 'mp4'
            if audio_format == "mpeg":
                audio_format = "mp3"

            if username not in self._user_sessions:
                title = f"Telegram: @{username}"
                chat_id = create_chat(title)
                self._user_sessions[username] = chat_id
                self.socketio.emit("chat_created", {"chat_id": chat_id, "title": title})

            chat_id = self._user_sessions[username]

            t = threading.Thread(
                target=self._process_voice,
                args=(token, telegram_chat_id, username, chat_id, file_id, audio_format),
                daemon=True
            )
            t.start()
            return

        # ── Photo message ──
        if "photo" in msg:
            caption = msg.get("caption", "").strip() or "Was soll ich mit diesem Bild machen?"

            if username not in self._user_sessions:
                title = f"Telegram: @{username}"
                chat_id = create_chat(title)
                self._user_sessions[username] = chat_id
                self.socketio.emit("chat_created", {"chat_id": chat_id, "title": title})

            chat_id = self._user_sessions[username]

            # Get highest-resolution variant
            photo = msg["photo"][-1]
            file_id = photo["file_id"]

            img_bytes, mime = self._download_telegram_photo(token, file_id)
            if img_bytes is None:
                self._send_message(
                    token, telegram_chat_id,
                    "Fehler: Bild konnte nicht heruntergeladen werden."
                )
                return

            img_b64 = base64.b64encode(img_bytes).decode()

            t = threading.Thread(
                target=self._process_message,
                args=(token, telegram_chat_id, username, chat_id, caption),
                kwargs={"image_b64": img_b64, "image_mime": mime},
                daemon=True
            )
            t.start()
            return

        # ── Text message ──
        text = msg.get("text", "").strip()
        if not text:
            return

        if text == "/start":
            self._send_message(
                token, telegram_chat_id,
                "Hallo! Ich bin Guenther, dein MCP-Agent.\n\n"
                "Schreib einfach los oder nutze:\n"
                "/agents – Agenten anzeigen\n"
                "/new – Neue Chat-Session\n\n"
                "Du kannst mir auch Fotos und Sprachnachrichten schicken!"
            )
            return

        if text.startswith("/new"):
            parts = text.split(None, 1)
            agent_id = self._user_agents.get(username)
            if agent_id:
                t = threading.Thread(
                    target=self._start_agent_session,
                    args=(token, telegram_chat_id, username, agent_id, parts[1].strip() if len(parts) > 1 else None),
                    daemon=True
                )
                t.start()
            else:
                title = parts[1].strip() if len(parts) > 1 and parts[1].strip() else f"Telegram: @{username}"
                chat_id = create_chat(title)
                self._user_sessions[username] = chat_id
                self.socketio.emit("chat_created", {"chat_id": chat_id, "title": title})
                self._send_message(token, telegram_chat_id, f'Neue Chat-Session gestartet: "{title}"')
            return

        if text == "/agents":
            self._handle_agents_command(token, telegram_chat_id)
            return

        if text.startswith("/agent"):
            arg = text[6:].strip()
            if not arg:
                self._handle_agents_command(token, telegram_chat_id)
            else:
                self._select_agent_by_input(token, telegram_chat_id, username, arg)
            return

        if username not in self._user_sessions:
            title = f"Telegram: @{username}"
            chat_id = create_chat(title)
            self._user_sessions[username] = chat_id
            self.socketio.emit("chat_created", {"chat_id": chat_id, "title": title})

        chat_id = self._user_sessions[username]

        t = threading.Thread(
            target=self._process_message,
            args=(token, telegram_chat_id, username, chat_id, text),
            daemon=True
        )
        t.start()

    def _process_voice(self, token, telegram_chat_id, username, chat_id, file_id, audio_format):
        """Download a voice/audio message, transcribe it via STT, then process as text."""
        typing_stop = self._start_typing_loop(token, telegram_chat_id)
        try:
            audio_bytes, _ = self._download_telegram_photo(token, file_id)
            if audio_bytes is None:
                self._send_message(
                    token, telegram_chat_id,
                    "Fehler: Sprachnachricht konnte nicht heruntergeladen werden."
                )
                return

            settings = get_settings()
            use_whisper = settings.get("use_openai_whisper", False)
            openai_key = settings.get("openai_api_key", "").strip()

            if use_whisper:
                if not openai_key:
                    self._send_message(
                        token, telegram_chat_id,
                        "Whisper aktiviert, aber kein OpenAI API-Key konfiguriert."
                    )
                    return
                logger.info(f"STT via Whisper: format={audio_format} bytes={len(audio_bytes)}")
                transcript = transcribe_with_whisper(audio_bytes, audio_format, openai_key)
            else:
                or_key = settings.get("openrouter_api_key", "")
                stt_model = settings.get("stt_model", "").strip()
                if not stt_model:
                    self._send_message(
                        token, telegram_chat_id,
                        "Kein STT-Modell konfiguriert. Bitte in den Einstellungen ein "
                        "Audio-fähiges Modell eintragen (z.B. google/gemini-2.5-flash) "
                        "oder OpenAI Whisper aktivieren."
                    )
                    return
                logger.info(f"STT via OpenRouter: model={stt_model} format={audio_format} bytes={len(audio_bytes)}")
                transcript = transcribe_audio(audio_bytes, audio_format, or_key, stt_model)

            logger.info(f"STT result: {repr(transcript)}")
            if not transcript:
                self._send_message(
                    token, telegram_chat_id,
                    "Konnte die Sprachnachricht nicht transkribieren."
                )
                return

            self._send_message(token, telegram_chat_id, f"[Sprache erkannt]: {transcript}")

        except Exception as e:
            logger.error(f"Voice processing error: {e}", exc_info=True)
            self._send_message(token, telegram_chat_id, f"Fehler bei Spracherkennung: {e}")
            return
        finally:
            typing_stop.set()

        # Process the transcript exactly like a regular text message
        self._process_message(token, telegram_chat_id, username, chat_id, transcript)

    def _process_message(self, token, telegram_chat_id, username, chat_id, text,
                         image_b64=None, image_mime=None):
        typing_stop = self._start_typing_loop(token, telegram_chat_id)
        session_key = f"tg_{username}"
        try:
            add_message(chat_id, "user", text)
            self.socketio.emit("chat_updated", {"chat_id": chat_id, "title": None})

            chat_data = get_chat(chat_id)
            if not chat_data:
                self._send_message(token, telegram_chat_id, "Fehler: Chat nicht gefunden.")
                return

            messages = [
                {"role": m["role"], "content": m["content"]}
                for m in chat_data.get("messages", [])
                if m["role"] in ("user", "assistant")
            ]

            # Update title on first user message
            if len(messages) == 1:
                title = text[:50] + ("..." if len(text) > 50 else "")
                update_chat_title(chat_id, title)
                self.socketio.emit("chat_updated", {"chat_id": chat_id, "title": title})

            # If a photo was sent, store it and inject a text hint for the LLM
            if image_b64:
                image_store.store(session_key, image_b64, image_mime or "image/jpeg")
                for i in range(len(messages) - 1, -1, -1):
                    if messages[i]["role"] == "user":
                        hint = (
                            f"\n\n[System: Bild vom Nutzer empfangen (Session-Key: '{session_key}'). "
                            f"Für Bildbearbeitung: process_image(session_key='{session_key}', operation='...'). "
                            f"Operationen: blur, grayscale, rotate, resize, sharpen, "
                            f"brightness, contrast, flip_horizontal, flip_vertical, invert]"
                        )
                        messages[i]["content"] = messages[i]["content"] + hint
                        break

            settings = get_settings()

            def emit_log(entry):
                if isinstance(entry, dict):
                    self.socketio.emit("guenther_log", entry)
                else:
                    self.socketio.emit("guenther_log", {"type": "text", "message": str(entry)})

            # Use selected agent if any
            agent_cfg = None
            agent_id = self._user_agents.get(username)
            if agent_id:
                from config import get_agent
                agent_cfg = get_agent(agent_id)

            self.socketio.emit("agent_start", {"chat_id": chat_id})
            response = run_agent(
                messages, settings, emit_log,
                system_prompt=agent_cfg.get("system_prompt") or None if agent_cfg else None,
                agent_provider_id=agent_cfg.get("provider_id") or None if agent_cfg else None,
                agent_model=agent_cfg.get("model") or None if agent_cfg else None,
                chat_id=chat_id
            )
            response = file_store.extract_and_store(response, chat_id)
            add_message(chat_id, "assistant", response)
            self.socketio.emit("agent_response", {"chat_id": chat_id, "content": response})
            self.socketio.emit("agent_end", {"chat_id": chat_id})

            text_part, images = self._extract_images(response)
            text_part, audio_clips = self._extract_audio(text_part)
            text_part, pdf_docs = self._extract_pdf_reports(text_part)
            text_part, pptx_files = self._extract_stored_files(text_part, chat_id)
            clean = self._clean_text_for_telegram(text_part)
            if clean:
                self._send_message(token, telegram_chat_id, clean)
            for img_bytes in images:
                self._send_photo(token, telegram_chat_id, img_bytes)
            for audio_bytes, mime_type, filename in audio_clips:
                self._send_audio(token, telegram_chat_id, audio_bytes, mime_type=mime_type, filename=filename)
            for pdf_bytes in pdf_docs:
                self._send_document(token, telegram_chat_id, pdf_bytes, 'seo-report.pdf')
            for filename, pptx_bytes in pptx_files:
                self._send_document(
                    token, telegram_chat_id, pptx_bytes, filename,
                    mime_type='application/vnd.openxmlformats-officedocument.presentationml.presentation'
                )

        except Exception as e:
            logger.error(f"Error processing Telegram message: {e}", exc_info=True)
            self._send_message(
                token, telegram_chat_id,
                f"Fehler bei der Verarbeitung: {str(e)}"
            )
        finally:
            typing_stop.set()
            if image_b64:
                image_store.remove(session_key)

    def _extract_images(self, text):
        """Extract base64 image embeds from markdown, return (clean_text, [image_bytes])."""
        images = []

        def replace_image(m):
            data_uri = m.group(1)
            try:
                b64_part = data_uri.split(",", 1)[1]
                images.append(base64.b64decode(b64_part))
            except Exception as e:
                logger.warning(f"Could not decode base64 image: {e}")
            return ""

        clean = re.sub(r'!\[.*?\]\((data:image/[^)]+)\)', replace_image, text)
        clean = clean.strip()
        return clean, images

    def _extract_audio(self, text):
        """Extract base64 audio embeds from markdown, return (clean_text, [(bytes, mime_type, filename)])."""
        _ext_map = {
            'audio/mpeg': 'mp3', 'audio/mp3': 'mp3',
            'audio/wav': 'wav', 'audio/x-wav': 'wav',
            'audio/ogg': 'ogg', 'audio/flac': 'flac',
            'audio/aac': 'aac', 'audio/mp4': 'm4a',
            'audio/opus': 'opus',
        }
        clips = []

        def replace_audio(m):
            data_uri = m.group(1)
            try:
                mime_type = data_uri.split(';')[0].split(':', 1)[1]
                b64_part = data_uri.split(",", 1)[1]
                ext = _ext_map.get(mime_type, 'mp3')
                clips.append((base64.b64decode(b64_part), mime_type, f"audio.{ext}"))
            except Exception as e:
                logger.warning(f"Could not decode base64 audio: {e}")
            return ""

        clean = re.sub(r'!\[audio\]\((data:audio/[^)]+)\)', replace_audio, text)
        clean = clean.strip()
        return clean, clips

    def _extract_stored_files(self, text, chat_id):
        """Extract [STORED_FILE](filename) markers, load from disk, return (clean_text, [(filename, bytes)])."""
        files = []

        def replace(m):
            filename = m.group(1)
            data = file_store.get_file(chat_id, filename)
            if data:
                files.append((filename, data))
            return ""

        clean = re.sub(r'\[STORED_FILE\]\(([^)]+)\)', replace, text)
        # Fallback: handle old [PPTX_DOWNLOAD] markers from pre-1.4.17 chat history
        clean, old_pptx = self._extract_pptx(clean)
        for fn, fb in old_pptx:
            files.append((fn, fb))
        return clean.strip(), files

    def _extract_pptx(self, text):
        """Extract [PPTX_DOWNLOAD](filename::base64) markers, return (clean_text, [(filename, pptx_bytes)])."""
        files = []

        def replace_pptx(m):
            filename = m.group(1)
            b64 = m.group(2)
            try:
                files.append((filename, base64.b64decode(b64)))
            except Exception as e:
                logger.warning(f"Could not decode base64 PPTX: {e}")
            return ""

        clean = re.sub(r'\[PPTX_DOWNLOAD\]\(([^:)]+)::([A-Za-z0-9+/=]+)\)', replace_pptx, text)
        clean = clean.strip()
        return clean, files

    def _extract_pdf_reports(self, text):
        """Extract [PDF_REPORT](data:text/html;base64,...) markers, convert to PDF, return (clean_text, [pdf_bytes])."""
        pdfs = []

        def replace_pdf(m):
            data_uri = m.group(1)
            try:
                b64_part = data_uri.split(",", 1)[1]
                html_str = base64.b64decode(b64_part).decode('utf-8')
                from weasyprint import HTML
                pdf_bytes = HTML(string=html_str).write_pdf()
                pdfs.append(pdf_bytes)
            except Exception as e:
                logger.warning(f"PDF conversion error: {e}")
            return ""

        clean = re.sub(r'\[PDF_REPORT\]\((data:text/html;base64,[^)]+)\)', replace_pdf, text)
        # Also strip any leftover HTML_REPORT markers (already handled by iframe in web UI)
        clean = re.sub(r'\[HTML_REPORT\]\((data:text/html;base64,[^)]+)\)', '', clean)
        clean = clean.strip()
        return clean, pdfs

    def _clean_text_for_telegram(self, text):
        if len(text) > 4096:
            text = text[:4090] + "\n[...]"
        return text
