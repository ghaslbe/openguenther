import uuid
import secrets
from datetime import datetime, timezone

from flask import Blueprint, request, jsonify

from config import get_webhooks, save_webhooks, get_webhook, get_agent
from models import get_chat, create_chat, add_message

webhooks_bp = Blueprint('webhooks', __name__)


def _mask_token(token):
    if len(token) <= 8:
        return '***'
    return token[:6] + '...' + token[-4:]


@webhooks_bp.route('/api/webhooks', methods=['GET'])
def list_webhooks():
    whs = get_webhooks()
    result = []
    for w in whs:
        result.append({**w, 'token': _mask_token(w['token'])})
    return jsonify(result)


@webhooks_bp.route('/api/webhooks', methods=['POST'])
def create_webhook():
    data = request.get_json() or {}
    name = (data.get('name') or '').strip()
    if not name:
        return jsonify({'error': 'Name ist erforderlich'}), 400

    wh = {
        'id': str(uuid.uuid4()),
        'name': name,
        'token': 'wh_' + secrets.token_hex(16),
        'chat_id': data.get('chat_id') or None,
        'agent_id': data.get('agent_id') or '',
        'created_at': datetime.now(timezone.utc).isoformat(),
    }
    whs = get_webhooks()
    whs.append(wh)
    save_webhooks(whs)
    return jsonify(wh), 201


@webhooks_bp.route('/api/webhooks/<wh_id>', methods=['PUT'])
def update_webhook(wh_id):
    whs = get_webhooks()
    for i, w in enumerate(whs):
        if w['id'] == wh_id:
            data = request.get_json() or {}
            w['name'] = data.get('name', w['name'])
            w['chat_id'] = data.get('chat_id') or None
            w['agent_id'] = data.get('agent_id') or ''
            whs[i] = w
            save_webhooks(whs)
            return jsonify({**w, 'token': _mask_token(w['token'])})
    return jsonify({'error': 'Nicht gefunden'}), 404


@webhooks_bp.route('/api/webhooks/<wh_id>', methods=['DELETE'])
def delete_webhook(wh_id):
    whs = [w for w in get_webhooks() if w['id'] != wh_id]
    save_webhooks(whs)
    return jsonify({'success': True})


# ── Public trigger endpoint ──

@webhooks_bp.route('/webhook/<wh_id>', methods=['POST'])
def trigger_webhook(wh_id):
    from config import get_settings
    from services.agent import run_agent
    from services import file_store

    wh = get_webhook(wh_id)
    if not wh:
        return jsonify({'error': 'Webhook nicht gefunden'}), 404

    auth = request.headers.get('Authorization', '')
    if not auth.startswith('Bearer ') or auth[7:] != wh['token']:
        return jsonify({'error': 'Ungültiger Token'}), 401

    body = request.get_json(silent=True) or {}
    message = (body.get('message') or '').strip()
    if not message:
        return jsonify({'error': 'message ist erforderlich'}), 400

    # Determine chat
    chat_id = wh.get('chat_id')
    if chat_id and not get_chat(chat_id):
        chat_id = None

    if chat_id:
        chat = get_chat(chat_id)
        messages = [
            {'role': m['role'], 'content': m['content']}
            for m in chat.get('messages', [])
            if m['role'] in ('user', 'assistant')
        ]
    else:
        chat_id = create_chat(message[:50] + ('...' if len(message) > 50 else ''))
        messages = []

    messages.append({'role': 'user', 'content': message})
    add_message(chat_id, 'user', message)

    # Resolve agent
    agent_system_prompt = None
    agent_provider_id = None
    agent_model = None
    agent_id = wh.get('agent_id') or ''
    if agent_id:
        agent_cfg = get_agent(agent_id)
        if agent_cfg:
            agent_system_prompt = agent_cfg.get('system_prompt') or None
            agent_provider_id = agent_cfg.get('provider_id') or None
            agent_model = agent_cfg.get('model') or None

    settings = get_settings()

    try:
        response = run_agent(
            messages, settings,
            emit_log=lambda _: None,
            system_prompt=agent_system_prompt,
            agent_provider_id=agent_provider_id,
            agent_model=agent_model,
            chat_id=chat_id,
        )
        response = file_store.extract_and_store(response, chat_id)
        add_message(chat_id, 'assistant', response)
        return jsonify({'chat_id': chat_id, 'response': response})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
