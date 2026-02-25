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
from mcp.registry import registry, MCPTool
from mcp.tools.time_tool import get_current_time, TOOL_DEFINITION as TIME_TOOL_DEF
from mcp.tools.text_to_image import text_to_image, TOOL_DEFINITION as IMAGE_TOOL_DEF, SETTINGS_SCHEMA as IMAGE_SETTINGS
from mcp.tools.dice_tool import roll_dice, TOOL_DEFINITION as DICE_TOOL_DEF
from mcp.tools.calculator_tool import calculate, TOOL_DEFINITION as CALC_TOOL_DEF
from mcp.tools.qr_code_tool import generate_qr_code, TOOL_DEFINITION as QR_TOOL_DEF
from mcp.tools.password_tool import generate_password, TOOL_DEFINITION as PW_TOOL_DEF
from mcp.tools.seo_tool import analyze_seo, TOOL_DEFINITION as SEO_TOOL_DEF
from mcp.tools.email_tool import send_email, TOOL_DEFINITION as EMAIL_TOOL_DEF, SETTINGS_SCHEMA as EMAIL_SETTINGS
from mcp.tools.help_tool import list_available_tools, get_help, LIST_TOOLS_DEFINITION, HELP_DEFINITION
from mcp.tools.image_process_tool import process_image, TOOL_DEFINITION as IMG_PROCESS_TOOL_DEF
from mcp.tools.image_gen_tool import generate_image, TOOL_DEFINITION as IMG_GEN_TOOL_DEF, SETTINGS_SCHEMA as IMG_GEN_SETTINGS
from mcp.tools.weather_tool import get_weather, TOOL_DEFINITION as WEATHER_TOOL_DEF
from mcp.tools.wikipedia_tool import wikipedia_search, TOOL_DEFINITION as WIKI_TOOL_DEF
from mcp.tools.tts_tool import text_to_speech, TOOL_DEFINITION as TTS_DEF, SETTINGS_SCHEMA as TTS_SETTINGS
from mcp.tools.code_interpreter_tool import run_code, TOOL_DEFINITION as CODE_TOOL_DEF, SETTINGS_SCHEMA as CODE_SETTINGS
from mcp.tools.stock_tool import get_stock_price, TOOL_DEFINITION as STOCK_TOOL_DEF
from mcp.tools.geocode_tool import geocode_location, TOOL_DEFINITION as GEOCODE_TOOL_DEF
from mcp.tools.flights_tool import get_flights_nearby, TOOL_DEFINITION as FLIGHTS_TOOL_DEF
from mcp.tools.callsign_tool import resolve_callsign, TOOL_DEFINITION as CALLSIGN_TOOL_DEF
from mcp.manager import load_external_tools
from services.agent import run_agent
from services.telegram_gateway import TelegramGateway

app = Flask(__name__, static_folder='../frontend/dist', static_url_path='')
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")
telegram_gateway = TelegramGateway(socketio)

app.register_blueprint(chat_bp)
app.register_blueprint(settings_bp)
app.register_blueprint(agents_bp)

# Initialize database
os.makedirs(DATA_DIR, exist_ok=True)
init_db()

# Register built-in MCP tools
registry.register(MCPTool(
    name=TIME_TOOL_DEF['name'],
    description=TIME_TOOL_DEF['description'],
    input_schema=TIME_TOOL_DEF['input_schema'],
    handler=get_current_time
))

registry.register(MCPTool(
    name=IMAGE_TOOL_DEF['name'],
    description=IMAGE_TOOL_DEF['description'],
    input_schema=IMAGE_TOOL_DEF['input_schema'],
    handler=text_to_image,
    settings_schema=IMAGE_SETTINGS
))

registry.register(MCPTool(
    name=DICE_TOOL_DEF['name'],
    description=DICE_TOOL_DEF['description'],
    input_schema=DICE_TOOL_DEF['input_schema'],
    handler=roll_dice
))

registry.register(MCPTool(
    name=CALC_TOOL_DEF['name'],
    description=CALC_TOOL_DEF['description'],
    input_schema=CALC_TOOL_DEF['input_schema'],
    handler=calculate
))

registry.register(MCPTool(
    name=QR_TOOL_DEF['name'],
    description=QR_TOOL_DEF['description'],
    input_schema=QR_TOOL_DEF['input_schema'],
    handler=generate_qr_code
))

