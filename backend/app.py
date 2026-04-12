import os
import json
import threading
import uuid
from flask import Flask, send_from_directory
from flask_socketio import SocketIO, emit
from flask_cors import CORS

from flask import request as flask_request
from config import get_settings, get_tool_settings, save_tool_settings, DATA_DIR, get_agent
from models import init_db, get_chat, add_message, create_chat, update_chat_title
from routes.chat import chat_bp
from routes.settings import settings_bp
from routes.agents import agents_bp
from routes.autoprompts import autoprompts_bp, set_service as set_autoprompt_service
from routes.usage import usage_bp
from routes.webhooks import webhooks_bp
from routes.custom_tools import custom_tools_bp
from routes.storage import storage_bp
from mcp.registry import registry, MCPTool
from mcp.loader import load_builtin_tools, load_custom_tools, get_startup_errors
from mcp.manager import load_external_tools
from services.agent import run_agent
from services import file_store
from services.telegram_gateway import TelegramGateway
from services.autoprompt import AutopromptService

app = Flask(__name__, static_folder='../frontend/dist', static_url_path='')
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")
telegram_gateway = TelegramGateway(socketio)

app.register_blueprint(chat_bp)
app.register_blueprint(settings_bp)
app.register_blueprint(agents_bp)
app.register_blueprint(autoprompts_bp)
app.register_blueprint(usage_bp)
app.register_blueprint(webhooks_bp)
app.register_blueprint(custom_tools_bp)
app.register_blueprint(storage_bp)

_cancel_flags = {}  # sid → threading.Event

# Initialize database
os.makedirs(DATA_DIR, exist_ok=True)
init_db()

# Register built-in and custom MCP tools via auto-discovery
load_builtin_tools()
load_custom_tools()
load_external_tools()

# Seed default agents (only if not yet present)
def _seed_default_agents():
    from config import get_agents, save_agents
    agents = get_agents()
    existing_names = {a['name'] for a in agents}
    seeded = []

    if 'Orchestrator' not in existing_names:
        seeded.append({
            'id': str(uuid.uuid4()),
            'name': 'Orchestrator',
            'description': 'Plant komplexe Aufgaben und fuehrt sie Schritt fuer Schritt mit den verfuegbaren Tools aus.',
            'system_prompt': (
                'Du bist ein Orchestrator-Agent. Deine Aufgabe ist es, komplexe Ziele '
                'systematisch zu planen und auszufuehren.\n\n'
                'VORGEHEN BEI JEDER AUFGABE:\n'
                '1. Rufe zuerst plan_task(goal="<Aufgabe>") auf, um einen strukturierten '
                'Plan auf Basis der verfuegbaren Tools zu erstellen.\n'
                '2. Praesentiiere den Plan dem Nutzer klar und uebersichtlich (nummerierte Schritte).\n'
                '3. Frage explizit: "Soll ich so vorgehen, oder moechtest du etwas aendern?" '
                '— und warte auf die Antwort.\n'
                '4. Erst nach Bestaetigung fuehre die Schritte nacheinander aus.\n'
                '5. Berichte nach jedem Schritt kurz das Ergebnis (1-2 Saetze).\n'
                '6. Passe den Plan an, wenn ein Schritt fehlschlaegt — erklaere kurz warum '
                'und frage ob du weitermachen sollst.\n'
                '7. Fasse am Ende zusammen, was erreicht wurde.\n\n'
                'WICHTIG:\n'
                '- Beginne IMMER mit plan_task — auch bei scheinbar einfachen Aufgaben.\n'
                '- Stelle den Plan VOR der Ausfuehrung vor und warte auf gruenes Licht.\n'
                '- Wenn ein Tool fehlt, sage es dem Nutzer klar.\n'
                '- Antworte praegnant — keine langen Erklaerungen zwischen den Schritten.'
            ),
            'provider_id': '',
            'model': '',
        })

    if seeded:
        agents.extend(seeded)
        save_agents(agents)

_seed_default_agents()


# ── Static file serving ──

@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/<path:path>')
def serve_static(path):
    file_path = os.path.join(app.static_folder, path)
    if os.path.exists(file_path):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, 'index.html')


# ── API: reload external MCP tools ──

