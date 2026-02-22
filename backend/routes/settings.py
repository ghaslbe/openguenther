from flask import Blueprint, request, jsonify
from config import get_settings, save_settings
import uuid

settings_bp = Blueprint('settings', __name__)


def _mask_key(key):
    if key and len(key) > 12:
        return key[:8] + '...' + key[-4:]
    elif key:
        return '***'
    return ''


@settings_bp.route('/api/settings', methods=['GET'])
def get_settings_route():
    settings = get_settings()
    masked = settings.copy()
    for field, masked_field in [
        ('openrouter_api_key', 'openrouter_api_key_masked'),
        ('openai_api_key', 'openai_api_key_masked'),
    ]:
        masked[masked_field] = _mask_key(masked.get(field, ''))
    # Mask provider api_keys
    if 'providers' in masked:
        import copy
        masked['providers'] = copy.deepcopy(masked['providers'])
        for pcfg in masked['providers'].values():
            pcfg['api_key_masked'] = _mask_key(pcfg.get('api_key', ''))
    return jsonify(masked)


@settings_bp.route('/api/settings', methods=['PUT'])
def update_settings():
    data = request.get_json()
    settings = get_settings()

    if 'openrouter_api_key' in data:
        settings['openrouter_api_key'] = data['openrouter_api_key']
    for key in ('model', 'stt_model', 'tts_model', 'image_gen_model', 'openai_api_key', 'default_provider'):
        if key in data:
            settings[key] = data[key]
    if 'temperature' in data:
        settings['temperature'] = float(data['temperature'])
    if 'use_openai_whisper' in data:
        settings['use_openai_whisper'] = bool(data['use_openai_whisper'])

    save_settings(settings)
    return jsonify({'success': True})


@settings_bp.route('/api/providers', methods=['GET'])
def get_providers():
    settings = get_settings()
    providers = settings.get('providers', {})
    result = {}
    for pid, pcfg in providers.items():
        import copy
        masked = copy.deepcopy(pcfg)
        masked['api_key_masked'] = _mask_key(pcfg.get('api_key', ''))
        result[pid] = masked
    return jsonify(result)


@settings_bp.route('/api/providers/<provider_id>', methods=['PUT'])
def update_provider(provider_id):
    data = request.get_json()
    settings = get_settings()
    if 'providers' not in settings:
        settings['providers'] = {}
    if provider_id not in settings['providers']:
        settings['providers'][provider_id] = {}

    pcfg = settings['providers'][provider_id]
    for field in ('name', 'base_url', 'enabled'):
        if field in data:
            pcfg[field] = data[field]
    if data.get('api_key'):
        pcfg['api_key'] = data['api_key']
        # Sync to legacy field for OpenRouter
        if provider_id == 'openrouter':
            settings['openrouter_api_key'] = data['api_key']

    save_settings(settings)
    return jsonify({'success': True})


@settings_bp.route('/api/mcp-servers', methods=['GET'])
def list_mcp_servers():
    settings = get_settings()
    return jsonify(settings.get('mcp_servers', []))


@settings_bp.route('/api/mcp-servers', methods=['POST'])
def add_mcp_server():
    data = request.get_json()
    settings = get_settings()

    server = {
        'id': str(uuid.uuid4()),
        'name': data.get('name', 'Unnamed'),
        'transport': data.get('transport', 'stdio'),
        'command': data.get('command', ''),
        'args': data.get('args', []),
        'url': data.get('url', ''),
        'enabled': True
    }

    if 'mcp_servers' not in settings:
        settings['mcp_servers'] = []
    settings['mcp_servers'].append(server)
    save_settings(settings)

    return jsonify(server), 201


@settings_bp.route('/api/mcp-servers/<server_id>', methods=['DELETE'])
def remove_mcp_server(server_id):
    settings = get_settings()
    settings['mcp_servers'] = [
        s for s in settings.get('mcp_servers', []) if s['id'] != server_id
    ]
    save_settings(settings)
    return jsonify({'success': True})


@settings_bp.route('/api/mcp-servers/<server_id>/toggle', methods=['POST'])
def toggle_mcp_server(server_id):
    settings = get_settings()
    for s in settings.get('mcp_servers', []):
        if s['id'] == server_id:
            s['enabled'] = not s.get('enabled', True)
            break
    save_settings(settings)
    return jsonify({'success': True})


@settings_bp.route('/api/telegram/settings', methods=['GET'])
def get_telegram_settings():
    settings = get_settings()
    cfg = settings.get('telegram', {})
    token = cfg.get('bot_token', '')
    masked = ''
    if token and len(token) > 12:
        masked = token[:8] + '...' + token[-4:]
    elif token:
        masked = '***'
    return jsonify({
        'bot_token_masked': masked,
        'allowed_users': cfg.get('allowed_users', []),
    })


@settings_bp.route('/api/telegram/settings', methods=['PUT'])
def update_telegram_settings():
    data = request.get_json()
    settings = get_settings()
    if 'telegram' not in settings:
        settings['telegram'] = {}

    if 'bot_token' in data and data['bot_token']:
        settings['telegram']['bot_token'] = data['bot_token']
    if 'allowed_users' in data:
        settings['telegram']['allowed_users'] = data['allowed_users']

    save_settings(settings)
    return jsonify({'success': True})


@settings_bp.route('/api/telegram/status', methods=['GET'])
def get_telegram_status():
    from app import telegram_gateway
    return jsonify({'running': telegram_gateway.is_running()})


@settings_bp.route('/api/telegram/restart', methods=['POST'])
def restart_telegram():
    from app import telegram_gateway
    settings = get_settings()
    token = settings.get('telegram', {}).get('bot_token', '')
    if not token:
        return jsonify({'success': False, 'error': 'Kein Bot-Token konfiguriert'}), 400
    telegram_gateway.stop()
    telegram_gateway.start(token)
    return jsonify({'success': True})


@settings_bp.route('/api/telegram/stop', methods=['POST'])
def stop_telegram():
    from app import telegram_gateway
    telegram_gateway.stop()
    return jsonify({'success': True})
