import os
import io
import re
import zipfile
import tempfile
import shutil
from flask import Blueprint, jsonify, Response, request
from config import DATA_DIR

custom_tools_bp = Blueprint('custom_tools', __name__)
CUSTOM_TOOLS_DIR = os.path.join(DATA_DIR, 'custom_tools')

_TOOL_NAME_RE = re.compile(r'^[a-zA-Z0-9_-]+$')


def _is_safe_member(name):
    """Reject path traversal attempts and absolute paths."""
    if os.path.isabs(name):
        return False
    norm = os.path.normpath(name)
    return not (norm.startswith('..') or norm == '..')


@custom_tools_bp.route('/api/custom-tools', methods=['GET'])
def list_custom_tools():
    if not os.path.isdir(CUSTOM_TOOLS_DIR):
        return jsonify([])
    names = [
        d for d in os.listdir(CUSTOM_TOOLS_DIR)
        if os.path.isdir(os.path.join(CUSTOM_TOOLS_DIR, d))
        and os.path.isfile(os.path.join(CUSTOM_TOOLS_DIR, d, 'tool.py'))
    ]
    return jsonify(sorted(names))


@custom_tools_bp.route('/api/custom-tools/<name>/download', methods=['GET'])
def download_custom_tool(name):
    if not _TOOL_NAME_RE.match(name):
        return jsonify({'error': 'Invalid tool name'}), 400

    tool_dir = os.path.join(CUSTOM_TOOLS_DIR, name)
    if not os.path.isdir(tool_dir):
        return jsonify({'error': 'Tool not found'}), 404

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        for fname in os.listdir(tool_dir):
            fpath = os.path.join(tool_dir, fname)
            if os.path.isfile(fpath):
                zf.write(fpath, arcname=f'{name}/{fname}')
    buf.seek(0)

    return Response(
        buf.read(),
        mimetype='application/zip',
        headers={'Content-Disposition': f'attachment; filename={name}.zip'}
    )


@custom_tools_bp.route('/api/custom-tools/upload', methods=['POST'])
def upload_custom_tool():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    uploaded = request.files['file']
    if not uploaded.filename.endswith('.zip'):
        return jsonify({'error': 'Only .zip files are accepted'}), 400

    try:
        zf = zipfile.ZipFile(uploaded.stream)
    except zipfile.BadZipFile:
        return jsonify({'error': 'Invalid ZIP file'}), 400

    # Security: validate all member paths
    for member in zf.namelist():
        if not _is_safe_member(member):
            return jsonify({'error': f'Unsafe path in ZIP: {member}'}), 400

    # Determine tool name from top-level folder or filename
    top_dirs = set()
    for member in zf.namelist():
        parts = member.replace('\\', '/').split('/')
        if len(parts) >= 2 and parts[0]:
            top_dirs.add(parts[0])

    if len(top_dirs) == 1:
        tool_name = next(iter(top_dirs))
    else:
        # Fall back to sanitised filename
        tool_name = re.sub(r'[^a-zA-Z0-9_-]', '_', uploaded.filename[:-4])

    if not _TOOL_NAME_RE.match(tool_name):
        return jsonify({'error': f'Invalid tool name: {tool_name}'}), 400

    with tempfile.TemporaryDirectory() as tmp:
        zf.extractall(tmp)

        # Locate tool.py — accept <name>/tool.py or tool.py at root
        candidate_paths = [
            os.path.join(tmp, tool_name, 'tool.py'),
            os.path.join(tmp, 'tool.py'),
        ]
        tool_py = next((p for p in candidate_paths if os.path.isfile(p)), None)
        if tool_py is None:
            return jsonify({'error': 'tool.py not found in ZIP'}), 400

        # Determine source directory (folder containing tool.py)
        src_dir = os.path.dirname(tool_py)

        dest_dir = os.path.join(CUSTOM_TOOLS_DIR, tool_name)
        if os.path.exists(dest_dir):
            shutil.rmtree(dest_dir)
        shutil.copytree(src_dir, dest_dir)

    return jsonify({'success': True, 'tool_name': tool_name})
