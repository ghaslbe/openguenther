import os
import re
import sys
import json
import shutil
import subprocess
import tempfile

from config import DATA_DIR, get_settings, get_tool_settings
from services.openrouter import call_openrouter
from services.tool_context import get_emit_log

MAX_LOOPS = 15
CUSTOM_TOOLS_DIR = os.path.join(DATA_DIR, 'custom_tools')

SETTINGS_INFO = """**MCP Tool Builder**

Erstellt oder bearbeitet Custom MCP-Tools per natürlichsprachlicher Beschreibung.
Der Builder generiert den Code per LLM, testet ihn in einer isolierten venv, installiert
fehlende Pakete automatisch und korrigiert sich bei Fehlern selbst — bis zu 15 Iterationen.

Ein Code-spezialisiertes Modell (z.B. `openai/gpt-4o`, `anthropic/claude-3-5-sonnet`) empfiehlt sich für komplexe Tools."""

SETTINGS_SCHEMA = [
    {
        "key": "model",
        "label": "Code-Generierungs-Modell",
        "type": "text",
        "placeholder": "leer = Hauptmodell verwenden",
        "description": "Optionales Modell für die Tool-Code-Generierung"
    }
]

TOOL_DEFINITION = {
    "name": "build_mcp_tool",
    "description": (
        "Erstellt oder bearbeitet ein Custom MCP-Tool. "
        "Einfach beschreiben was das Tool tun soll — Code wird per LLM generiert, "
        "in einer venv getestet, fehlende Pakete automatisch installiert und Fehler "
        "bis zu 15 Mal selbstständig korrigiert. Das fertige Tool ist sofort aktiv. "
        "Falls tool_name eines bestehenden Custom Tools angegeben wird: Edit-Modus."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "description": {
                "type": "string",
                "description": (
                    "Was soll das Tool tun? Möglichst konkret: "
                    "z.B. 'Tool das YouTube Transkripte per Video-URL abruft' oder "
                    "'Tool das den aktuellen Bitcoin-Preis von CoinGecko holt'"
                )
            },
            "tool_name": {
                "type": "string",
                "description": (
                    "Optionaler Name (snake_case). Wird automatisch generiert wenn leer. "
                    "Wenn ein bestehendes Custom Tool angegeben wird: Edit-Modus."
                )
            }
        },
        "required": ["description"]
    }
}


