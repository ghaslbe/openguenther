import os
import json
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
from mcp.registry import registry, MCPTool
from mcp.loader import load_builtin_tools, load_custom_tools
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

# Initialize database
os.makedirs(DATA_DIR, exist_ok=True)
init_db()

# Register built-in and custom MCP tools via auto-discovery
load_builtin_tools()
load_custom_tools()
load_external_tools()


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

@app.route('/api/mcp/reload', methods=['POST'])
def reload_mcp():
    logs = []
    load_external_tools(emit_log=lambda msg: logs.append(msg))
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
        })
    return result


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

    # Update title on first message
    if len(messages) == 1:
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

    try:
        response = run_agent(messages, settings, emit_log, system_prompt=agent_system_prompt,
                             agent_provider_id=agent_provider_id, agent_model=agent_model, chat_id=chat_id)
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

    emit('agent_end', {'chat_id': chat_id})


@socketio.on('disconnect')
def handle_disconnect():
    pass


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
