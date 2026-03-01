import os
import re
import base64
import shutil

from config import FILES_DIR


def _chat_dir(chat_id):
    return os.path.join(FILES_DIR, str(chat_id))


def save_file(chat_id, filename, data: bytes):
    d = _chat_dir(chat_id)
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, filename), 'wb') as f:
        f.write(data)


def get_file(chat_id, filename) -> bytes | None:
    path = os.path.join(_chat_dir(chat_id), filename)
    try:
        with open(path, 'rb') as f:
            return f.read()
    except FileNotFoundError:
        return None


def delete_chat_files(chat_id):
    d = _chat_dir(chat_id)
    if os.path.exists(d):
        shutil.rmtree(d)


def list_chat_files(chat_id):
    d = _chat_dir(chat_id)
    if not os.path.exists(d):
        return []
    return sorted(os.listdir(d))


def extract_and_store(response: str, chat_id: int) -> str:
    """
    Processes special file markers in the LLM response and stores files on disk.

    Supported markers:
      [PPTX_DOWNLOAD](filename::base64)  — base64-encoded file (legacy)
      [LOCAL_FILE](/abs/path/to/file)    — file already on disk (e.g. from a tool)
    Both are replaced with [STORED_FILE](filename) for the frontend.
    """
    # ── [PPTX_DOWNLOAD](filename::base64) ──────────────────────────────────────
    def replace_pptx(m):
        filename = m.group(1)
        b64 = m.group(2)
        try:
            save_file(chat_id, filename, base64.b64decode(b64))
            return f'[STORED_FILE]({filename})'
        except Exception:
            return m.group(0)

    response = re.sub(
        r'\[PPTX_DOWNLOAD\]\(([^:)]+)::([A-Za-z0-9+/=\n]+)\)',
        replace_pptx,
        response
    )

    # ── [LOCAL_FILE](/abs/path) ─────────────────────────────────────────────────
    def replace_local(m):
        src_path = m.group(1)
        filename = os.path.basename(src_path)
        try:
            with open(src_path, 'rb') as f:
                save_file(chat_id, filename, f.read())
            return f'[STORED_FILE]({filename})'
        except Exception:
            return m.group(0)

    response = re.sub(
        r'\[LOCAL_FILE\]\(([^)]+)\)',
        replace_local,
        response
    )

    return response
