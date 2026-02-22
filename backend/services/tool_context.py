"""Thread-local context so tool handlers can emit log entries to the terminal."""
import threading

_ctx = threading.local()


def set_emit_log(fn):
    _ctx.fn = fn


def get_emit_log():
    return getattr(_ctx, 'fn', None)