def handler(description: str, tool_name: str = "") -> dict:
    emit_log = get_emit_log()
    settings = get_settings()
    tool_cfg = get_tool_settings("build_mcp_tool")

    provider_id = settings.get('default_provider', 'openrouter')
    providers = settings.get('providers', {})
    provider_cfg = providers.get(provider_id, {})
    api_key = provider_cfg.get('api_key', '') or settings.get('openrouter_api_key', '')
    base_url = provider_cfg.get('base_url', 'https://openrouter.ai/api/v1')
    model = (tool_cfg.get('model') or '').strip() or settings.get('model', 'openai/gpt-4o-mini')

    def log(msg: str):
        if emit_log:
            emit_log({"type": "text", "message": msg})

    def header(msg: str):
        if emit_log:
            emit_log({"type": "header", "message": msg})

    def llm(messages):
        return call_openrouter(messages, None, api_key, model, temperature=0.1, base_url=base_url)

    # ── Determine mode ─────────────────────────────────────────────────────────
    safe_name = re.sub(r'[^a-z0-9_]', '_', tool_name.lower().strip()) if tool_name.strip() else ""
    existing_code = ""
    edit_mode = False

    if safe_name:
        existing_py = os.path.join(CUSTOM_TOOLS_DIR, safe_name, 'tool.py')
        if os.path.isfile(existing_py):
            edit_mode = True
            with open(existing_py, 'r', encoding='utf-8') as f:
                existing_code = f.read()
            header(f"BUILD MCP TOOL: EDIT '{safe_name}'")
            log("Bestehender Code als Basis geladen.")
        else:
            header(f"BUILD MCP TOOL: NEU '{safe_name}'")
    else:
        header("BUILD MCP TOOL: STARTE")

    log(f"Aufgabe: {description}")
    log(f"Modell: {model}")

    # ── Phase 1: Generate initial code ────────────────────────────────────────
    header("BUILD MCP TOOL: CODE-GENERIERUNG")
    gen_prompt = _build_gen_prompt(description, safe_name, existing_code)
    try:
        resp = llm([{"role": "user", "content": gen_prompt}])
    except Exception as e:
        return {"success": False, "error": f"LLM-Fehler: {e}"}

    raw = resp.get("choices", [{}])[0].get("message", {}).get("content", "")
    _log_tokens(resp, log)

    parsed = _parse_json(raw)
    if not parsed or not parsed.get("code"):
        return {"success": False, "error": "LLM hat keinen gültigen Code zurückgegeben"}

    if not safe_name:
        generated_name = parsed.get("tool_name", "custom_tool")
        safe_name = re.sub(r'[^a-z0-9_]', '_', generated_name.lower()) or "custom_tool"

    code = parsed["code"].strip()
    requirements = (parsed.get("requirements") or "").strip()

    header("BUILD MCP TOOL: GENERIERTER CODE")
    log(code[:1200] + (" …[gekürzt]" if len(code) > 1200 else ""))
    if requirements:
        log(f"Requirements: {requirements.replace(chr(10), ', ')}")

    # ── Phase 2: Venv test + self-correction loop ──────────────────────────────
    tmpdir = tempfile.mkdtemp()
    loop = 0
    try:
        header("BUILD MCP TOOL: VENV ERSTELLEN")
        venv_dir = os.path.join(tmpdir, "venv")
        r = subprocess.run(
            ["python", "-m", "venv", venv_dir],
            capture_output=True, text=True, timeout=60
        )
        if r.returncode != 0:
            return {"success": False, "error": f"venv-Fehler: {r.stderr[:300]}"}
        log("venv bereit.")

        venv_python = os.path.join(venv_dir, "bin", "python")
        venv_pip = os.path.join(venv_dir, "bin", "pip")

        for loop in range(1, MAX_LOOPS + 1):
            header(f"BUILD MCP TOOL: VERSUCH {loop}/{MAX_LOOPS}")

            # Write tool.py
            with open(os.path.join(tmpdir, "tool.py"), 'w', encoding='utf-8') as f:
                f.write(code)

            # Install requirements
            if requirements:
                req_path = os.path.join(tmpdir, "requirements.txt")
                with open(req_path, 'w', encoding='utf-8') as f:
                    f.write(requirements)
                log(f"pip install: {requirements.replace(chr(10), ', ')}")
                pip_r = subprocess.run(
                    [venv_pip, "install", "-r", "requirements.txt", "-q"],
                    cwd=tmpdir, capture_output=True, text=True, timeout=120
                )
                if pip_r.returncode != 0:
                    err = (pip_r.stderr + pip_r.stdout).strip()[:500]
                    log(f"pip-Fehler: {err}")
                    if loop < MAX_LOOPS:
                        fix = _ask_fix(llm, description, code, requirements, f"pip install failed:\n{err}", log)
                        if fix:
                            code = fix.get("code") or code
                            requirements = (fix.get("requirements") or requirements).strip()
                        continue
                    return {"success": False, "error": f"pip install fehlgeschlagen: {err}"}
                log("Pakete installiert.")

            # Write and run test runner
            runner = os.path.join(tmpdir, "test_runner.py")
            with open(runner, 'w', encoding='utf-8') as f:
                f.write(_test_runner_script())

            result = subprocess.run(
                [venv_python, "test_runner.py"],
                cwd=tmpdir, capture_output=True, text=True, timeout=30
            )

            if result.returncode == 0:
                log(f"Test OK: {result.stdout.strip()}")
                break
            else:
                err = (result.stderr + result.stdout).strip()[:600]
                log(f"Test-Fehler: {err}")

                if loop >= MAX_LOOPS:
                    return {
                        "success": False,
                        "error": f"Test fehlgeschlagen nach {MAX_LOOPS} Versuchen.\nLetzter Fehler:\n{err}"
                    }

                fix = _ask_fix(llm, description, code, requirements, err, log)
                if fix:
                    code = fix.get("code") or code
                    requirements = (fix.get("requirements") or requirements).strip()
                    header("BUILD MCP TOOL: KORRIGIERTER CODE")
                    log(code[:800] + (" …[gekürzt]" if len(code) > 800 else ""))
                    if requirements:
                        log(f"Requirements: {requirements.replace(chr(10), ', ')}")

        # ── Phase 3: Install packages into Flask Python ───────────────────────
        if requirements:
            pkgs = [p.strip() for p in requirements.splitlines() if p.strip()]
            log(f"Installiere ins System-Python: {', '.join(pkgs)}")
            sys_pip = subprocess.run(
                [sys.executable, '-m', 'pip', 'install'] + pkgs + ['-q'],
                capture_output=True, text=True, timeout=180
            )
            if sys_pip.returncode != 0:
                log(f"Warnung: System-pip teilweise fehlgeschlagen: {sys_pip.stderr[:300]}")

        # ── Phase 4: Write + register ─────────────────────────────────────────
        header("BUILD MCP TOOL: DEPLOY")
        tool_dir_final = os.path.join(CUSTOM_TOOLS_DIR, safe_name)
        os.makedirs(tool_dir_final, exist_ok=True)
        final_tool_py = os.path.join(tool_dir_final, 'tool.py')

        # Unregister old version in edit mode
        if edit_mode and os.path.isfile(final_tool_py):
            try:
                from mcp.loader import _load_module
                from mcp.registry import registry
                old_mod = _load_module(final_tool_py, f'custom_tools.{safe_name}_old')
                old_td = getattr(old_mod, 'TOOL_DEFINITION', None)
                old_tds = getattr(old_mod, 'TOOL_DEFINITIONS', None)
                if old_td:
                    registry.unregister(old_td['name'])
                    log(f"Altes Tool '{old_td['name']}' deregistriert")
                elif old_tds:
                    for t in old_tds:
                        registry.unregister(t['name'])
                        log(f"Altes Tool '{t['name']}' deregistriert")
            except Exception as e:
                log(f"Hinweis: Deregistrierung fehlgeschlagen: {e}")

        with open(final_tool_py, 'w', encoding='utf-8') as f:
            f.write(code)

        from mcp.loader import _load_module, _register_module
        mod = _load_module(final_tool_py, f'custom_tools.{safe_name}')
        count = _register_module(mod, f'custom/{safe_name}', custom=True)

        if count == 0:
            if not edit_mode:
                shutil.rmtree(tool_dir_final, ignore_errors=True)
            return {"success": False, "error": "Tool geladen, aber nicht registriert — TOOL_DEFINITION prüfen"}

        log(f"'{safe_name}' registriert ({count} Tool(s))")
        header("BUILD MCP TOOL: FERTIG")

        # Build return info
        td = getattr(mod, 'TOOL_DEFINITION', None)
        tds = getattr(mod, 'TOOL_DEFINITIONS', None)
        registered_names = [td['name']] if td else [t['name'] for t in (tds or [])]
        has_settings = bool(getattr(mod, 'SETTINGS_SCHEMA', None))

        return {
            "success": True,
            "tool_name": safe_name,
            "registered_tools": registered_names,
            "mode": "edit" if edit_mode else "create",
            "loops_used": loop,
            "has_settings": has_settings,
            "hint": (
                f"Tool '{registered_names[0]}' ist jetzt aktiv. "
                + ("Konfigurierbare Einstellungen (z.B. API-Key) findest du unter Einstellungen → MCP Tools." if has_settings else "")
            )
        }

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _build_gen_prompt(description: str, tool_name: str, existing_code: str) -> str:
    name_hint = f'\nUse this exact tool_name in your response: "{tool_name}"' if tool_name else ""
    edit_section = ""
    if existing_code:
        edit_section = f"\n\nEXISTING CODE (modify as needed based on the description):\n```python\n{existing_code}\n```"

    return f"""You are an expert Python developer creating MCP tools for OpenGuenther, a self-hosted AI agent.

TASK: {description}{name_hint}{edit_section}

Generate a complete, working tool.py following this format:

```python
# Imports — only use packages available via pip or Python stdlib
import requests  # example
from config import get_tool_settings   # only if tool needs configurable settings
from services.tool_context import get_emit_log  # only if you want terminal logging

# SETTINGS_SCHEMA — define only if the tool needs configuration (API keys, URLs, etc.)
SETTINGS_SCHEMA = [
    {{"key": "api_key", "label": "API Key", "type": "password", "placeholder": "sk-...", "description": "Your API key"}},
    {{"key": "base_url", "label": "Base URL", "type": "text", "default": "https://...", "description": "API endpoint"}},
]

TOOL_DEFINITION = {{
    "name": "tool_name",       # snake_case, descriptive, unique
    "description": "What this tool does — be specific, this text is read by the AI agent",
    "input_schema": {{
        "type": "object",
        "properties": {{
            "param": {{"type": "string", "description": "clear description for the AI"}},
            "optional_param": {{"type": "integer", "description": "optional, default 10"}}
        }},
        "required": ["param"]
    }}
}}

def handler(param, optional_param=10):
    settings = get_tool_settings("tool_name")  # only if using SETTINGS_SCHEMA
    api_key = settings.get("api_key", "")
    # ... implementation
    try:
        # actual logic
        return {{"result": "..."}}
    except Exception as e:
        return {{"error": str(e)}}
```

CRITICAL RULE — HANDLER SIGNATURE:
The handler function MUST accept the input_schema properties as individual keyword arguments.
NEVER use def handler(params) or def handler(data) or def handler(**kwargs) alone.

CORRECT:   def handler(url):                   # if input_schema has property "url"
CORRECT:   def handler(query, max_results=10): # if schema has "query" (required) and "max_results" (optional)
WRONG:     def handler(params):                # ← THIS BREAKS THE TOOL, never do this
WRONG:     def handler(data):                  # ← same problem
WRONG:     def handler(**kwargs):              # ← only acceptable if combined with explicit params

RULES:
- Use SETTINGS_SCHEMA for API keys/tokens — never hardcode credentials in code
- For HTTP requests: always set a realistic browser User-Agent header
- Handle all errors with try/except, return {{"error": "message"}} on failure
- Keep the handler focused — do one thing well
- List ALL non-stdlib packages needed in requirements (one per line)
- Do not import from openguenther internals except config.get_tool_settings and services.tool_context.get_emit_log

Respond ONLY with valid JSON (no text before or after, no markdown wrapping):
{{
  "tool_name": "snake_case_name",
  "code": "complete tool.py content as a single string with \\n for newlines",
  "requirements": "package1\\npackage2"
}}"""


