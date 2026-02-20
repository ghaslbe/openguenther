from mcp.client import MCPStdioClient
from mcp.registry import registry, MCPTool
from config import get_settings

active_clients = {}


def load_external_tools(emit_log=None):
    """Connect to configured external MCP servers and register their tools."""
    settings = get_settings()
    servers = settings.get('mcp_servers', [])

    # Disconnect existing external clients
    for sid, entry in list(active_clients.items()):
        try:
            registry.unregister_by_server(sid)
            entry['client'].disconnect()
        except Exception:
            pass
    active_clients.clear()

    for server in servers:
        if not server.get('enabled', True):
            continue

        sid = server['id']
        name = server.get('name', sid)

        if emit_log:
            emit_log(f"Verbinde mit MCP Server: {name}...")

        try:
            if server.get('transport', 'stdio') == 'stdio':
                client = MCPStdioClient(
                    server['command'],
                    server.get('args', [])
                )
                client.connect()
                tools = client.list_tools()

                for tool_def in tools:
                    tool_name = tool_def['name']

                    def make_handler(c, n):
                        def handler(**kwargs):
                            result = c.call_tool(n, kwargs)
                            # MCP returns content array, extract text
                            if isinstance(result, dict) and 'content' in result:
                                contents = result['content']
                                if isinstance(contents, list) and len(contents) > 0:
                                    first = contents[0]
                                    if first.get('type') == 'text':
                                        return {"result": first['text']}
                                    elif first.get('type') == 'image':
                                        return {
                                            "image_base64": first.get('data', ''),
                                            "mime_type": first.get('mimeType', 'image/png')
                                        }
                            return result
                        return handler

                    mcp_tool = MCPTool(
                        name=tool_name,
                        description=tool_def.get('description', ''),
                        input_schema=tool_def.get('inputSchema', {"type": "object", "properties": {}}),
                        handler=make_handler(client, tool_name),
                        server_id=sid
                    )
                    registry.register(mcp_tool)

                active_clients[sid] = {'client': client}

                if emit_log:
                    emit_log(f"  OK {len(tools)} Tools geladen von {name}")
            else:
                if emit_log:
                    emit_log(f"  Transport '{server.get('transport')}' noch nicht unterstuetzt")

        except Exception as e:
            if emit_log:
                emit_log(f"  FEHLER bei {name}: {str(e)}")


def disconnect_all():
    for sid, entry in active_clients.items():
        try:
            entry['client'].disconnect()
        except Exception:
            pass
    active_clients.clear()
