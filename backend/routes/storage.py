import os
import mimetypes
from flask import Blueprint, jsonify, request, Response
from models import get_chats
from config import DATA_DIR, FILES_DIR

storage_bp = Blueprint('storage', __name__)

UPLOADS_DIR = os.path.join(DATA_DIR, 'uploads')

_CONFIG_FILES = [
    'settings.json', 'agents.json', 'autoprompts.json',
    'telegram_users.json', 'webhooks.json',
]


def _dir_size(path):
    total = 0
    if os.path.exists(path):
        for dirpath, _, filenames in os.walk(path):
            for fname in filenames:
                try:
                    total += os.path.getsize(os.path.join(dirpath, fname))
                except OSError:
                    pass
    return total


def _safe_full_path(relative_path):
    """Resolve path and verify it stays within DATA_DIR. Returns full path or None."""
    full = os.path.realpath(os.path.join(DATA_DIR, relative_path))
    root = os.path.realpath(DATA_DIR)
    if full.startswith(root + os.sep):
        return full
    return None


@storage_bp.route('/api/storage/info', methods=['GET'])
def get_storage_info():
    # Chat-ID → Titel
    chats = get_chats()
    chat_map = {str(c['id']): c['title'] for c in chats}

    all_files = []

    # Scan files/ (vom LLM/Tool erzeugte Chat-Dateien)
    if os.path.exists(FILES_DIR):
        for chat_id_str in os.listdir(FILES_DIR):
            chat_dir = os.path.join(FILES_DIR, chat_id_str)
            if not os.path.isdir(chat_dir):
                continue
            for filename in os.listdir(chat_dir):
                filepath = os.path.join(chat_dir, filename)
                if not os.path.isfile(filepath):
                    continue
                try:
                    size = os.path.getsize(filepath)
                except OSError:
                    size = 0
                all_files.append({
                    'name': filename,
                    'size': size,
                    'chat_id': chat_id_str,
                    'chat_title': chat_map.get(chat_id_str),
                    'category': 'files',
                    'relative_path': f'files/{chat_id_str}/{filename}',
                })

    # Scan uploads/ (hochgeladene Binärdateien)
    if os.path.exists(UPLOADS_DIR):
        for filename in os.listdir(UPLOADS_DIR):
            filepath = os.path.join(UPLOADS_DIR, filename)
            if not os.path.isfile(filepath):
                continue
            try:
                size = os.path.getsize(filepath)
            except OSError:
                size = 0
            all_files.append({
                'name': filename,
                'size': size,
                'chat_id': None,
                'chat_title': None,
                'category': 'uploads',
                'relative_path': f'uploads/{filename}',
            })

    all_files.sort(key=lambda x: x['size'], reverse=True)

    # Größen-Breakdown
    files_size = _dir_size(FILES_DIR)
    uploads_size = _dir_size(UPLOADS_DIR)

    db_path = os.path.join(DATA_DIR, 'guenther.db')
    db_size = os.path.getsize(db_path) if os.path.exists(db_path) else 0

    other_size = sum(
        os.path.getsize(os.path.join(DATA_DIR, f))
        for f in _CONFIG_FILES
        if os.path.exists(os.path.join(DATA_DIR, f))
    )

    return jsonify({
        'total_size': files_size + uploads_size + db_size + other_size,
        'breakdown': {
            'files': files_size,
            'uploads': uploads_size,
            'database': db_size,
            'other': other_size,
        },
        'top_files': all_files[:50],
        'file_count': len(all_files),
    })


@storage_bp.route('/api/storage/file', methods=['DELETE'])
def delete_storage_file():
    data = request.get_json() or {}
    relative_path = data.get('path', '').strip()
    if not relative_path:
        return jsonify({'error': 'Kein Pfad angegeben'}), 400

    full_path = _safe_full_path(relative_path)
    if full_path is None:
        return jsonify({'error': 'Ungültiger Pfad'}), 403

    if not os.path.isfile(full_path):
        return jsonify({'error': 'Datei nicht gefunden'}), 404

    os.remove(full_path)
    return jsonify({'success': True})


@storage_bp.route('/api/storage/download', methods=['GET'])
def download_storage_file():
    relative_path = request.args.get('path', '').strip()
    if not relative_path:
        return jsonify({'error': 'Kein Pfad angegeben'}), 400

    full_path = _safe_full_path(relative_path)
    if full_path is None:
        return jsonify({'error': 'Ungültiger Pfad'}), 403

    if not os.path.isfile(full_path):
        return jsonify({'error': 'Datei nicht gefunden'}), 404

    filename = os.path.basename(full_path)
    mime = mimetypes.guess_type(filename)[0] or 'application/octet-stream'

    with open(full_path, 'rb') as f:
        data = f.read()

    return Response(
        data,
        mimetype=mime,
        headers={'Content-Disposition': f'attachment; filename="{filename}"'},
    )
