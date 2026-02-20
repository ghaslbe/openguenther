import requests

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

SYSTEM_PROMPT = """Du bist Guenther, ein hilfreicher KI-Assistent mit Zugang zu verschiedenen Werkzeugen (MCP Tools).

Wenn der Benutzer eine Aufgabe stellt, die Werkzeuge erfordert:
1. Analysiere, welche Werkzeuge du benoetigen wirst
2. Erstelle einen kurzen Plan und teile ihn dem Benutzer mit
3. Fuehre die Werkzeuge Schritt fuer Schritt aus
4. Fasse das Ergebnis zusammen

Wenn mehrere Werkzeuge nacheinander noetig sind (z.B. erst die Uhrzeit holen, dann als Bild darstellen), rufe sie in der richtigen Reihenfolge auf.

Antworte auf Deutsch, es sei denn, der Benutzer schreibt in einer anderen Sprache.
Sei praezise und hilfreich."""


def call_openrouter(messages, tools=None, api_key='', model='openai/gpt-4o-mini'):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://guenther.app",
        "X-Title": "Guenther"
    }

    payload = {
        "model": model,
        "messages": messages,
    }

    if tools:
        payload["tools"] = tools
        payload["tool_choice"] = "auto"

    response = requests.post(
        OPENROUTER_API_URL,
        headers=headers,
        json=payload,
        timeout=120
    )
    response.raise_for_status()
    return response.json()
