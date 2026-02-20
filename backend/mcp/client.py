import subprocess
import json


class MCPStdioClient:
    """Client for MCP servers communicating over stdio (JSON-RPC 2.0)."""

    def __init__(self, command, args=None, env=None):
        self.command = command
        self.args = args or []
        self.env = env
        self.process = None
        self._id = 0

    def _next_id(self):
        self._id += 1
        return self._id

    def connect(self):
        self.process = subprocess.Popen(
            [self.command] + self.args,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=self.env
        )
        response = self._send_request("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {
                "name": "guenther",
                "version": "1.0.0"
            }
        })
        self._send_notification("notifications/initialized")
        return response

    def _send_request(self, method, params=None):
        msg = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": method,
        }
        if params is not None:
            msg["params"] = params
        return self._send(msg)

    def _send_notification(self, method, params=None):
        msg = {
            "jsonrpc": "2.0",
            "method": method,
        }
        if params is not None:
            msg["params"] = params
        if self.process and self.process.stdin:
            self.process.stdin.write(json.dumps(msg) + '\n')
            self.process.stdin.flush()

    def _send(self, message):
        if not self.process or not self.process.stdin or not self.process.stdout:
            raise RuntimeError("Not connected to MCP server")
        self.process.stdin.write(json.dumps(message) + '\n')
        self.process.stdin.flush()
        line = self.process.stdout.readline()
        if line:
            return json.loads(line.strip())
        return None

    def list_tools(self):
        response = self._send_request("tools/list", {})
        if response and 'result' in response:
            return response['result'].get('tools', [])
        return []

    def call_tool(self, name, arguments=None):
        response = self._send_request("tools/call", {
            "name": name,
            "arguments": arguments or {}
        })
        if response and 'result' in response:
            return response['result']
        if response and 'error' in response:
            return {"error": response['error']}
        return {"error": "No response from MCP server"}

    def disconnect(self):
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except Exception:
                self.process.kill()
            self.process = None
