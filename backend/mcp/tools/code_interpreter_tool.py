import json
import subprocess
import tempfile
import shutil
import os

from config import get_settings, get_tool_settings
from services.openrouter import call_openrouter
from services.tool_context import get_emit_log

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
        "Berechnungen oder Textanalysen. "
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
                    "oder 'Berechne den Durchschnitt aller Zahlenwerte'"
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

    header("CODE-INTERPRETER GESTARTET")
    log(f"Aufgabe: {task}")
    log(f"Modell: {model} | Eingabedaten: {len(input_data)} Zeichen")

    prompt = _build_prompt(task, input_data)

    header("CODE-INTERPRETER: LLM-ANFRAGE")
    log(prompt)

    messages = [{"role": "user", "content": prompt}]

    try:
        response = call_openrouter(
            messages, None, api_key, model,
            temperature=0.1, base_url=base_url
        )
    except Exception as e:
        log(f"FEHLER LLM-Anfrage: {str(e)}")
        return {"success": False, "output": "", "error": f"LLM-Fehler: {str(e)}"}

    raw = response.get("choices", [{}])[0].get("message", {}).get("content", "")
    usage = response.get("usage", {})
    if usage:
        log(f"Tokens: prompt={usage.get('prompt_tokens','?')} completion={usage.get('completion_tokens','?')}")

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
        # Write files
        with open(os.path.join(tmpdir, "script.py"), "w", encoding="utf-8") as f:
            f.write(script)
        if requirements:
            with open(os.path.join(tmpdir, "requirements.txt"), "w", encoding="utf-8") as f:
                f.write(requirements)

        # Paths for venv binaries (Linux/Docker)
        venv_dir = os.path.join(tmpdir, "venv")
        venv_python = os.path.join(venv_dir, "bin", "python")
        venv_pip = os.path.join(venv_dir, "bin", "pip")

        # Create venv
        header("CODE-INTERPRETER: VENV")
        log("Erstelle virtuelle Umgebung...")
        venv_result = subprocess.run(
            ["python", "-m", "venv", venv_dir],
            capture_output=True, text=True, timeout=60
        )
        if venv_result.returncode != 0:
            log(f"venv-Fehler: {venv_result.stderr}")
            return {"success": False, "output": "", "error": f"venv-Fehler: {venv_result.stderr}"}
        log("venv erstellt.")

        # Install requirements if present
        if requirements:
            log("Installiere Abhängigkeiten via pip...")
            pip_result = subprocess.run(
                [venv_pip, "install", "-r", "requirements.txt", "-q"],
                cwd=tmpdir,
                capture_output=True, text=True, timeout=120
            )
            if pip_result.returncode != 0:
                log(f"pip-Fehler: {pip_result.stderr}")
                return {"success": False, "output": "", "error": f"pip install fehlgeschlagen: {pip_result.stderr}"}
            log("Abhängigkeiten installiert.")

        # Run script
        header("CODE-INTERPRETER: AUSFUEHRUNG")
        log(f"Starte script.py mit venv-Python (timeout=60s, stdin={len(input_data)} Zeichen)...")

        result = subprocess.run(
            [venv_python, "script.py"],
            cwd=tmpdir,
            input=input_data,
            capture_output=True,
            text=True,
            timeout=60
        )

        stdout = result.stdout.strip()
        stderr = result.stderr.strip()

        if result.returncode != 0:
            header("CODE-INTERPRETER: FEHLER")
            log(f"returncode={result.returncode}")
            log(stderr)
            return {"success": False, "output": stdout, "error": stderr}

        header("CODE-INTERPRETER: ERGEBNIS")
        log(stdout[:2000] + (" …[gekuerzt]" if len(stdout) > 2000 else ""))
        log(f"Fertig — {len(stdout)} Zeichen Output")
        return {"success": True, "output": stdout, "error": ""}

    except subprocess.TimeoutExpired:
        return {"success": False, "output": "", "error": "Timeout überschritten"}
    except Exception as e:
        return {"success": False, "output": "", "error": str(e)}
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


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
- Beliebige pip-Pakete erlaubt (z.B. beautifulsoup4, pandas, requests)
- Fehlerbehandlung mit try/except einbauen
- Ergebnis immer nach stdout schreiben"""


def _parse_llm_response(text: str) -> tuple[str, str]:
    """Parse LLM response: returns (script, requirements). Both may be empty strings."""
    text = text.strip()

    # Strip markdown code block if wrapped
    if text.startswith("```"):
        lines = text.splitlines()
        # Remove first line (```json or ```) and last line (```)
        inner = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])
        text = inner.strip()

    try:
        data = json.loads(text)
        script = (data.get("script") or "").strip()
        requirements = (data.get("requirements") or "").strip()
        return script, requirements
    except json.JSONDecodeError:
        # Fallback: try to extract a python code block
        if "```python" in text:
            start = text.index("```python") + len("```python")
            end = text.rindex("```")
            return text[start:end].strip(), ""
        if any(kw in text for kw in ("import ", "def ", "print(", "sys.")):
            return text, ""
        return "", ""