def _ask_fix(llm_fn, description: str, code: str, requirements: str, error: str, log) -> dict | None:
    prompt = f"""You are debugging an MCP tool for OpenGuenther. Fix the code based on the error.

TASK: {description}

CURRENT CODE:
```python
{code}
```

CURRENT REQUIREMENTS: {requirements or "(none)"}

ERROR:
{error}

Common fixes:
- ModuleNotFoundError / ImportError: add the missing package to requirements, fix the import
- AttributeError on mock: the code uses an internal module incorrectly — simplify imports
- AssertionError "Missing TOOL_DEFINITION": make sure TOOL_DEFINITION is at module level, not inside a function
- AssertionError "No callable handler": define a `handler` function or a function named after the tool
- AssertionError "wrong signature" / "missing parameter": handler must accept keyword arguments
  matching input_schema properties. NEVER use def handler(params) or def handler(data).
  CORRECT: def handler(url) for schema property "url"
  CORRECT: def handler(query, limit=10) for properties "query" and "limit"
- pip install failed: use a different package name or version, or find an alternative library

Respond ONLY with valid JSON:
{{
  "code": "fixed complete tool.py",
  "requirements": "updated requirements, one package per line"
}}"""

    try:
        resp = llm_fn([{"role": "user", "content": prompt}])
        raw = resp.get("choices", [{}])[0].get("message", {}).get("content", "")
        _log_tokens(resp, log)
        return _parse_json(raw)
    except Exception as e:
        log(f"Fix-LLM-Fehler: {e}")
        return None


