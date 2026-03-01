"""Thread-local context so tool handlers can emit log entries to the terminal."""
import threading

_ctx = threading.local()


def set_emit_log(fn):
    _ctx.fn = fn


def get_emit_log():
    return getattr(_ctx, 'fn', None)


def set_current_chat_id(chat_id):
    _ctx.chat_id = chat_id


def get_current_chat_id():
    return getattr(_ctx, 'chat_id', None)