@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in flask_request.files:
        return {'error': 'No file provided'}, 400
    f = flask_request.files['file']
    uploads_dir = os.path.join(DATA_DIR, 'uploads')
    os.makedirs(uploads_dir, exist_ok=True)
    safe_name = f"{uuid.uuid4().hex}_{f.filename}"
    file_path = os.path.join(uploads_dir, safe_name)
    f.save(file_path)
    return {'path': file_path}


@app.route('/api/mcp/reload', methods=['POST'])
def reload_mcp():
    logs = []
    def _log(entry):
        logs.append(entry if isinstance(entry, dict) else {"type": "text", "message": str(entry)})
        socketio.emit('guenther_log', entry if isinstance(entry, dict) else {"type": "text", "message": str(entry)})
    load_custom_tools(emit_log=_log)
    load_external_tools(emit_log=_log)
    return {"success": True, "logs": logs}


@app.route('/api/mcp/tools', methods=['GET'])
def list_mcp_tools():
    tools = registry.list_tools()
    result = []
    for t in tools:
        ts = get_tool_settings(t.name)
        result.append({
            "name": t.name,
            "description": t.description,
            "server_id": t.server_id,
            "builtin": t.server_id is None,
            "custom": t.custom,
            "has_settings": bool(t.settings_schema),
            "settings_schema": t.settings_schema or [],
            "settings_info": t.settings_info or "",
            "agent_overridable": t.agent_overridable,
            "current_provider": ts.get("provider", ""),
            "current_model": ts.get("model", ""),
            "enabled": ts.get("enabled", True),
            "always_enabled": t.always_enabled,
        })
    return result


@app.route('/api/mcp/tools/<tool_name>/enabled', methods=['PUT'])
def set_tool_enabled_route(tool_name):
    data = flask_request.get_json() or {}
    enabled = bool(data.get('enabled', True))
    ts = get_tool_settings(tool_name)
    ts['enabled'] = enabled
    save_tool_settings(tool_name, ts)
    return {"success": True}


@app.route('/api/mcp/tools/<tool_name>/settings', methods=['GET'])
def get_tool_settings_route(tool_name):
    tool = registry.get_tool(tool_name)
    if not tool:
        return {"error": "Tool nicht gefunden"}, 404
    return {
        "name": tool_name,
        "schema": tool.settings_schema or [],
        "values": get_tool_settings(tool_name)
    }


@app.route('/api/mcp/tools/<tool_name>/settings', methods=['PUT'])
def update_tool_settings_route(tool_name):
    tool = registry.get_tool(tool_name)
    if not tool:
        return {"error": "Tool nicht gefunden"}, 404
    data = flask_request.get_json()
    save_tool_settings(tool_name, data)
    return {"success": True}


# ── WebSocket events ──

@socketio.on('connect')
def handle_connect():
    emit('guenther_log', {'type': 'header', 'message': 'G U E N T H E R  v1.0 - MCP Agent Terminal'})
    emit('guenther_log', {'type': 'text', 'message': 'Verbindung hergestellt.'})

    tools = registry.list_tools()
    tool_info = [
        {"name": t.name, "description": t.description, "builtin": t.server_id is None}
        for t in tools
    ]
    emit('guenther_log', {'type': 'text', 'message': f'Registrierte Tools: {len(tools)}'})
    emit('guenther_log', {'type': 'json', 'label': 'tools', 'data': tool_info})
    emit('guenther_log', {'type': 'text', 'message': 'Warte auf Eingabe...'})

    for err in get_startup_errors():
        emit('guenther_log', {'type': 'text', 'message': err})


