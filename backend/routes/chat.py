from flask import Blueprint, request, jsonify, Response
from models import create_chat, get_chats, get_chat, delete_chat, add_message, update_chat_title
from services import file_store

chat_bp = Blueprint('chat', __name__)


@chat_bp.route('/api/chats', methods=['GET'])
def list_chats():
    return jsonify(get_chats())


@chat_bp.route('/api/chats', methods=['POST'])
def new_chat():
    data = request.get_json() or {}
    title = data.get('title', 'Neuer Chat')
    chat_id = create_chat(title)
    return jsonify({'id': chat_id, 'title': title})


@chat_bp.route('/api/chats/<int:chat_id>', methods=['GET'])
def get_chat_detail(chat_id):
    chat = get_chat(chat_id)
    if chat:
        return jsonify(chat)
    return jsonify({'error': 'Chat nicht gefunden'}), 404


@chat_bp.route('/api/chats/<int:chat_id>', methods=['DELETE'])
def remove_chat(chat_id):
    delete_chat(chat_id)
    file_store.delete_chat_files(chat_id)
    return jsonify({'success': True})


@chat_bp.route('/api/chats/<int:chat_id>/files/<path:filename>', methods=['GET'])
def get_chat_file(chat_id, filename):
    data = file_store.get_file(chat_id, filename)
    if data is None:
        return jsonify({'error': 'Datei nicht gefunden'}), 404
    mime = 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
    return Response(
        data,
        mimetype=mime,
        headers={'Content-Disposition': f'attachment; filename="{filename}"'}
    )


@chat_bp.route('/api/chats/<int:chat_id>/info', methods=['GET'])
def get_chat_info(chat_id):
    chat = get_chat(chat_id)
    if not chat:
        return jsonify({'error': 'Chat nicht gefunden'}), 404
    msgs = chat.get('messages', [])
    user_msgs = [m for m in msgs if m['role'] == 'user']
    asst_msgs = [m for m in msgs if m['role'] == 'assistant']
    files = file_store.list_chat_files(chat_id)
    return jsonify({
        'id': chat['id'],
        'title': chat['title'],
        'created_at': chat['created_at'],
        'updated_at': chat['updated_at'],
        'agent_id': chat.get('agent_id'),
        'message_count': len(msgs),
        'user_messages': len(user_msgs),
        'assistant_messages': len(asst_msgs),
        'files': files,
    })


@chat_bp.route('/api/chats/<int:chat_id>/title', methods=['PUT'])
def rename_chat(chat_id):
    data = request.get_json() or {}
    title = data.get('title', '')
    if title:
        update_chat_title(chat_id, title)
    return jsonify({'success': True})
