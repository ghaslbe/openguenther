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
from services import image_store
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

    def _send_audio(self, token, chat_id, audio_bytes, caption=None):
        url = TELEGRAM_API.format(token=token, method="sendAudio")
        try:
            files = {"audio": ("voice.mp3", io.BytesIO(audio_bytes), "audio/mpeg")}
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

        if text == "/start":
            self._send_message(
                token, telegram_chat_id,
                "Hallo! Ich bin Guenther, dein MCP-Agent. "
                "Schreib einfach los oder nutze /new <Name> für eine neue Chat-Session. "
                "Du kannst mir auch Fotos schicken!"
            )
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

            self.socketio.emit("agent_start", {"chat_id": chat_id})
            response = run_agent(messages, settings, emit_log)
            add_message(chat_id, "assistant", response)
            self.socketio.emit("agent_response", {"chat_id": chat_id, "content": response})
            self.socketio.emit("agent_end", {"chat_id": chat_id})

            text_part, images = self._extract_images(response)
            text_part, audio_clips = self._extract_audio(text_part)
            text_part, pdf_docs = self._extract_pdf_reports(text_part)
            text_part, pptx_files = self._extract_pptx(text_part)
            clean = self._clean_text_for_telegram(text_part)
            if clean:
                self._send_message(token, telegram_chat_id, clean)
            for img_bytes in images:
                self._send_photo(token, telegram_chat_id, img_bytes)
            for audio_bytes in audio_clips:
                self._send_audio(token, telegram_chat_id, audio_bytes)
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
        """Extract base64 audio embeds from markdown, return (clean_text, [audio_bytes])."""
        clips = []

        def replace_audio(m):
            data_uri = m.group(1)
            try:
                b64_part = data_uri.split(",", 1)[1]
                clips.append(base64.b64decode(b64_part))
            except Exception as e:
                logger.warning(f"Could not decode base64 audio: {e}")
            return ""

        clean = re.sub(r'!\[audio\]\((data:audio/[^)]+)\)', replace_audio, text)
        clean = clean.strip()
        return clean, clips

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