@socketio.on('send_message')
def handle_message(data):
    chat_id = data.get('chat_id')
    content = data.get('content', '').strip()
    agent_id = data.get('agent_id') or None
    file_name = data.get('file_name', '')
    file_content = data.get('file_content', '')
    if not content and not file_content:
        return

    # Prepend file content to message so the LLM can work with it
    # Binary files are uploaded via /api/upload first; their path is already in content.
    # Only text files still send file_content inline here.
    if file_name and file_content:
        content = f"[Datei: {file_name}]\n```\n{file_content}\n```\n\n{content}" if content else f"[Datei: {file_name}]\n```\n{file_content}\n```"

    # Create new chat if needed
    if not chat_id:
        title = content[:50] + ('...' if len(content) > 50 else '')
        chat_id = create_chat(title, agent_id=agent_id)
        emit('chat_created', {'chat_id': chat_id, 'title': title, 'agent_id': agent_id})
    else:
        agent_id = None  # will be loaded from existing chat below

    # Save user message
    add_message(chat_id, 'user', content)

    # Get chat history for context
    chat = get_chat(chat_id)
    messages = []
    for msg in chat.get('messages', []):
        if msg['role'] in ('user', 'assistant'):
            messages.append({
                'role': msg['role'],
                'content': msg['content']
            })


    # For existing chats, read agent_id from DB
    if agent_id is None:
        agent_id = chat.get('agent_id')

    # Update title on first real user message.
    # For agent chats the first message is the auto-greeting "Hallo", so we
    # also update the title on the second user message (= first real input).
    user_messages = [m for m in messages if m['role'] == 'user']
    is_first_real_message = (
        len(user_messages) == 1 or
        (len(user_messages) == 2 and bool(chat.get('agent_id')))
    )
    if is_first_real_message:
        title = content[:50] + ('...' if len(content) > 50 else '')
        update_chat_title(chat_id, title)
        emit('chat_updated', {'chat_id': chat_id, 'title': title})

    settings = get_settings()

    def emit_log(entry):
        """Accepts structured log entries (dict) or plain strings."""
        if isinstance(entry, dict):
            socketio.emit('guenther_log', entry)
        else:
            socketio.emit('guenther_log', {'type': 'text', 'message': str(entry)})

    emit('agent_start', {'chat_id': chat_id})

    sid = flask_request.sid
    stop_event = threading.Event()
    _cancel_flags[sid] = stop_event

    # Resolve optional agent system_prompt + provider/model overrides
    agent_system_prompt = None
    agent_provider_id = None
    agent_model = None
    if agent_id:
        agent_cfg = get_agent(agent_id)
        if agent_cfg:
            agent_system_prompt = agent_cfg.get('system_prompt') or None
            agent_provider_id = agent_cfg.get('provider_id') or None
            agent_model = agent_cfg.get('model') or None

    # Beim initialen Agent-Greeting (neuer Chat mit agent_id) keine Tools nötig
    is_agent_start = bool(agent_id and len(messages) == 1)

    try:
        response = run_agent(messages, settings, emit_log, system_prompt=agent_system_prompt,
                             agent_provider_id=agent_provider_id, agent_model=agent_model, chat_id=chat_id,
                             stop_event=stop_event, no_tools=is_agent_start)
        if stop_event.is_set():
            emit_log({"type": "text", "message": "⏹ Generierung abgebrochen."})
            emit('agent_end', {'chat_id': chat_id, 'cancelled': True})
            return
        response = file_store.extract_and_store(response, chat_id)
        add_message(chat_id, 'assistant', response)
        emit('agent_response', {
            'chat_id': chat_id,
            'content': response
        })
    except Exception as e:
        error_msg = f"Fehler: {str(e)}"
        emit_log(f"KRITISCHER FEHLER: {error_msg}")
        add_message(chat_id, 'assistant', error_msg)
        emit('agent_response', {
            'chat_id': chat_id,
            'content': error_msg
        })
    finally:
        _cancel_flags.pop(sid, None)

    emit('agent_end', {'chat_id': chat_id})



@socketio.on('cancel_generation')
def handle_cancel():
    flag = _cancel_flags.get(flask_request.sid)
    if flag:
        flag.set()
        socketio.emit('guenther_log', {"type": "text", "message": "⏹ Abbruch angefordert..."})


@socketio.on('disconnect')
def handle_disconnect():
    _cancel_flags.pop(flask_request.sid, None)


# Auto-start Telegram gateway if token is configured
_tg_token = get_settings().get('telegram', {}).get('bot_token', '')
if _tg_token:
    telegram_gateway.start(_tg_token)

# Start Autoprompt scheduler
_autoprompt_service = AutopromptService(socketio)
set_autoprompt_service(_autoprompt_service)


if __name__ == '__main__':
    socketio.run(
        app,
        host='0.0.0.0',
        port=5000,
        debug=os.environ.get('DEBUG', 'false').lower() == 'true',
        allow_unsafe_werkzeug=True
    )
