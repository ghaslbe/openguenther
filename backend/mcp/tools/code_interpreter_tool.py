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
        "Eingabedaten (z.B. Dateiinhalt) werden dem Skript via stdin übergeben."
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

    log(f"[Code-Interpreter] Aufgabe: {task[:120]}")
    log(f"[Code-Interpreter] Modell: {model} | Input: {len(input_data)} Zeichen")

    prompt = _build_prompt(task, input_data)
    messages = [{"role": "user", "content": prompt}]

    try:
        response = call_openrouter(
            messages, None, api_key, model,
            temperature=0.1, base_url=base_url
        )
    except Exception as e:
        return {"success": False, "output": "", "error": f"LLM-Fehler: {str(e)}"}

    raw = response.get("choices", [{}])[0].get("message", {}).get("content", "")
    code = _extract_code(raw)

    if not code:
        return {"success": False, "output": "", "error": "LLM hat keinen ausfuehrbaren Code generiert"}

    log(f"[Code-Interpreter] Code generiert ({len(code)} Zeichen) — führe aus...")

    tmpdir = tempfile.mkdtemp()
    try:
        script_path = os.path.join(tmpdir, "script.py")
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(code)

        result = subprocess.run(
            ["python", "script.py"],
            cwd=tmpdir,
            input=input_data,
            capture_output=True,
            text=True,
            timeout=30
        )

        stdout = result.stdout.strip()
        stderr = result.stderr.strip()

        if result.returncode != 0:
            log(f"[Code-Interpreter] Fehler bei Ausführung: {stderr[:200]}")
            return {"success": False, "output": stdout, "error": stderr}

        log(f"[Code-Interpreter] Erfolgreich. Output: {len(stdout)} Zeichen")
        return {"success": True, "output": stdout, "error": ""}

    except subprocess.TimeoutExpired:
        return {"success": False, "output": "", "error": "Timeout: Skript überschritt 30 Sekunden"}
    except Exception as e:
        return {"success": False, "output": "", "error": str(e)}
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def _build_prompt(task: str, input_data: str) -> str:
    if input_data:
        sample = "\n".join(input_data.splitlines()[:10])
        data_section = f"""Es gibt Eingabedaten. Das Skript soll sie mit `sys.stdin.read()` lesen.
Erste Zeilen der Daten:
```
{sample}
```
Das Ergebnis muss nach stdout ausgegeben werden (print() oder sys.stdout.write())."""
    else:
        data_section = "Es gibt keine Eingabedaten. Das Skript führt die Aufgabe selbstständig aus und schreibt das Ergebnis nach stdout."

    return f"""Du bist ein Python-Code-Generator. Schreibe ein Python-Skript für folgende Aufgabe:

AUFGABE: {task}

{data_section}

REGELN:
- Nur Python-Standardbibliothek (sys, json, csv, re, collections, datetime usw.)
- Fehlerbehandlung mit try/except
- Ergebnis immer nach stdout

Antworte NUR mit dem Code-Block:
```python
# dein code hier
```"""


def _extract_code(text: str) -> str:
    text = text.strip()
    if "```python" in text:
        start = text.index("```python") + len("```python")
        end = text.rindex("```")
        return text[start:end].strip()
    if text.startswith("```") and "```" in text[3:]:
        start = text.index("\n") + 1
        end = text.rindex("```")
        return text[start:end].strip()
    # Kein Codeblock — trotzdem zurückgeben wenn es wie Code aussieht
    if any(kw in text for kw in ("import ", "def ", "print(", "sys.")):
        return text
    return ""
