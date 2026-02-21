import requests

WHISPER_URL = "https://api.openai.com/v1/audio/transcriptions"


def transcribe_with_whisper(audio_bytes, audio_format, api_key, model="whisper-1"):
    """
    Transkribiert Audio via OpenAI Whisper API.
    Gibt den transkribierten Text zurück oder wirft eine Exception.
    """
    headers = {"Authorization": f"Bearer {api_key}"}
    files = {
        "file": (f"audio.{audio_format}", audio_bytes, f"audio/{audio_format}"),
        "model": (None, model),
    }
    response = requests.post(WHISPER_URL, headers=headers, files=files, timeout=60)

    if not response.ok:
        try:
            err = response.json().get("error", {})
            msg = err.get("message", response.text) if isinstance(err, dict) else str(err)
        except Exception:
            msg = response.text or response.reason
        raise requests.HTTPError(f"Whisper API {response.status_code}: {msg}")

    return response.json().get("text", "").strip()
