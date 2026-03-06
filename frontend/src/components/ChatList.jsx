import React, { useState, useRef, useEffect } from 'react';
import { useTranslation } from 'react-i18next';

export default function ChatList({ chats, activeChatId, onSelectChat, onNewChat, onDeleteChat, onOpenSettings, agents }) {
  const { t } = useTranslation();
  const [showMenu, setShowMenu] = useState(false);
  const menuRef = useRef(null);

  function getAgentName(agentId) {
    if (!agentId || !agents) return null;
    const agent = agents.find(a => a.id === agentId);
    return agent ? agent.name : null;
  }

  // Menü schließen bei Klick außerhalb
  useEffect(() => {
    function handleClickOutside(e) {
      if (menuRef.current && !menuRef.current.contains(e.target)) {
        setShowMenu(false);
      }
    }
    if (showMenu) document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [showMenu]);

  function handleSelect(agentId) {
    setShowMenu(false);
    onNewChat(agentId || '');
  }

  return (
    <div className="chat-list">
      <div className="chat-list-header">
        <h2>Chats</h2>
        <div ref={menuRef} style={{ position: 'relative' }}>
          <button
            className="btn-new-chat"
            onClick={() => setShowMenu(s => !s)}
            title={t('chatList.newChatTitle')}
          >+</button>
          {showMenu && (
            <div className="new-chat-menu">
              <div className="new-chat-menu-item" onClick={() => handleSelect('')}>
                <span className="new-chat-menu-icon">💬</span>
                <span>Ohne Agent</span>
              </div>
              {agents && agents.length > 0 && (
                <>
                  <div className="new-chat-menu-divider" />
                  {agents.map(a => (
                    <div key={a.id} className="new-chat-menu-item" onClick={() => handleSelect(a.id)}>
                      <span className="new-chat-menu-icon">🤖</span>
                      <span>{a.name}</span>
                      {a.description && <span className="new-chat-menu-desc">{a.description}</span>}
                    </div>
                  ))}
                </>
              )}
            </div>
          )}
        </div>
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
