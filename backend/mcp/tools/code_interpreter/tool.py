import json
import subprocess
import tempfile
import shutil
import os

from config import get_settings, get_tool_settings
from services.openrouter import call_openrouter
from services.tool_context import get_emit_log

SETTINGS_INFO = """**Python Code-Interpreter**

Guenther generiert Python-Code und führt ihn direkt aus — ideal für Datenverarbeitung, Konvertierungen (CSV, JSON, Excel…), Web-Scraping, Berechnungen und Analysen. Benötigte Pakete werden automatisch per `pip` in einer isolierten venv installiert. Kein API-Key nötig.

Ein separates Modell für die Code-Generierung ist optional — leer lassen um das globale Standardmodell zu verwenden. Ein Code-spezialisiertes Modell (z.B. `openai/gpt-4o` oder `anthropic/claude-3.5-sonnet`) kann die Qualität des generierten Codes verbessern."""

SETTINGS_SCHEMA = [
    {
        "key": "model",
        "label": "Code-Generierungs-Modell",
        "type": "text",
        "placeholder": "leer = Hauptmodell verwenden",
        "description": "Optionales Modell für die Code-Generierung (z.B. openai/gpt-4o)"
    }
]

TOOL_DEFINITION = {
    "name": "run_code",
    "description": (
        "Generiert Python-Code via LLM und führt ihn aus. "
        "Ideal für Datenverarbeitung, Konvertierung (CSV→JSON, JSON→XML usw.), "
        "Web-Scraping, Berechnungen oder Textanalysen. "
        "Eingabedaten (z.B. Dateiinhalt) werden dem Skript via stdin übergeben. "
        "Benötigte Bibliotheken werden automatisch in einer venv installiert."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "task": {
                "type": "string",
                "description": (
                    "Was soll der Code tun? Z.B. 'Konvertiere die CSV-Daten zu JSON' "
                    "oder 'Rufe https://example.com ab und extrahiere alle h1-Überschriften'"
                )
            },
            "input_data": {
                "type": "string",
                "description": (
                    "Optionale Eingabedaten (z.B. CSV-Inhalt aus einer hochgeladenen Datei). "
                    "Werden dem Skript via stdin übergeben."
                )
            }
        },
        "required": ["task"]
    }
}

MAX_RETRIES = 2