def _parse_json(text: str) -> dict | None:
    """Parse JSON from LLM response, stripping markdown wrappers."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        end = len(lines) - 1
        while end > 0 and lines[end].strip() in ("```", "```json"):
            end -= 1
        text = "\n".join(lines[1:end + 1]).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find('{')
        end = text.rfind('}')
        if start >= 0 and end > start:
            try:
                return json.loads(text[start:end + 1])
            except Exception:
                pass
        return None


def _log_tokens(response: dict, log):
    usage = response.get("usage", {})
    if usage:
        log(f"Tokens: prompt={usage.get('prompt_tokens', '?')} completion={usage.get('completion_tokens', '?')}")


def _test_runner_script() -> str:
    """Returns the Python script that validates tool.py in the isolated venv."""
    return r"""
import sys
import types
import importlib.util


class _FlexMod(types.ModuleType):
    """Module mock that allows any attribute access without AttributeError."""
    def __getattr__(self, name):
        child = _FlexMod(f"{self.__name__}.{name}")
        setattr(self, name, child)
        return child
    def __call__(self, *a, **kw):
        return None


def _mock(name, **attrs):
    m = _FlexMod(name)
    for k, v in attrs.items():
        setattr(m, k, v)
    return m


# Register mocks for all openguenther-internal modules
sys.modules['config'] = _mock('config',
    DATA_DIR='/tmp',
    get_settings=lambda: {},
    get_tool_settings=lambda n: {},
    save_tool_settings=lambda n, v: None,
    DB_FILE='/tmp/test.db',
    SETTINGS_FILE='/tmp/settings.json',
)
sys.modules['services'] = _mock('services')
sys.modules['services.tool_context'] = _mock('services.tool_context',
    get_emit_log=lambda: None)
