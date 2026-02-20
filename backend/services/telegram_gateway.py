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
from config import get_settings

logger = logging.getLogger(__name__)

TELEGRAM_API = "https://api.telegram.org/bot{token}/{method}"


class TelegramGateway:
    def __init__(self, socketio):
        self.socketio = socketio
        self._thread = None
        self._stop_event = threading.Event()
        self._user_sessions = {}  # username -> chat_id

    def start(self, token):
        if self._thread and self._thread.is_alive():
            self.stop()
        self._stop_event.clear()
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

    def _get_updates(self, token, offset):
        url = TELEGRAM_API.format(token=token, method="getUpdates")
        try:
            r = http_requests.get(
                url,
                params={
                    "offset": offset,
                    "timeout": 25,
                    "allowed_updates": ["message"]
                },
                timeout=30
            )
            return r.json()
        except Exception as e:
            logger.error(f"getUpdates error: {e}")
            return None

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

        # Whitelist check
        if not username or username not in allowed_users:
            display = f"@{username}" if username else "(kein Username)"
            self._send_message(
                token, telegram_chat_id,
                f"Dein Telegram-Username {display} ist nicht freigeschaltet. "
                f"Bitte kontaktiere den Administrator."
            )
            return

        # Reject non-text content
        media_keys = ("photo", "audio", "voice", "video", "document", "sticker", "animation")
        if any(k in msg for k in media_keys):
            self._send_message(
                token, telegram_chat_id,
                "Aktuell werden nur Text-Nachrichten unterstützt. "
                "Bilder und Audio werden nicht verarbeitet."
            )
            return

        text = msg.get("text", "").strip()
        if not text:
            return

        # /new command: start a new chat session
        if text.startswith("/new"):
            parts = text.split(None, 1)
            title = (
                parts[1].strip()
                if len(parts) > 1 and parts[1].strip()
                else f"Telegram: @{username}"
            )
            chat_id = create_chat(title)
            self._user_sessions[username] = chat_id
            self.socketio.emit("chat_created", {"chat_id": chat_id, "title": title})
            self._send_message(
                token, telegram_chat_id,
                f'Neue Chat-Session gestartet: "{title}"'
            )
            return

        # /start: welcome message (already whitelisted at this point)
        if text == "/start":
            self._send_message(
                token, telegram_chat_id,
                "Hallo! Ich bin Guenther, dein MCP-Agent. "
                "Schreib einfach los oder nutze /new <Name> für eine neue Chat-Session."
            )
            return

        # Get or create session for user
        if username not in self._user_sessions:
            title = f"Telegram: @{username}"
            chat_id = create_chat(title)
            self._user_sessions[username] = chat_id
            self.socketio.emit("chat_created", {"chat_id": chat_id, "title": title})

        chat_id = self._user_sessions[username]

        # Process message in background thread to not block the poller
        t = threading.Thread(
            target=self._process_message,
            args=(token, telegram_chat_id, username, chat_id, text),
            daemon=True
        )
        t.start()

    def _process_message(self, token, telegram_chat_id, username, chat_id, text):
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

            settings = get_settings()

            def emit_log(entry):
                if isinstance(entry, dict):
                    self.socketio.emit("guenther_log", entry)
                else:
                    self.socketio.emit("guenther_log", {"type": "text", "message": str(entry)})

            self.socketio.emit("agent_start", {"chat_id": chat_id})
            response = run_agent(messages, settings, emit_log)
            add_message(chat_id, "assistant", response)
            self.socketio.emit("agent_response", {"chat_id": chat_id, "content": response})
            self.socketio.emit("agent_end", {"chat_id": chat_id})

            text_part, images = self._extract_images(response)
            clean = self._clean_text_for_telegram(text_part)
            if clean:
                self._send_message(token, telegram_chat_id, clean)
            for img_bytes in images:
                self._send_photo(token, telegram_chat_id, img_bytes)

        except Exception as e:
            logger.error(f"Error processing Telegram message: {e}", exc_info=True)
            self._send_message(
                token, telegram_chat_id,
                f"Fehler bei der Verarbeitung: {str(e)}"
            )

    def _extract_images(self, text):
        """Extract base64 image embeds from markdown, return (clean_text, [image_bytes])."""
        images = []

        def replace_image(m):
            data_uri = m.group(1)
            try:
                # data:image/png;base64,<data>
                b64_part = data_uri.split(",", 1)[1]
                images.append(base64.b64decode(b64_part))
            except Exception as e:
                logger.warning(f"Could not decode base64 image: {e}")
            return ""

        clean = re.sub(r'!\[.*?\]\((data:image/[^)]+)\)', replace_image, text)
        clean = clean.strip()
        return clean, images

    def _clean_text_for_telegram(self, text):
        """Truncate text for Telegram message limit."""
        if len(text) > 4096:
            text = text[:4090] + "\n[...]"
        return text
