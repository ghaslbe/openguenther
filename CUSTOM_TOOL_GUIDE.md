# Custom Tool Guide — OpenGuenther MCP Tools

This guide explains how to create your own MCP tools for OpenGuenther.
Custom tools are loaded automatically at startup — no code changes to the core application are needed.

---

## Where to put your tool

Each tool lives in its own subdirectory inside the persistent data volume:

```
/app/data/custom_tools/
└── my_tool/
    ├── tool.py          ← required: tool definition + handler
    └── helpers.py       ← optional: helper modules (importable from tool.py)
```

> **Note:** `/app/data/` is a Docker volume and persists across container restarts and rebuilds.
> Built-in tools live in `backend/mcp/tools/` inside the image and follow the same conventions.

---

## Minimal example — single tool

```python
# /app/data/custom_tools/hello/tool.py

TOOL_DEFINITION = {
    "name": "say_hello",
    "description": "Greets a person by name.",
    "input_schema": {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "The name to greet"
            }
        },
        "required": ["name"]
    }
}


def handler(name):
    return {"message": f"Hello, {name}!"}
```

That's it. On the next reload the tool is available to the agent.

---

## Reloading tools at runtime

After adding or editing a custom tool, trigger a reload without restarting:

```
POST /api/mcp/reload
```

Or click **"MCP neu laden"** in the Settings UI.

---

## `TOOL_DEFINITION` reference

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | yes | Unique tool name (snake_case). The agent uses this name to call the tool. |
| `description` | string | yes | What the tool does. Used by the LLM to decide when to use it — be descriptive. |
| `input_schema` | object | yes | JSON Schema (type `"object"`) describing the parameters. |

### `input_schema` structure

```python
"input_schema": {
    "type": "object",
    "properties": {
        "param_name": {
            "type": "string",        # string | integer | number | boolean | array | object
            "description": "..."     # shown to the LLM — be specific
        },
        "optional_param": {
            "type": "integer",
            "description": "Days to look ahead (default: 1)"
        }
    },
    "required": ["param_name"]       # list only mandatory params
}
```

---

## Handler function

The handler receives the parameters from `input_schema` as **keyword arguments** and must return a JSON-serializable value (dict, list, string, number, or bool).

```python
def handler(param_name, optional_param=1):
    # do something
    return {"result": "..."}
```

**Alternative:** name the function after the tool instead of `handler`:

```python
def say_hello(name):
    return {"message": f"Hello, {name}!"}
```

Both conventions work. `handler` takes priority if both exist.

### Return values

| Return type | What the agent sees |
|-------------|---------------------|
| `dict` | JSON object |
| `list` | JSON array |
| `str` | plain text |
| `{"error": "..."}` | error message shown to agent |

---

## Optional: `SETTINGS_SCHEMA` — configurable tool settings

If your tool needs configuration (API keys, URLs, timeouts), define a settings schema. The settings are stored in `/app/data/settings.json` and editable in the UI under **Settings → Tools**.

```python
SETTINGS_SCHEMA = [
    {
        "key": "api_key",
        "label": "API Key",
        "type": "password",          # text | password | number
        "placeholder": "sk-...",
        "description": "Your API key from example.com"
    },
    {
        "key": "timeout",
        "label": "Timeout (s)",
        "type": "number",
        "default": "10",
        "description": "Request timeout in seconds"
    }
]
```

Read settings in your handler:

```python
from config import get_tool_settings

def handler(query):
    settings = get_tool_settings("my_tool_name")
    api_key = settings.get("api_key", "")
    timeout = int(settings.get("timeout") or 10)
    # ...
```

---

## Advanced: multiple tools in one file

Use `TOOL_DEFINITIONS` (list) + `HANDLERS` (dict) to register multiple tools from a single `tool.py`:

```python
# /app/data/custom_tools/math_tools/tool.py

def add(a, b):
    return {"result": a + b}

def multiply(a, b):
    return {"result": a * b}


TOOL_DEFINITIONS = [
    {
        "name": "add_numbers",
        "description": "Adds two numbers.",
        "input_schema": {
            "type": "object",
            "properties": {
                "a": {"type": "number", "description": "First number"},
                "b": {"type": "number", "description": "Second number"}
            },
            "required": ["a", "b"]
        }
    },
    {
        "name": "multiply_numbers",
        "description": "Multiplies two numbers.",
        "input_schema": {
            "type": "object",
            "properties": {
                "a": {"type": "number", "description": "First number"},
                "b": {"type": "number", "description": "Second number"}
            },
            "required": ["a", "b"]
        }
    }
]

HANDLERS = {
    "add_numbers": add,
    "multiply_numbers": multiply,
}
```