sys.modules['services.openrouter'] = _mock('services.openrouter',
    call_openrouter=lambda *a, **k: {"choices": [{"message": {"content": ""}}]})
sys.modules['services.file_store'] = _mock('services.file_store')
sys.modules['flask'] = _mock('flask',
    Blueprint=lambda *a, **k: _mock('bp'),
    request=_mock('request'),
    jsonify=lambda x: x,
    Response=object,
    current_app=_mock('current_app'),
)

# Load tool.py
spec = importlib.util.spec_from_file_location('tool_under_test', 'tool.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

# Validate structure
td = getattr(mod, 'TOOL_DEFINITION', None)
tds = getattr(mod, 'TOOL_DEFINITIONS', None)

assert td is not None or tds is not None, \
    "Missing TOOL_DEFINITION or TOOL_DEFINITIONS at module level"

if td is not None:
    assert isinstance(td, dict), "TOOL_DEFINITION must be a dict"
    for key in ('name', 'description', 'input_schema'):
        assert key in td, f"TOOL_DEFINITION missing required key: '{key}'"
    assert isinstance(td['input_schema'], dict), "input_schema must be a dict"
    h = getattr(mod, 'handler', None) or getattr(mod, td['name'], None)
    assert h is not None, f"No handler function found (define 'handler' or '{td['name']}')"
    assert callable(h), "handler is not callable"

    # Validate handler signature against input_schema
    import inspect
    props = list(td['input_schema'].get('properties', {}).keys())
    required_params = td['input_schema'].get('required', [])
    sig = inspect.signature(h)
    sig_params = sig.parameters
    has_var_kw = any(p.kind == inspect.Parameter.VAR_KEYWORD for p in sig_params.values())
    positional = [n for n, p in sig_params.items()
                  if p.kind in (inspect.Parameter.POSITIONAL_OR_KEYWORD,
                                inspect.Parameter.POSITIONAL_ONLY,
                                inspect.Parameter.KEYWORD_ONLY)]
    # Catch def handler(params) / def handler(data) anti-pattern:
    # single arg whose name doesn't match any schema property
    if len(positional) == 1 and props and positional[0] not in props and not has_var_kw:
        assert False, (
            f"Wrong handler signature: def handler({positional[0]}) — "
            f"handler must accept keyword arguments matching input_schema properties {props}. "
            f"Fix: def handler({', '.join(props)})"
        )
    # Ensure all required schema params are present (unless **kwargs used)
    if not has_var_kw:
        for req in required_params:
            assert req in sig_params, (
                f"handler missing required parameter '{req}' from input_schema. "
                f"Fix: def handler({', '.join(props)})"
            )
    print(f"OK|{td['name']}|{td['description'][:70]}")
else:
    assert isinstance(tds, list) and len(tds) > 0, \
        "TOOL_DEFINITIONS must be a non-empty list"
    names = []
    for t in tds:
        for key in ('name', 'description', 'input_schema'):
            assert key in t, f"TOOL_DEFINITIONS entry missing '{key}'"
        h = getattr(mod, 'handler', None) or getattr(mod, t['name'], None)
        assert h is not None and callable(h), \
            f"No callable handler for tool '{t['name']}'"
        names.append(t['name'])
    print(f"OK|{','.join(names)}|multi-tool")
"""
