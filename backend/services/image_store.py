"""
Temporary in-memory storage for images shared between gateway and tools.
Images are stored by session key (e.g. "tg_username") and cleaned up after use.
"""
import threading

_lock = threading.Lock()
_images = {}  # key -> {"b64": str, "mime": str}


def store(key, b64, mime):
    with _lock:
        _images[key] = {"b64": b64, "mime": mime}


def get(key):
    with _lock:
        return _images.get(key)


def remove(key):
    with _lock:
        _images.pop(key, None)
