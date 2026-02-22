import os
import json

DATA_DIR = os.environ.get('DATA_DIR', '/app/data')
SETTINGS_FILE = os.path.join(DATA_DIR, 'settings.json')
DB_FILE = os.path.join(DATA_DIR, 'guenther.db')

DEFAULT_SETTINGS = {
    'openrouter_api_key': '',
    'model': 'openai/gpt-4o-mini',
    'temperature': 0.5,
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
    'providers': {
        'openrouter': {'name': 'OpenRouter', 'base_url': 'https://openrouter.ai/api/v1', 'api_key': '', 'enabled': True},
        'ollama':     {'name': 'Ollama',     'base_url': 'http://localhost:11434/v1',    'api_key': '', 'enabled': False},
        'lmstudio':   {'name': 'LM Studio',  'base_url': 'http://localhost:1234/v1',     'api_key': '', 'enabled': False},
    },
    'default_provider': 'openrouter',
}


def get_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'r') as f:
            settings = json.load(f)
            for key in DEFAULT_SETTINGS:
                if key not in settings:
                    settings[key] = DEFAULT_SETTINGS[key]

            # Ensure all provider keys exist in stored providers
            stored_providers = settings.get('providers', {})
            for pid, pdefault in DEFAULT_SETTINGS['providers'].items():
                if pid not in stored_providers:
                    stored_providers[pid] = pdefault.copy()
                else:
                    for k, v in pdefault.items():
                        if k not in stored_providers[pid]:
                            stored_providers[pid][k] = v
            settings['providers'] = stored_providers

            # Migration: copy openrouter_api_key into providers.openrouter.api_key
            legacy_key = settings.get('openrouter_api_key', '')
            if legacy_key and not settings['providers']['openrouter'].get('api_key'):
                settings['providers']['openrouter']['api_key'] = legacy_key

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
