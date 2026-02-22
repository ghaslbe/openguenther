import uuid
from flask import Blueprint, request, jsonify
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
