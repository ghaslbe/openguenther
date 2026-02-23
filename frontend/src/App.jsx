import React, { useState, useEffect, useCallback, useRef } from 'react';
import ChatList from './components/ChatList';
import ChatWindow from './components/ChatWindow';
import GuentherBox from './components/GuentherBox';
import Settings from './components/Settings';
import { fetchChats, fetchChat, deleteChat, fetchAgents } from './services/api';
import { getSocket } from './services/socket';

export default function App() {
  const [chats, setChats] = useState([]);
  const [activeChatId, setActiveChatId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [guentherLogs, setGuentherLogs] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [guentherWidth, setGuentherWidth] = useState(480);
  const [agents, setAgents] = useState([]);
  const [selectedAgentId, setSelectedAgentId] = useState('');
  const [theme, setTheme] = useState(() => localStorage.getItem('theme') || 'dark');

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
  }, [theme]);

  function toggleTheme() {
    const next = theme === 'dark' ? 'light' : 'dark';
    setTheme(next);
    localStorage.setItem('theme', next);
  }

  const isResizing = useRef(false);
  const socket = getSocket();

  // Load chats and agents on mount
  useEffect(() => {
    loadChats();
    loadAgents();
  }, []);

  async function loadAgents() {
    const data = await fetchAgents();
    setAgents(data);
  }

  // Socket event listeners
  useEffect(() => {
    socket.on('guenther_log', (data) => {
      setGuentherLogs(prev => [...prev, data]);
    });

    socket.on('chat_created', (data) => {
      setActiveChatId(data.chat_id);
      setSelectedAgentId('');
      loadChats();
    });

    socket.on('chat_updated', (data) => {
      setChats(prev => prev.map(c =>
        c.id === data.chat_id ? { ...c, title: data.title } : c
      ));
    });

    socket.on('agent_start', () => {
      setIsLoading(true);
    });

    socket.on('agent_response', (data) => {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: data.content
      }]);
    });

    socket.on('agent_end', () => {
      setIsLoading(false);
      loadChats();
    });

    return () => {
      socket.off('guenther_log');
      socket.off('chat_created');
      socket.off('chat_updated');
      socket.off('agent_start');
      socket.off('agent_response');
      socket.off('agent_end');
    };
  }, [socket]);

  // Resize handlers
  const handleResizeStart = useCallback((e) => {
    e.preventDefault();
    isResizing.current = true;
    document.body.style.cursor = 'col-resize';
    document.body.style.userSelect = 'none';

    const handleMouseMove = (e) => {
      if (!isResizing.current) return;
      const newWidth = window.innerWidth - e.clientX;
      setGuentherWidth(Math.max(300, Math.min(newWidth, window.innerWidth - 500)));
    };

    const handleMouseUp = () => {
      isResizing.current = false;
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
  }, []);

  async function loadChats() {
    const data = await fetchChats();
    setChats(data);
  }

  async function handleSelectChat(chatId) {
    setActiveChatId(chatId);
    const chat = await fetchChat(chatId);
    if (chat && chat.messages) {
      setMessages(chat.messages.map(m => ({
        role: m.role,
        content: m.content
      })));
    }
  }

  function handleNewChat() {
    setActiveChatId(null);
    setMessages([]);
  }

  function handleClearLogs() {
    setGuentherLogs([]);
  }

  async function handleDeleteChat(chatId) {
    await deleteChat(chatId);
    if (activeChatId === chatId) {
      setActiveChatId(null);
      setMessages([]);
    }
    loadChats();
  }

  // Determine which agent name to show in ChatWindow
  function getActiveAgentName() {
    if (!activeChatId) {
      // New chat: use the selected agent
      if (!selectedAgentId) return null;
      const a = agents.find(a => a.id === selectedAgentId);
      return a ? a.name : null;
    } else {
      // Existing chat: look up agent_id from chats list
      const chat = chats.find(c => c.id === activeChatId);
      if (!chat || !chat.agent_id) return null;
      const a = agents.find(a => a.id === chat.agent_id);
      return a ? a.name : null;
    }
  }

  function handleSendMessage(content, file = null) {
    const displayContent = file
      ? `📎 ${file.name}${content ? `\n${content}` : ''}`
      : content;
    setMessages(prev => [...prev, { role: 'user', content: displayContent }]);
    socket.emit('send_message', {
      chat_id: activeChatId,
      content,
      agent_id: activeChatId ? '' : selectedAgentId,
      file_name: file ? file.name : '',
      file_content: file ? file.content : ''
    });
  }

  return (
    <div className="app-wrapper">
      <div className="app-topbar">
        <span className="topbar-open">OPEN</span><span className="topbar-guenther">guenther</span>
        <span className="topbar-version">v{__APP_VERSION__}</span>
        <button className="btn-theme-toggle" onClick={toggleTheme}>
          {theme === 'dark' ? 'LIGHT' : 'DARK'}
        </button>
      </div>
      <div className="app">
        <ChatList
        chats={chats}
        activeChatId={activeChatId}
        onSelectChat={handleSelectChat}
        onNewChat={handleNewChat}
        onDeleteChat={handleDeleteChat}
        onOpenSettings={() => setShowSettings(true)}
        agents={agents}
      />
      <ChatWindow
        messages={messages}
        onSendMessage={handleSendMessage}
        isLoading={isLoading}
        activeChatId={activeChatId}
        agents={agents}
        selectedAgentId={selectedAgentId}
        onAgentChange={setSelectedAgentId}
        activeAgentName={getActiveAgentName()}
      />
      <GuentherBox
        logs={guentherLogs}
        width={guentherWidth}
        onResizeStart={handleResizeStart}
        onClear={handleClearLogs}
      />
      {showSettings && <Settings onClose={() => setShowSettings(false)} onAgentsChange={loadAgents} />}
      </div>
    </div>
  );
}