---

## Helper modules

You can split your tool into multiple files. The tool's directory is automatically added to `sys.path`, so you can import from sibling files directly:

```
/app/data/custom_tools/my_tool/
├── tool.py
└── utils.py
```

```python
# tool.py
from utils import format_result   # works without any path manipulation

def handler(input):
    return format_result(input)
```

---

## Logging

Use the `emit_log` context to send log messages to the terminal panel in the UI:

```python
from services.tool_context import get_emit_log

def handler(query):
    emit_log = get_emit_log()
    if emit_log:
        emit_log({"type": "text", "message": f"Fetching data for: {query}"})
    # ...
```

Log entry types: `text`, `json`, `header`, `error`

```python
emit_log({"type": "json", "label": "response", "data": {"key": "value"}})
emit_log({"type": "error", "message": "Something went wrong"})
```

---

## Complete example with external API

```python
# /app/data/custom_tools/exchange_rate/tool.py
import requests
from config import get_tool_settings

SETTINGS_SCHEMA = [
    {
        "key": "timeout",
        "label": "Timeout (s)",
        "type": "number",
        "default": "10",
        "description": "HTTP request timeout in seconds"
    }
]

TOOL_DEFINITION = {
    "name": "get_exchange_rate",
    "description": "Returns the current exchange rate between two currencies. Example: USD to EUR.",
    "input_schema": {
        "type": "object",
        "properties": {
            "from_currency": {
                "type": "string",
                "description": "Source currency code, e.g. 'USD'"
            },
            "to_currency": {
                "type": "string",
                "description": "Target currency code, e.g. 'EUR'"
            }
        },
        "required": ["from_currency", "to_currency"]
    }
}


def handler(from_currency, to_currency):
    settings = get_tool_settings("get_exchange_rate")
    timeout = int(settings.get("timeout") or 10)

    url = f"https://api.frankfurter.app/latest?from={from_currency}&to={to_currency}"
    try:
        resp = requests.get(url, timeout=timeout)
        data = resp.json()
    except Exception as e:
        return {"error": str(e)}

    if "rates" not in data:
        return {"error": f"Currency '{to_currency}' not found"}

    rate = data["rates"].get(to_currency.upper())
    return {
        "from": from_currency.upper(),
        "to": to_currency.upper(),
        "rate": rate,
        "date": data.get("date")
    }
```

---

## Checklist

- [ ] Directory: `/app/data/custom_tools/<tool_name>/`
- [ ] File: `tool.py` with `TOOL_DEFINITION` and `handler` function (or function named after the tool)
- [ ] `TOOL_DEFINITION.name` is unique (no collision with built-in tools)
- [ ] `input_schema` uses `"type": "object"` at the top level
- [ ] Handler returns a JSON-serializable value
- [ ] (Optional) `SETTINGS_SCHEMA` defined for configurable tools
- [ ] Reload via `POST /api/mcp/reload` or Settings UI

---

## Built-in tools overview

For reference, these tools ship with OpenGuenther:

| Tool name | Description |
|-----------|-------------|
| `calculate` | Safe math expression evaluator |
| `roll_dice` | Dice roller (NdM notation) |
| `get_current_time` | Current date and time |
| `generate_password` | Secure random password |
| `generate_qr_code` | QR code as image |
| `get_weather` | Weather forecast via Open-Meteo |
| `wikipedia_search` | Wikipedia article search |
| `get_stock_price` | Stock price via yfinance |
| `geocode_location` | Address/ZIP → coordinates via OSM |
| `get_flights_nearby` | Live flights near coordinates via OpenSky |
| `resolve_callsign` | ICAO callsign → airline name |
| `analyze_seo` | SEO analysis with HTML report |
| `text_to_speech` | TTS via ElevenLabs |
| `run_code` | Python code interpreter (sandboxed venv) |
| `send_email` | Email via SMTP |
| `generate_image` | Image generation via LLM |
| `process_image` | Image analysis via vision model |
| `text_to_image` | Text rendered as PNG |
| `list_available_tools` | List all registered tools |
| `get_help` | Help about Guenther and its features |
