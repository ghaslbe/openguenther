import uuid
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify, Response
import json
from config import get_agents, save_agents

agents_bp = Blueprint('agents', __name__)


@agents_bp.route('/api/agents', methods=['GET'])
def list_agents():
    return jsonify(get_agents())


@agents_bp.route('/api/agents', methods=['POST'])
def create_agent():
    data = request.get_json()
    agents = get_agents()
    agent = {
        'id': str(uuid.uuid4()),
        'name': data.get('name', '').strip(),
        'description': data.get('description', '').strip(),
        'system_prompt': data.get('system_prompt', '').strip(),
        'provider_id': data.get('provider_id', '').strip(),
        'model': data.get('model', '').strip(),
    }
    agents.append(agent)
    save_agents(agents)
    return jsonify(agent), 201


@agents_bp.route('/api/agents/<agent_id>', methods=['PUT'])
def update_agent(agent_id):
    data = request.get_json()
    agents = get_agents()
    for a in agents:
        if a['id'] == agent_id:
            a['name'] = data.get('name', a['name']).strip()
            a['description'] = data.get('description', a.get('description', '')).strip()
            a['system_prompt'] = data.get('system_prompt', a['system_prompt']).strip()
            a['provider_id'] = data.get('provider_id', a.get('provider_id', '')).strip()
            a['model'] = data.get('model', a.get('model', '')).strip()
            save_agents(agents)
            return jsonify(a)
    return jsonify({'error': 'Agent nicht gefunden'}), 404


@agents_bp.route('/api/agents/<agent_id>', methods=['DELETE'])
def delete_agent(agent_id):
    agents = get_agents()
    new_agents = [a for a in agents if a['id'] != agent_id]
    if len(new_agents) == len(agents):
        return jsonify({'error': 'Agent nicht gefunden'}), 404
    save_agents(new_agents)
    return jsonify({'success': True})


EXPORT_VERSION = 1

@agents_bp.route('/api/agents/export', methods=['GET'])
def export_agents():
    payload = {
        'type': 'openguenther_agents',
        'version': EXPORT_VERSION,
        'exported_at': datetime.now(timezone.utc).isoformat(),
        'data': get_agents(),
    }
    return Response(
        json.dumps(payload, ensure_ascii=False, indent=2),
        mimetype='application/json',
        headers={'Content-Disposition': 'attachment; filename="agents.json"'}
    )


@agents_bp.route('/api/agents/import', methods=['POST'])
def import_agents():
    payload = request.get_json()
    if not payload or payload.get('type') != 'openguenther_agents':
        return jsonify({'error': 'Ungültiges Format'}), 400
    if payload.get('version', 1) > EXPORT_VERSION:
        return jsonify({'error': f'Version {payload["version"]} wird nicht unterstützt (max: {EXPORT_VERSION})'}), 400
    incoming = payload.get('data', [])
    agents = get_agents()
    existing_names = {a['name'] for a in agents}
    added = 0
    for a in incoming:
        new = {
            'id': str(uuid.uuid4()),
            'name': a.get('name', '').strip(),
            'description': a.get('description', '').strip(),
            'system_prompt': a.get('system_prompt', '').strip(),
            'provider_id': a.get('provider_id', '').strip(),
            'model': a.get('model', '').strip(),
        }
        if not new['name'] or not new['system_prompt']:
            continue
        if new['name'] in existing_names:
            new['name'] += ' (importiert)'
        agents.append(new)
        existing_names.add(new['name'])
        added += 1
    save_agents(agents)
    return jsonify({'success': True, 'added': added})
