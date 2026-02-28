import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { fetchMcpServers, addMcpServer, deleteMcpServer } from '../../services/api';

export default function SettingsMcp() {
  const { t } = useTranslation();
  const [mcpServers, setMcpServers] = useState([]);
  const [newName, setNewName] = useState('');
  const [newCommand, setNewCommand] = useState('');
  const [newArgs, setNewArgs] = useState('');
  const [newEnv, setNewEnv] = useState('');
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
    const env = {};
    newEnv.split('\n').forEach(line => {
      const idx = line.indexOf('=');
      if (idx > 0) env[line.slice(0, idx).trim()] = line.slice(idx + 1).trim();
    });
    await addMcpServer({ name: newName, transport: 'stdio', command: newCommand, args, env });
    setNewName('');
    setNewCommand('');
    setNewArgs('');
    setNewEnv('');
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
                {s.env && Object.keys(s.env).length > 0 && (
                  <span style={{ fontSize: '11px', color: 'var(--text-secondary)', marginTop: '2px', display: 'block' }}>
                    ENV: {Object.keys(s.env).join(', ')}
                  </span>
                )}
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
          <textarea
            placeholder={t('settings.mcp.envPlaceholder')}
            value={newEnv}
            onChange={(e) => setNewEnv(e.target.value)}
            rows={3}
            style={{ fontFamily: 'monospace', fontSize: '12px', resize: 'vertical' }}
          />
          <button className="btn-add-server" onClick={handleAddServer}>
            {t('settings.mcp.add')}
          </button>
        </div>
      </div>

      <div style={{
        marginTop: '24px',
        padding: '12px 16px',
        background: 'var(--bg-input)',
        border: '1px solid var(--border)',
        borderRadius: '8px',
        fontSize: '13px',
        color: 'var(--text-secondary)',
        lineHeight: '1.5',
      }}>
        💡 {t('settings.mcp.marketplaceHint')}{' '}
        <a href="https://mcpmarket.com/" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--accent)' }}>
          mcpmarket.com
        </a>
        {t('settings.mcp.marketplaceHintSuffix')}
      </div>
    </div>
  );
}
