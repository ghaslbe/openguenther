import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import ChatList from './components/ChatList';
import ChatWindow from './components/ChatWindow';
import GuentherBox from './components/GuentherBox';
import Settings from './components/Settings';
import FirstRunOverlay from './components/FirstRunOverlay';
import { fetchChats, fetchChat, deleteChat, fetchAgents, fetchProviders, fetchUsageStats } from './services/api';
import { getSocket } from './services/socket';

function formatBytes(n) {
  if (n == null || n === 0) return '0 B';
  if (n >= 1024 * 1024) return (n / (1024 * 1024)).toFixed(1) + ' MB';
  if (n >= 1024) return (n / 1024).toFixed(1) + ' KB';
  return n + ' B';
}

function UsagePopup({ onClose }) {
  const [todayStats, setTodayStats] = useState([]);
  const [allStats, setAllStats] = useState([]);

  useEffect(() => {
    fetchUsageStats('today').then(d => setTodayStats(Array.isArray(d) ? d : [])).catch(() => {});
    fetchUsageStats('all').then(d => setAllStats(Array.isArray(d) ? d : [])).catch(() => {});
  }, []);

  function renderRows(stats) {
    if (stats.length === 0) return <p style={{ fontSize: '12px', color: 'var(--text-secondary)', margin: '4px 0' }}>—</p>;
    return stats.map((r, i) => (
      <div key={i} style={{ fontSize: '12px', color: 'var(--text-primary)', marginBottom: '2px' }}>
        <span style={{ fontWeight: 600 }}>{r.provider_id}</span>
        {': '}
        {r.requests} Anfragen · {formatBytes(r.bytes_sent)} gesendet · {formatBytes(r.bytes_received)} empfangen
      </div>
    ));
  }

  return (
    <div
      onClick={onClose}
      style={{ position: 'fixed', inset: 0, zIndex: 1000 }}
    >
      <div
        onClick={e => e.stopPropagation()}
        style={{
          position: 'absolute',
          top: '48px',
          right: '12px',
          background: 'var(--bg-sidebar)',
          border: '1px solid var(--border)',
          borderRadius: '8px',
          padding: '16px',
          minWidth: '320px',
          maxWidth: '420px',
          boxShadow: '0 4px 24px rgba(0,0,0,0.3)',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
          <strong style={{ fontSize: '13px' }}>📊 Nutzung</strong>
          <button onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-secondary)', fontSize: '16px', lineHeight: 1 }}>×</button>
        </div>
        <p style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-secondary)', margin: '0 0 4px' }}>HEUTE</p>
        {renderRows(todayStats)}
        <p style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-secondary)', margin: '10px 0 4px' }}>GESAMT</p>
        {renderRows(allStats)}
      </div>
    </div>
  );
}

export default function App() {
  const [chats, setChats] = useState([]);
  const [activeChatId, setActiveChatId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [guentherLogs, setGuentherLogs] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [currentTool, setCurrentTool] = useState(null);
  const [currentToolLog, setCurrentToolLog] = useState(null);
  const [showSettings, setShowSettings] = useState(false);
  const [guentherWidth, setGuentherWidth] = useState(480);
  const [agents, setAgents] = useState([]);
  const [selectedAgentId, setSelectedAgentId] = useState('');
  const [theme, setTheme] = useState(() => localStorage.getItem('theme') || 'dark');
  const [showFirstRun, setShowFirstRun] = useState(false);
  const [showUsage, setShowUsage] = useState(false);
  const { t, i18n } = useTranslation();

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
  }, [theme]);

  function toggleTheme() {
    const next = theme === 'dark' ? 'light' : 'dark';
    setTheme(next);
    localStorage.setItem('theme', next);
  }

  function toggleLang() {
    const next = i18n.language === 'de' ? 'en' : 'de';
    i18n.changeLanguage(next);
    localStorage.setItem('language', next);
  }

  // Show first-run overlay if language is not saved and no provider is configured
  useEffect(() => {
    if (localStorage.getItem('language')) return;
    fetchProviders().then(providers => {
      const hasProvider = Object.values(providers || {}).some(p => p.enabled);
      if (!hasProvider) setShowFirstRun(true);
    }).catch(() => {});
  }, []);

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
      if (data.type === 'header') {
        if (data.message?.startsWith('TOOL CALL: ')) {
          setCurrentTool(data.message.replace('TOOL CALL: ', ''));
          setCurrentToolLog(null);
        } else if (data.message?.startsWith('TOOL RESULT: ') || data.message === 'GUENTHER AGENT BEENDET') {
          setCurrentTool(null);
          setCurrentToolLog(null);
        }
      } else if (data.type === 'text' && data.message) {
        setCurrentToolLog(data.message);
      }
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
      setCurrentTool(null);
      setCurrentToolLog(null);
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
        <span className="topbar-version">v{__APP_VERSION__}</span><span className="topbar-beta">beta</span>
        <div style={{ marginLeft: 'auto', display: 'flex', gap: '6px', alignItems: 'center' }}>
          <button className="btn-theme-toggle" style={{ marginLeft: 0 }} onClick={() => setShowUsage(v => !v)}>
            📊
          </button>
          <button className="btn-theme-toggle" style={{ marginLeft: 0 }} onClick={toggleLang}>
            {i18n.language === 'de' ? 'EN' : 'DE'}
          </button>
          <button className="btn-theme-toggle" style={{ marginLeft: 0 }} onClick={toggleTheme}>
            {theme === 'dark' ? t('topbar.light') : t('topbar.dark')}
          </button>
        </div>
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
        onNewChat={handleNewChat}
        isLoading={isLoading}
        currentTool={currentTool}
        currentToolLog={currentToolLog}
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
      {showFirstRun && <FirstRunOverlay onClose={() => setShowFirstRun(false)} />}
      {showUsage && <UsagePopup onClose={() => setShowUsage(false)} />}
      </div>
    </div>
  );
}
