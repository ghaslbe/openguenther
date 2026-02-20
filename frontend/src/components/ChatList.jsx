import React from 'react';

export default function ChatList({ chats, activeChatId, onSelectChat, onNewChat, onDeleteChat, onOpenSettings }) {
  return (
    <div className="chat-list">
      <div className="chat-list-header">
        <h2>Chats</h2>
        <button className="btn-new-chat" onClick={onNewChat} title="Neuer Chat">+</button>
      </div>
      <div className="chat-list-items">
        {chats.map(chat => (
          <div
            key={chat.id}
            className={`chat-list-item ${chat.id === activeChatId ? 'active' : ''}`}
            onClick={() => onSelectChat(chat.id)}
          >
            <span className="chat-title">{chat.title}</span>
            <button
              className="btn-delete-chat"
              onClick={(e) => { e.stopPropagation(); onDeleteChat(chat.id); }}
              title="Chat loeschen"
            >
              x
            </button>
          </div>
        ))}
        {chats.length === 0 && (
          <div className="chat-list-empty">Keine Chats vorhanden</div>
        )}
      </div>
      <div className="chat-list-footer">
        <button className="btn-settings" onClick={onOpenSettings}>
          Einstellungen
        </button>
      </div>
    </div>
  );
}
