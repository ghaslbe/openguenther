import uuid
import json
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify, Response
from services.autoprompt import (
    get_autoprompts, get_autoprompt, save_autoprompt, delete_autoprompt
)

autoprompts_bp = Blueprint('autoprompts', __name__)

# Will be set by app.py after service is created
_service = None


def set_service(service):
    global _service
    _service = service


@autoprompts_bp.route('/api/server-time', methods=['GET'])
def server_time():
    now = datetime.now(timezone.utc)
    return jsonify({"utc": now.strftime("%H:%M"), "local": datetime.now().strftime("%H:%M"), "tz": "UTC"})


@autoprompts_bp.route('/api/autoprompts', methods=['GET'])
def list_autoprompts():
    return jsonify(get_autoprompts())


@autoprompts_bp.route('/api/autoprompts', methods=['POST'])
def create_autoprompt():
    data = request.get_json()
    ap = {
        'id': str(uuid.uuid4()),
        'name': data.get('name', 'Autoprompt'),
        'prompt': data.get('prompt', ''),
        'enabled': data.get('enabled', True),
        'schedule_type': data.get('schedule_type', 'daily'),
        'interval_minutes': data.get('interval_minutes', 60),
        'daily_time': data.get('daily_time', '08:00'),
        'weekly_day': data.get('weekly_day', 0),
        'agent_id': data.get('agent_id') or None,
        'save_to_chat': data.get('save_to_chat', False),
        'chat_id': None,
        'last_run': None,
        'last_error': None,
    }
    save_autoprompt(ap)
    if _service:
        _service.reload(ap['id'])
    return jsonify(ap), 201


@autoprompts_bp.route('/api/autoprompts/<ap_id>', methods=['PUT'])
def update_autoprompt(ap_id):
    existing = get_autoprompt(ap_id)
    if not existing:
        return jsonify({'error': 'Nicht gefunden'}), 404
    data = request.get_json()
    existing.update({
        'name': data.get('name', existing['name']),
        'prompt': data.get('prompt', existing['prompt']),
        'enabled': data.get('enabled', existing['enabled']),
        'schedule_type': data.get('schedule_type', existing['schedule_type']),
        'interval_minutes': data.get('interval_minutes', existing['interval_minutes']),
        'daily_time': data.get('daily_time', existing['daily_time']),
        'weekly_day': data.get('weekly_day', existing['weekly_day']),
        'agent_id': data.get('agent_id') or None,
        'save_to_chat': data.get('save_to_chat', existing.get('save_to_chat', False)),
    })
    save_autoprompt(existing)
    if _service:
        _service.reload(ap_id)
    return jsonify(existing)


@autoprompts_bp.route('/api/autoprompts/<ap_id>', methods=['DELETE'])
def remove_autoprompt(ap_id):
    delete_autoprompt(ap_id)
    if _service:
        _service.remove(ap_id)
    return jsonify({'success': True})


EXPORT_VERSION = 1

EXPORT_FIELDS = ['name', 'prompt', 'enabled', 'schedule_type', 'interval_minutes',
                 'daily_time', 'weekly_day', 'agent_id', 'save_to_chat']

@autoprompts_bp.route('/api/autoprompts/export', methods=['GET'])
def export_autoprompts():
    data = [{k: ap.get(k) for k in EXPORT_FIELDS} for ap in get_autoprompts()]
    payload = {
        'type': 'openguenther_autoprompts',
        'version': EXPORT_VERSION,
        'exported_at': datetime.now(timezone.utc).isoformat(),
        'data': data,
    }
    return Response(
        json.dumps(payload, ensure_ascii=False, indent=2),
        mimetype='application/json',
        headers={'Content-Disposition': 'attachment; filename="autoprompts.json"'}
    )


@autoprompts_bp.route('/api/autoprompts/import', methods=['POST'])
def import_autoprompts():
    payload = request.get_json()
    if not payload or payload.get('type') != 'openguenther_autoprompts':
        return jsonify({'error': 'Ungültiges Format'}), 400
    if payload.get('version', 1) > EXPORT_VERSION:
        return jsonify({'error': f'Version {payload["version"]} wird nicht unterstützt (max: {EXPORT_VERSION})'}), 400
    added = 0
    for ap in payload.get('data', []):
        if not ap.get('name') or not ap.get('prompt'):
            continue
        new = {k: ap.get(k) for k in EXPORT_FIELDS}
        new.update({'id': str(uuid.uuid4()), 'chat_id': None, 'last_run': None, 'last_error': None})
        save_autoprompt(new)
        if _service:
            _service.reload(new['id'])
        added += 1
    return jsonify({'success': True, 'added': added})


@autoprompts_bp.route('/api/autoprompts/<ap_id>/run', methods=['POST'])
def run_autoprompt_now(ap_id):
    ap = get_autoprompt(ap_id)
    if not ap:
        return jsonify({'error': 'Nicht gefunden'}), 404
    if _service:
        import threading
        t = threading.Thread(target=_service._run, args=[ap_id], daemon=True)
        t.start()
        return jsonify({'success': True, 'message': 'Autoprompt wird ausgeführt...'})
    return jsonify({'error': 'Service nicht verfügbar'}), 500