def run_code(task: str, input_data: str = "") -> dict:
    emit_log = get_emit_log()
    settings = get_settings()
    tool_cfg = get_tool_settings("run_code")

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

    header("CODE-INTERPRETER GESTARTET")
    log(f"Aufgabe: {task}")
    log(f"Modell: {model} | Eingabedaten: {len(input_data)} Zeichen")

    # --- Phase 1: Code generieren ---
    prompt = _build_prompt(task, input_data)
    header("CODE-INTERPRETER: LLM-ANFRAGE")
    log(prompt)

    try:
        response = llm([{"role": "user", "content": prompt}])
    except Exception as e:
        log(f"FEHLER LLM-Anfrage: {str(e)}")
        return {"success": False, "output": "", "error": f"LLM-Fehler: {str(e)}"}

    raw = response.get("choices", [{}])[0].get("message", {}).get("content", "")
    _log_tokens(response, log)

    script, requirements = _parse_llm_response(raw)
    if not script:
        log("FEHLER: Kein ausfuehrbarer Code in LLM-Antwort gefunden")
        return {"success": False, "output": "", "error": "LLM hat keinen ausfuehrbaren Code generiert"}

    header("CODE-INTERPRETER: GENERIERTER CODE")
    log(script)
    if requirements:
        header("CODE-INTERPRETER: REQUIREMENTS")
        log(requirements)

    tmpdir = tempfile.mkdtemp()
    try:
        venv_python, venv_pip = _setup_venv(tmpdir, requirements, log, header)
        if venv_python is None:
            return {"success": False, "output": "", "error": venv_pip}  # venv_pip holds error msg here

        # --- Phase 2: Ausführen + ggf. selbst korrigieren ---
        for attempt in range(1, MAX_RETRIES + 2):  # 1 initial + MAX_RETRIES fixes
            if attempt > 1:
                header(f"CODE-INTERPRETER: KORREKTUR (Versuch {attempt})")

            _write_script(tmpdir, script)

            stdout, stderr, returncode = _run_script(tmpdir, venv_python, input_data, log, header, attempt)

            # Success
            if returncode == 0 and _output_looks_ok(stdout):
                header("CODE-INTERPRETER: ERGEBNIS")
                log(stdout[:2000] + (" …[gekuerzt]" if len(stdout) > 2000 else ""))
                log(f"Fertig — {len(stdout)} Zeichen Output (Versuch {attempt})")
                return {"success": True, "output": stdout, "error": ""}

            # Failure or suspicious output — let LLM fix it
            if attempt <= MAX_RETRIES:
                problem = stderr if returncode != 0 else f"Output war leer oder verdaechtig: '{stdout}'"
                log(f"Versuche Korrektur... Problem: {problem[:300]}")
                fix_prompt = _build_fix_prompt(task, script, requirements, problem)
                try:
                    fix_response = llm([{"role": "user", "content": fix_prompt}])
                except Exception as e:
                    break
                fix_raw = fix_response.get("choices", [{}])[0].get("message", {}).get("content", "")
                _log_tokens(fix_response, log)
                new_script, new_req = _parse_llm_response(fix_raw)
                if new_script:
                    script = new_script
                    header("CODE-INTERPRETER: KORRIGIERTER CODE")
                    log(script)
                    # Install new requirements if changed
                    if new_req and new_req != requirements:
                        requirements = new_req
                        header("CODE-INTERPRETER: NEUE REQUIREMENTS")
                        log(requirements)
                        req_path = os.path.join(tmpdir, "requirements.txt")
                        with open(req_path, "w") as f:
                            f.write(requirements)
                        pip_result = subprocess.run(
                            [venv_pip, "install", "-r", "requirements.txt", "-q"],
                            cwd=tmpdir, capture_output=True, text=True, timeout=120
                        )
                        if pip_result.returncode != 0:
                            log(f"pip-Fehler bei Korrektur: {pip_result.stderr[:200]}")
            else:
                # Final failure
                header("CODE-INTERPRETER: FEHLER (alle Versuche erschoepft)")
                log(f"returncode={returncode}")
                if stderr:
                    log(stderr)
                return {"success": False, "output": stdout, "error": stderr or f"Output leer nach {attempt} Versuchen"}

        return {"success": False, "output": "", "error": "Maximale Korrekturversuche erreicht"}

    except subprocess.TimeoutExpired:
        return {"success": False, "output": "", "error": "Timeout überschritten"}
    except Exception as e:
        return {"success": False, "output": "", "error": str(e)}
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


# ── Helpers ──────────────────────────────────────────────────────────────────

