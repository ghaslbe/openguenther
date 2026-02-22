import base64
import logging
import requests

logger = logging.getLogger(__name__)

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


def call_openrouter(messages, tools=None, api_key='', model='openai/gpt-4o-mini', temperature=0.5, base_url=None, timeout=120):
    if base_url is None:
        url = OPENROUTER_API_URL
    elif base_url.endswith('/chat/completions'):
        url = base_url
    else:
        url = base_url.rstrip('/') + '/chat/completions'

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://guenther.app",
        "X-Title": "Guenther"
    }

    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
    }

    if tools:
        payload["tools"] = tools
        payload["tool_choice"] = "auto"

    response = requests.post(
        url,
        headers=headers,
        json=payload,
        timeout=timeout
    )

    if not response.ok:
        try:
            error_body = response.json()
            error_detail = error_body.get('error', {})
            if isinstance(error_detail, dict):
                error_msg = error_detail.get('message', str(error_body))
                error_code = error_detail.get('code', response.status_code)
            else:
                error_msg = str(error_detail)
                error_code = response.status_code
        except Exception:
            error_msg = response.text or response.reason
            error_code = response.status_code

        raise requests.HTTPError(
            f"OpenRouter {error_code}: {error_msg}",
            response=response
        )

    return response.json()


def transcribe_audio(audio_bytes, audio_format, api_key, model):
    """
    Transkribiert Audio via OpenRouter multimodal API.
    audio_format: 'ogg', 'mp3', 'wav', 'flac', 'm4a', ...
    Gibt den transkribierten Text zurück.
    """
    audio_b64 = base64.b64encode(audio_bytes).decode()
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "input_audio",
                    "data": audio_b64,
                    "format": audio_format,
                },
                {
                    "type": "text",
                    "text": "Transkribiere das Audio. Gib nur den transkribierten Text zurück, ohne Erklärungen.",
                },
            ],
        }
    ]
    response = call_openrouter(messages, None, api_key, model)
    logger.info(f"STT raw response: {response}")
    return response.get("choices", [{}])[0].get("message", {}).get("content", "").strip()


def generate_image(prompt, api_key, model, aspect_ratio="1:1", timeout=120):
    """
    Generiert ein Bild via OpenRouter image generation API.
    Gibt (image_bytes, mime_type) zurück oder wirft eine Exception.
    """
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://guenther.app",
        "X-Title": "Guenther",
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "modalities": ["image", "text"],
    }
    if aspect_ratio and aspect_ratio != "1:1":
        payload["image_config"] = {"aspect_ratio": aspect_ratio}

    response = requests.post(OPENROUTER_API_URL, headers=headers, json=payload, timeout=timeout)

    if not response.ok:
        try:
            err = response.json().get("error", {})
            msg = err.get("message", response.text) if isinstance(err, dict) else str(err)
        except Exception:
            msg = response.text or response.reason
        raise requests.HTTPError(f"OpenRouter {response.status_code}: {msg}", response=response)

    data = response.json()
    choice = data.get("choices", [{}])[0]
    message = choice.get("message", {})

    # Images can be in message.images or embedded in content as data URIs
    images = message.get("images", [])
    if images:
        url = images[0].get("url", "")
    else:
        # Fallback: search content for data URI
        content = message.get("content", "")
        if "data:image" in str(content):
            import re
            m = re.search(r'data:image/[^"\')\s]+', str(content))
            url = m.group(0) if m else ""
        else:
            url = ""

    if not url:
        raise ValueError("Kein Bild in der API-Antwort gefunden.")

    if url.startswith("data:"):
        # data:image/png;base64,<data>
        header, b64data = url.split(",", 1)
        mime = header.split(";")[0].split(":")[1]
        img_bytes = base64.b64decode(b64data)
    else:
        # Remote URL — download it
        r = requests.get(url, timeout=60)
        r.raise_for_status()
        mime = r.headers.get("Content-Type", "image/png").split(";")[0]
        img_bytes = r.content

    return img_bytes, mime
