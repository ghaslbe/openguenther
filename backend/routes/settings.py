from flask import Blueprint, request, jsonify
from config import get_settings, save_settings
import uuid

settings_bp = Blueprint('settings', __name__)


@settings_bp.route('/api/settings', methods=['GET'])
def get_settings_route():
    settings = get_settings()
    masked = settings.copy()
    key = masked.get('openrouter_api_key', '')
    if key and len(key) > 12:
        masked['openrouter_api_key_masked'] = key[:8] + '...' + key[-4:]
    elif key:
        masked['openrouter_api_key_masked'] = '***'
    else:
        masked['openrouter_api_key_masked'] = ''
    return jsonify(masked)


@settings_bp.route('/api/settings', methods=['PUT'])
def update_settings():
    data = request.get_json()
    settings = get_settings()

    if 'openrouter_api_key' in data:
        settings['openrouter_api_key'] = data['openrouter_api_key']
    if 'model' in data:
        settings['model'] = data['model']

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