def _setup_venv(tmpdir, requirements, log, header):
    """Create venv, install requirements. Returns (venv_python, venv_pip) or (None, error_msg)."""
    venv_dir = os.path.join(tmpdir, "venv")
    venv_python = os.path.join(venv_dir, "bin", "python")
    venv_pip = os.path.join(venv_dir, "bin", "pip")

    header("CODE-INTERPRETER: VENV")
    log("Erstelle virtuelle Umgebung...")
    r = subprocess.run(["python", "-m", "venv", venv_dir], capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        log(f"venv-Fehler: {r.stderr}")
        return None, f"venv-Fehler: {r.stderr}"
    log("venv erstellt.")

    if requirements:
        req_path = os.path.join(tmpdir, "requirements.txt")
        with open(req_path, "w") as f:
            f.write(requirements)
        log(f"Installiere: {requirements.replace(chr(10), ', ')}")
        pip_r = subprocess.run(
            [venv_pip, "install", "-r", "requirements.txt", "-q"],
            cwd=tmpdir, capture_output=True, text=True, timeout=120
        )
        if pip_r.returncode != 0:
            log(f"pip-Fehler: {pip_r.stderr}")
            return None, f"pip install fehlgeschlagen: {pip_r.stderr}"
        log("Abhängigkeiten installiert.")

    return venv_python, venv_pip


def _write_script(tmpdir, script):
    with open(os.path.join(tmpdir, "script.py"), "w", encoding="utf-8") as f:
        f.write(script)


def _run_script(tmpdir, venv_python, input_data, log, header, attempt):
    header(f"CODE-INTERPRETER: AUSFUEHRUNG (Versuch {attempt})")
    log(f"Starte script.py (timeout=60s)...")
    result = subprocess.run(
        [venv_python, "script.py"],
        cwd=tmpdir, input=input_data,
        capture_output=True, text=True, timeout=60
    )
    return result.stdout.strip(), result.stderr.strip(), result.returncode


def _output_looks_ok(stdout: str) -> bool:
    """Return False if output looks like an empty/failed result."""
    if not stdout:
        return False
    stripped = stdout.strip()
    # Empty collections
    if stripped in ("[]", "{}", "()", "None", ""):
        return False
    return True


def _log_tokens(response, log):
    usage = response.get("usage", {})
    if usage:
        log(f"Tokens: prompt={usage.get('prompt_tokens','?')} completion={usage.get('completion_tokens','?')}")


def _build_prompt(task: str, input_data: str) -> str:
    if input_data:
        sample = "\n".join(input_data.splitlines()[:10])
        data_section = (
            f"Es gibt Eingabedaten. Das Skript soll sie mit `sys.stdin.read()` lesen.\n"
            f"Erste Zeilen der Daten:\n```\n{sample}\n```\n"
            "Das Ergebnis muss nach stdout ausgegeben werden."
        )
    else:
        data_section = "Es gibt keine Eingabedaten. Das Skript führt die Aufgabe selbstständig aus und schreibt das Ergebnis nach stdout."

    return f"""Du bist ein Python-Code-Generator. Schreibe ein Python-Skript für folgende Aufgabe:

AUFGABE: {task}

{data_section}

Antworte AUSSCHLIESSLICH mit einem JSON-Objekt (kein Text davor oder danach):
{{
  "script": "<vollständiger Python-Code als String>",
  "requirements": "<pip-Pakete, eine pro Zeile, oder leer wenn nur Standardbibliothek>"
}}

REGELN:
- Beliebige pip-Pakete erlaubt (beautifulsoup4, pandas, requests, lxml usw.)
- Bei HTTP-Anfragen IMMER einen realistischen User-Agent setzen:
  headers = {{"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}}
- Fehlerbehandlung mit try/except
- Bei Web-Scraping: HTTP-Statuscode und Antwortgröße printen wenn kein Ergebnis
- Ergebnis immer nach stdout schreiben"""


def _build_fix_prompt(task: str, current_script: str, requirements: str, problem: str) -> str:
    return f"""Du bist ein Python-Code-Debugger. Folgender Code hat ein Problem:

AUFGABE: {task}

AKTUELLER CODE:
```python
{current_script}
```

REQUIREMENTS: {requirements or '(keine)'}

PROBLEM:
{problem}

Korrigiere den Code. Häufige Ursachen:
- Bei HTTP/Web: User-Agent fehlt oder zu schwach → setze einen realistischen Browser-User-Agent
- Bei leerem Ergebnis: Website blockiert Bots → teste mit Session, Cookies oder anderen Headern
- Bei leerem Scraping-Ergebnis: HTML-Struktur prüfen, andere Tags/Klassen verwenden, HTML ausgeben zur Analyse

Antworte AUSSCHLIESSLICH mit JSON (kein Text davor oder danach):
{{
  "script": "<korrigierter Python-Code>",
  "requirements": "<pip-Pakete oder leer>"
}}"""


def _parse_llm_response(text: str) -> tuple[str, str]:
    """Parse LLM response: returns (script, requirements). Both may be empty strings."""
    text = text.strip()

    # Strip markdown code block wrapper
    if text.startswith("```"):
        lines = text.splitlines()
        end = len(lines) - 1
        while end > 0 and lines[end].strip() == "```":
            end -= 1
        text = "\n".join(lines[1:end + 1]).strip()

    try:
        data = json.loads(text)
        script = (data.get("script") or "").strip()
        requirements = (data.get("requirements") or "").strip()
        return script, requirements
    except json.JSONDecodeError:
        # Fallback: extract python code block
        if "```python" in text:
            start = text.index("```python") + len("```python")
            end = text.rindex("```")
            return text[start:end].strip(), ""
        if any(kw in text for kw in ("import ", "def ", "print(", "sys.")):
            return text, ""
        return "", ""
