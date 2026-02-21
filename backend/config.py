import os
import json

DATA_DIR = os.environ.get('DATA_DIR', '/app/data')
SETTINGS_FILE = os.path.join(DATA_DIR, 'settings.json')
DB_FILE = os.path.join(DATA_DIR, 'guenther.db')

DEFAULT_SETTINGS = {
    'openrouter_api_key': '',
    'model': 'openai/gpt-4o-mini',
    'stt_model': '',        # Speech-to-Text model via OpenRouter (leer = Hauptmodell verwenden)
    'tts_model': '',        # Text-to-Speech model (leer = Hauptmodell verwenden)
    'image_gen_model': '',  # Bildgenerierungs-Modell (leer = Hauptmodell verwenden)
    'openai_api_key': '',   # OpenAI API Key (für Whisper STT)
    'use_openai_whisper': False,  # Whisper statt OpenRouter für STT verwenden
    'mcp_servers': [],
    'tool_settings': {},
    'telegram': {
        'bot_token': '',
        'allowed_users': [],
    },
}


def get_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'r') as f:
            settings = json.load(f)
            for key in DEFAULT_SETTINGS:
                if key not in settings:
                    settings[key] = DEFAULT_SETTINGS[key]
            return settings
    return DEFAULT_SETTINGS.copy()


def save_settings(settings):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(settings, f, indent=2)


def get_tool_settings(tool_name):
    settings = get_settings()
    return settings.get('tool_settings', {}).get(tool_name, {})


def save_tool_settings(tool_name, tool_cfg):
    settings = get_settings()
    if 'tool_settings' not in settings:
        settings['tool_settings'] = {}
    settings['tool_settings'][tool_name] = tool_cfg
    save_settings(settings)
