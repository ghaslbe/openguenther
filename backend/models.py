import sqlite3
import os
from datetime import datetime
from config import DB_FILE, DATA_DIR


def get_db():
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS chats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    ''')
    # Migration: add agent_id column if missing
    try:
        conn.execute("ALTER TABLE chats ADD COLUMN agent_id TEXT")
        conn.commit()
    except Exception:
        pass  # column already exists

    conn.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            message_type TEXT DEFAULT 'text',
            created_at TEXT NOT NULL,
            FOREIGN KEY (chat_id) REFERENCES chats(id) ON DELETE CASCADE
        )
    ''')

    conn.execute('''
        CREATE TABLE IF NOT EXISTS usage_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            provider_id TEXT NOT NULL,
            model TEXT NOT NULL,
            bytes_sent INTEGER DEFAULT 0,
            bytes_received INTEGER DEFAULT 0,
            prompt_tokens INTEGER,
            completion_tokens INTEGER
        )
    ''')
    conn.commit()
    conn.close()


def create_chat(title="Neuer Chat", agent_id=None):
    conn = get_db()
    now = datetime.utcnow().isoformat()
    cursor = conn.execute(
        'INSERT INTO chats (title, created_at, updated_at, agent_id) VALUES (?, ?, ?, ?)',
        (title, now, now, agent_id)
    )
    chat_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return chat_id


def get_chats():
    conn = get_db()
    chats = conn.execute('SELECT * FROM chats ORDER BY updated_at DESC').fetchall()
    conn.close()
    return [dict(c) for c in chats]


def get_chat(chat_id):
    conn = get_db()
    chat = conn.execute('SELECT * FROM chats WHERE id = ?', (chat_id,)).fetchone()
    if chat:
        messages = conn.execute(
            'SELECT * FROM messages WHERE chat_id = ? ORDER BY created_at',
            (chat_id,)
        ).fetchall()
        conn.close()
        result = dict(chat)
        result['messages'] = [dict(m) for m in messages]
        return result
    conn.close()
    return None


def delete_chat(chat_id):
    conn = get_db()
    conn.execute('DELETE FROM messages WHERE chat_id = ?', (chat_id,))
    conn.execute('DELETE FROM chats WHERE id = ?', (chat_id,))
    conn.commit()
    conn.close()


def add_message(chat_id, role, content, message_type='text'):
    conn = get_db()
    now = datetime.utcnow().isoformat()
    conn.execute(
        'INSERT INTO messages (chat_id, role, content, message_type, created_at) VALUES (?, ?, ?, ?, ?)',
        (chat_id, role, content, message_type, now)
    )
    conn.execute('UPDATE chats SET updated_at = ? WHERE id = ?', (now, chat_id))
    conn.commit()
    conn.close()


def update_chat_title(chat_id, title):
    conn = get_db()
    conn.execute('UPDATE chats SET title = ? WHERE id = ?', (title, chat_id))
    conn.commit()
    conn.close()


def log_usage(provider_id, model, bytes_sent, bytes_received, prompt_tokens=None, completion_tokens=None):
    conn = get_db()
    now = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')
    conn.execute(
        'INSERT INTO usage_log (timestamp, provider_id, model, bytes_sent, bytes_received, prompt_tokens, completion_tokens) VALUES (?, ?, ?, ?, ?, ?, ?)',
        (now, provider_id, model, bytes_sent, bytes_received, prompt_tokens, completion_tokens)
    )
    conn.commit()
    conn.close()


def get_usage_stats(period='today'):
    where = ''
    if period == 'today':
        where = "WHERE timestamp >= strftime('%Y-%m-%dT00:00:00', 'now')"
    elif period == 'week':
        where = "WHERE timestamp >= datetime('now', '-7 days')"
    elif period == 'month':
        where = "WHERE timestamp >= datetime('now', '-30 days')"

    conn = get_db()
    rows = conn.execute(f'''
        SELECT provider_id, model,
               COUNT(*) as requests,
               SUM(bytes_sent) as bytes_sent,
               SUM(bytes_received) as bytes_received,
               SUM(prompt_tokens) as prompt_tokens,
               SUM(completion_tokens) as completion_tokens
        FROM usage_log
        {where}
        GROUP BY provider_id, model
        ORDER BY bytes_sent DESC
    ''').fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_usage_timeline(granularity='day'):
    if granularity == 'hour':
        fmt = '%Y-%m-%dT%H:00:00'
        where = "timestamp >= datetime('now', '-24 hours')"
    elif granularity == 'month':
        fmt = '%Y-%m'
        where = "timestamp >= datetime('now', '-12 months')"
    else:  # day
        fmt = '%Y-%m-%d'
        where = "timestamp >= datetime('now', '-30 days')"

    conn = get_db()
    rows = conn.execute(f'''
        SELECT strftime('{fmt}', timestamp) as period,
               SUM(bytes_sent) as bytes_sent,
               SUM(bytes_received) as bytes_received,
               COUNT(*) as requests
        FROM usage_log
        WHERE {where}
        GROUP BY period
        ORDER BY period
    ''').fetchall()
    conn.close()
    return [dict(r) for r in rows]


def reset_usage_stats():
    conn = get_db()
    conn.execute('DELETE FROM usage_log')
    conn.commit()
    conn.close()