registry.register(MCPTool(
    name=PW_TOOL_DEF['name'],
    description=PW_TOOL_DEF['description'],
    input_schema=PW_TOOL_DEF['input_schema'],
    handler=generate_password
))

registry.register(MCPTool(
    name=SEO_TOOL_DEF['name'],
    description=SEO_TOOL_DEF['description'],
    input_schema=SEO_TOOL_DEF['input_schema'],
    handler=analyze_seo
))

registry.register(MCPTool(
    name=EMAIL_TOOL_DEF['name'],
    description=EMAIL_TOOL_DEF['description'],
    input_schema=EMAIL_TOOL_DEF['input_schema'],
    handler=send_email,
    settings_schema=EMAIL_SETTINGS
))

registry.register(MCPTool(
    name=LIST_TOOLS_DEFINITION['name'],
    description=LIST_TOOLS_DEFINITION['description'],
    input_schema=LIST_TOOLS_DEFINITION['input_schema'],
    handler=list_available_tools
))

registry.register(MCPTool(
    name=HELP_DEFINITION['name'],
    description=HELP_DEFINITION['description'],
    input_schema=HELP_DEFINITION['input_schema'],
    handler=get_help
))

registry.register(MCPTool(
    name=IMG_PROCESS_TOOL_DEF['name'],
    description=IMG_PROCESS_TOOL_DEF['description'],
    input_schema=IMG_PROCESS_TOOL_DEF['input_schema'],
    handler=process_image
))

registry.register(MCPTool(
    name=IMG_GEN_TOOL_DEF['name'],
    description=IMG_GEN_TOOL_DEF['description'],
    input_schema=IMG_GEN_TOOL_DEF['input_schema'],
    handler=generate_image,
    settings_schema=IMG_GEN_SETTINGS,
    agent_overridable=False
))

registry.register(MCPTool(
    name=WEATHER_TOOL_DEF['name'],
    description=WEATHER_TOOL_DEF['description'],
    input_schema=WEATHER_TOOL_DEF['input_schema'],
    handler=get_weather
))

registry.register(MCPTool(
    name=WIKI_TOOL_DEF['name'],
    description=WIKI_TOOL_DEF['description'],
    input_schema=WIKI_TOOL_DEF['input_schema'],
    handler=wikipedia_search
))

registry.register(MCPTool(
    name=TTS_DEF['name'],
    description=TTS_DEF['description'],
    input_schema=TTS_DEF['input_schema'],
    handler=text_to_speech,
    settings_schema=TTS_SETTINGS,
    agent_overridable=False
))

registry.register(MCPTool(
    name=CODE_TOOL_DEF['name'],
    description=CODE_TOOL_DEF['description'],
    input_schema=CODE_TOOL_DEF['input_schema'],
    handler=run_code,
    settings_schema=CODE_SETTINGS
))

registry.register(MCPTool(
    name=STOCK_TOOL_DEF['name'],
    description=STOCK_TOOL_DEF['description'],
    input_schema=STOCK_TOOL_DEF['input_schema'],
    handler=get_stock_price
))

registry.register(MCPTool(
    name=GEOCODE_TOOL_DEF['name'],
    description=GEOCODE_TOOL_DEF['description'],
    input_schema=GEOCODE_TOOL_DEF['input_schema'],
    handler=geocode_location
))

registry.register(MCPTool(
    name=FLIGHTS_TOOL_DEF['name'],
    description=FLIGHTS_TOOL_DEF['description'],
    input_schema=FLIGHTS_TOOL_DEF['input_schema'],
    handler=get_flights_nearby
))

registry.register(MCPTool(
    name=CALLSIGN_TOOL_DEF['name'],
    description=CALLSIGN_TOOL_DEF['description'],
    input_schema=CALLSIGN_TOOL_DEF['input_schema'],
    handler=resolve_callsign
))


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
            "has_settings": bool(t.settings_schema),
            "settings_schema": t.settings_schema or [],
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

    # Resolve optional agent system_prompt
    agent_system_prompt = None
    if agent_id:
        agent_cfg = get_agent(agent_id)
        if agent_cfg:
            agent_system_prompt = agent_cfg.get('system_prompt') or None

    try:
        response = run_agent(messages, settings, emit_log, system_prompt=agent_system_prompt)
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


if __name__ == '__main__':
    socketio.run(
        app,
        host='0.0.0.0',
        port=5000,
        debug=os.environ.get('DEBUG', 'false').lower() == 'true',
        allow_unsafe_werkzeug=True
    )
