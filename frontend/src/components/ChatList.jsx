import React from 'react';
import { useTranslation } from 'react-i18next';

export default function ChatList({ chats, activeChatId, onSelectChat, onNewChat, onDeleteChat, onOpenSettings, agents }) {
  const { t } = useTranslation();

  function getAgentName(agentId) {
    if (!agentId || !agents) return null;
    const agent = agents.find(a => a.id === agentId);
    return agent ? agent.name : null;
  }

  return (
    <div className="chat-list">
      <div className="chat-list-header">
        <h2>Chats</h2>
        <button className="btn-new-chat" onClick={onNewChat} title={t('chatList.newChatTitle')}>+</button>
      </div>
      <div className="chat-list-items">
        {chats.map(chat => (
          <div
            key={chat.id}
            className={`chat-list-item ${chat.id === activeChatId ? 'active' : ''}`}
            onClick={() => onSelectChat(chat.id)}
          >
            <div className="chat-item-body">
              <span className="chat-title">{chat.title}</span>
              {getAgentName(chat.agent_id) && (
                <span className="chat-agent-badge">{getAgentName(chat.agent_id)}</span>
              )}
            </div>
            <button
              className="btn-delete-chat"
              onClick={(e) => { e.stopPropagation(); onDeleteChat(chat.id); }}
              title={t('chatList.deleteChatTitle')}
            >
              x
            </button>
          </div>
        ))}
        {chats.length === 0 && (
          <div className="chat-list-empty">{t('chatList.empty')}</div>
        )}
      </div>
      <div className="chat-list-footer">
        <button className="btn-settings" onClick={onOpenSettings}>
          {t('chatList.settings')}
        </button>
      </div>
    </div>
  );
}
