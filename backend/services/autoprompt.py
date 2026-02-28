import json
import uuid
import logging
from datetime import datetime, timezone

from apscheduler.schedulers.background import BackgroundScheduler

from config import AUTOPROMPTS_FILE, get_settings, get_agent, DATA_DIR
from models import create_chat, add_message, get_chat, update_chat_title

log = logging.getLogger(__name__)


def _load_file():
    try:
        with open(AUTOPROMPTS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def _save_file(data):
    import os
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(AUTOPROMPTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_autoprompts():
    return _load_file()


def get_autoprompt(ap_id):
    return next((a for a in _load_file() if a['id'] == ap_id), None)


def save_autoprompt(ap):
    data = _load_file()
    for i, a in enumerate(data):
        if a['id'] == ap['id']:
            data[i] = ap
            _save_file(data)
            return
    data.append(ap)
    _save_file(data)


def delete_autoprompt(ap_id):
    data = [a for a in _load_file() if a['id'] != ap_id]
    _save_file(data)


class AutopromptService:
    def __init__(self, socketio):
        self.socketio = socketio
        self.scheduler = BackgroundScheduler(timezone='UTC')
        self.scheduler.start()
        self._load_all()

    def _load_all(self):
        for ap in _load_file():
            if ap.get('enabled'):
                try:
                    self._schedule(ap)
                except Exception as e:
                    log.warning(f"Autoprompt '{ap.get('name')}' konnte nicht geplant werden: {e}")

    def _schedule(self, ap):
        job_id = f"ap_{ap['id']}"
        st = ap.get('schedule_type', 'daily')

        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)

        if st == 'interval':
            minutes = int(ap.get('interval_minutes', 60))
            self.scheduler.add_job(
                self._run, 'interval', minutes=minutes,
                id=job_id, args=[ap['id']], replace_existing=True
            )
        elif st == 'daily':
            t = ap.get('daily_time', '08:00')
            h, m = (int(x) for x in t.split(':'))
            self.scheduler.add_job(
                self._run, 'cron', hour=h, minute=m,
                id=job_id, args=[ap['id']], replace_existing=True
            )
        elif st == 'weekly':
            t = ap.get('daily_time', '08:00')
            h, m = (int(x) for x in t.split(':'))
            wd = int(ap.get('weekly_day', 0))
            self.scheduler.add_job(
                self._run, 'cron', day_of_week=wd, hour=h, minute=m,
                id=job_id, args=[ap['id']], replace_existing=True
            )

    def _unschedule(self, ap_id):
        job_id = f"ap_{ap_id}"
        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)

    def _run(self, ap_id):
        from services.agent import run_agent

        ap = get_autoprompt(ap_id)
        if not ap or not ap.get('enabled'):
            return

        log.info(f"Autoprompt '{ap['name']}' läuft...")
        now_iso = datetime.now(timezone.utc).isoformat()

        # Ensure a dedicated chat exists — create once, reuse always
        chat_id = ap.get('chat_id')
        if not chat_id or not get_chat(chat_id):
            chat_id = create_chat(f"Autoprompt: {ap['name']}")
            update_chat_title(chat_id, f"Autoprompt: {ap['name']}")
            ap['chat_id'] = chat_id

        settings = get_settings()

        # Build message history for agent (full chat history)
        chat = get_chat(chat_id)
        messages = [
            {'role': m['role'], 'content': m['content']}
            for m in chat.get('messages', [])
            if m['role'] in ('user', 'assistant')
        ]
        messages.append({'role': 'user', 'content': ap['prompt']})

        agent_system_prompt = None
        if ap.get('agent_id'):
            agent_cfg = get_agent(ap['agent_id'])
            if agent_cfg:
                agent_system_prompt = agent_cfg.get('system_prompt') or None

        try:
            response = run_agent(messages, settings, emit_log=None, system_prompt=agent_system_prompt)
            add_message(chat_id, 'user', ap['prompt'])
            add_message(chat_id, 'assistant', response)
            ap['last_run'] = now_iso
            ap['last_error'] = None
            log.info(f"Autoprompt '{ap['name']}' abgeschlossen.")
            self.socketio.emit('autoprompt_done', {
                'id': ap_id,
                'name': ap['name'],
                'chat_id': chat_id,
                'last_run': now_iso,
            })
        except Exception as e:
            ap['last_error'] = str(e)
            ap['last_run'] = now_iso
            log.error(f"Autoprompt '{ap['name']}' Fehler: {e}")

        save_autoprompt(ap)

    def reload(self, ap_id):
        ap = get_autoprompt(ap_id)
        if not ap:
            self._unschedule(ap_id)
            return
        if ap.get('enabled'):
            self._schedule(ap)
        else:
            self._unschedule(ap_id)

    def remove(self, ap_id):
        self._unschedule(ap_id)
