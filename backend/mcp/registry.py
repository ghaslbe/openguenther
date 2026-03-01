class MCPTool:
    def __init__(self, name, description, input_schema, handler=None, server_id=None, settings_schema=None, agent_overridable=True, settings_info=None, custom=False, usage=None):
        self.name = name
        self.description = description
        self.input_schema = input_schema
        self.handler = handler
        self.server_id = server_id  # None for built-in tools
        self.settings_schema = settings_schema  # List of field defs for tool-specific settings
        self.agent_overridable = agent_overridable  # False for tools that make their own API calls (e.g. generate_image)
        self.settings_info = settings_info  # Optional markdown info text shown in settings UI
        self.custom = custom  # True for tools loaded from /app/data/custom_tools/
        self.usage = usage  # Optional usage hints appended to description for the model

    def to_openai_format(self):
        desc = self.description
        if self.usage:
            desc = f"{desc}\n\nVerwendung:\n{self.usage.strip()}"
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": desc,
                "parameters": self.input_schema
            }
        }


class MCPRegistry:
    def __init__(self):
        self.tools = {}

    def register(self, tool):
        self.tools[tool.name] = tool

    def unregister(self, name):
        if name in self.tools:
            del self.tools[name]

    def get_tool(self, name):
        return self.tools.get(name)

    def list_tools(self):
        return list(self.tools.values())

    def get_openai_tools(self):
        return [tool.to_openai_format() for tool in self.tools.values()]

    def unregister_by_server(self, server_id):
        to_remove = [n for n, t in self.tools.items() if t.server_id == server_id]
        for name in to_remove:
            del self.tools[name]


registry = MCPRegistry()
