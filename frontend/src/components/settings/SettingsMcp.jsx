import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { fetchMcpServers, addMcpServer, deleteMcpServer } from '../../services/api';

export default function SettingsMcp() {
  const { t } = useTranslation();
  const [mcpServers, setMcpServers] = useState([]);
  const [newName, setNewName] = useState('');
  const [newCommand, setNewCommand] = useState('');
  const [newArgs, setNewArgs] = useState('');
  const [message, setMessage] = useState('');

  useEffect(() => {
    loadMcpServers();
  }, []);

  async function loadMcpServers() {
    const servers = await fetchMcpServers();
    setMcpServers(servers);
  }

  async function handleAddServer() {
    if (!newName || !newCommand) return;
    const args = newArgs ? newArgs.split(' ').filter(Boolean) : [];
    await addMcpServer({ name: newName, transport: 'stdio', command: newCommand, args });
    setNewName('');
    setNewCommand('');
    setNewArgs('');
    await loadMcpServers();
    setMessage(t('settings.mcp.added'));
    setTimeout(() => setMessage(''), 3000);
  }

  async function handleDeleteServer(id) {
    await deleteMcpServer(id);
    await loadMcpServers();
  }

  return (
    <div>
      {message && <div className="settings-message">{message}</div>}
      <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginBottom: '16px' }}>
        {t('settings.mcp.description')}
      </p>

      <div className="settings-section">
        <h3>{t('settings.mcp.configured')}</h3>
        <div className="mcp-servers-list">
          {mcpServers.map(s => (
            <div key={s.id} className="mcp-server-item">
              <div className="mcp-server-info">
                <strong>{s.name}</strong>
                <span className="mcp-server-cmd">{s.command} {(s.args || []).join(' ')}</span>
              </div>
              <button className="btn-delete-server" onClick={() => handleDeleteServer(s.id)}>
                {t('settings.mcp.remove')}
              </button>
            </div>
          ))}
          {mcpServers.length === 0 && (
            <div className="mcp-servers-empty">{t('settings.mcp.empty')}</div>
          )}
        </div>
      </div>

      <div className="settings-section">
        <h3>{t('settings.mcp.addTitle')}</h3>
        <div className="mcp-add-form">
          <input
            type="text"
            placeholder="Name (z.B. Weather MCP)"
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
          />
          <input
            type="text"
            placeholder="Command (z.B. npx)"
            value={newCommand}
            onChange={(e) => setNewCommand(e.target.value)}
          />
          <input
            type="text"
            placeholder="Argumente (z.B. -y @weather/mcp)"
            value={newArgs}
            onChange={(e) => setNewArgs(e.target.value)}
          />
          <button className="btn-add-server" onClick={handleAddServer}>
            {t('settings.mcp.add')}
          </button>
        </div>
      </div>
    </div>
  );
}
