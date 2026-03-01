import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { fetchMcpServers, addMcpServer, updateMcpServer, deleteMcpServer, reloadMcpTools } from '../../services/api';

function envToText(env) {
  if (!env) return '';
  return Object.entries(env).map(([k, v]) => `${k}=${v}`).join('\n');
}

function textToEnv(text) {
  const env = {};
  text.split('\n').forEach(line => {
    const idx = line.indexOf('=');
    if (idx > 0) env[line.slice(0, idx).trim()] = line.slice(idx + 1).trim();
  });
  return env;
}

export default function SettingsMcp() {
  const { t } = useTranslation();
  const [mcpServers, setMcpServers] = useState([]);
  const [newName, setNewName] = useState('');
  const [newCommand, setNewCommand] = useState('');
  const [newArgs, setNewArgs] = useState('');
  const [newEnv, setNewEnv] = useState('');
  const [editId, setEditId] = useState(null);
  const [editState, setEditState] = useState({});
  const [message, setMessage] = useState('');
  const [reloading, setReloading] = useState(false);

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
    const env = textToEnv(newEnv);
    await addMcpServer({ name: newName, transport: 'stdio', command: newCommand, args, env });
    setNewName('');
    setNewCommand('');
    setNewArgs('');
    setNewEnv('');
    await loadMcpServers();
    setMessage(t('settings.mcp.added'));
    setTimeout(() => setMessage(''), 3000);
  }

  function startEdit(s) {
    setEditId(s.id);
    setEditState({
      name: s.name,
      command: s.command,
      args: (s.args || []).join(' '),
      env: envToText(s.env),
    });
  }

  function cancelEdit() {
    setEditId(null);
    setEditState({});
  }

  async function handleSaveEdit(id) {
    const args = editState.args ? editState.args.split(' ').filter(Boolean) : [];
    const env = textToEnv(editState.env || '');
    await updateMcpServer(id, { name: editState.name, command: editState.command, args, env });
    setEditId(null);
    await loadMcpServers();
    setMessage(t('settings.mcp.saved'));
    setTimeout(() => setMessage(''), 3000);
  }

  async function handleDeleteServer(id) {
    await deleteMcpServer(id);
    await loadMcpServers();
  }

  async function handleReload() {
    setReloading(true);
    await reloadMcpTools();
    setReloading(false);
    setMessage(t('settings.mcp.reloaded'));
    setTimeout(() => setMessage(''), 3000);
  }

  return (
    <div>
      {message && <div className="settings-message">{message}</div>}
      <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginBottom: '16px' }}>
        {t('settings.mcp.description')}
      </p>

      <div className="settings-section">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
          <h3 style={{ margin: 0 }}>{t('settings.mcp.configured')}</h3>
          <button className="btn-test-provider" onClick={handleReload} disabled={reloading}>
            {reloading ? t('settings.mcp.reloading') : t('settings.mcp.reload')}
          </button>
        </div>
        <div className="mcp-servers-list">
          {mcpServers.map(s => (
            <div key={s.id} className="mcp-server-item" style={{ flexDirection: 'column', alignItems: 'stretch' }}>
              {editId === s.id ? (
                <div className="mcp-add-form" style={{ border: 'none', padding: '8px 0' }}>
                  <input
                    type="text"
                    value={editState.name}
                    onChange={e => setEditState(p => ({ ...p, name: e.target.value }))}
                    placeholder="Name"
                  />
                  <input
                    type="text"
                    value={editState.command}
                    onChange={e => setEditState(p => ({ ...p, command: e.target.value }))}
                    placeholder="Command"
                  />
                  <input
                    type="text"
                    value={editState.args}
                    onChange={e => setEditState(p => ({ ...p, args: e.target.value }))}
                    placeholder="Argumente"
                  />
                  <textarea
                    value={editState.env}
                    onChange={e => setEditState(p => ({ ...p, env: e.target.value }))}
                    placeholder={t('settings.mcp.envPlaceholder')}
                    rows={3}
                    style={{ fontFamily: 'monospace', fontSize: '12px', resize: 'vertical' }}
                  />
                  <div style={{ display: 'flex', gap: '8px' }}>
                    <button className="btn-save" onClick={() => handleSaveEdit(s.id)}>
                      {t('settings.mcp.save')}
                    </button>
                    <button className="btn-test-provider" onClick={cancelEdit}>
                      {t('settings.mcp.cancel')}
                    </button>
                  </div>
                </div>
              ) : (
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', width: '100%' }}>
                  <div className="mcp-server-info" style={{ flex: 1 }}>
                    <strong>{s.name}</strong>
                    <span className="mcp-server-cmd">{s.command} {(s.args || []).join(' ')}</span>
                    {s.env && Object.keys(s.env).length > 0 && (
                      <span style={{ fontSize: '11px', color: 'var(--text-secondary)', marginTop: '2px', display: 'block' }}>
                        ENV: {Object.keys(s.env).join(', ')}
                      </span>
                    )}
                  </div>
                  <button className="btn-test-provider" onClick={() => startEdit(s)}>
                    {t('settings.mcp.edit')}
                  </button>
                  <button className="btn-delete-server" onClick={() => handleDeleteServer(s.id)}>
                    {t('settings.mcp.remove')}
                  </button>
                </div>
              )}
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

      <p style={{ marginTop: '12px', fontSize: '12px', color: 'var(--text-secondary)', opacity: 0.7 }}>
        ℹ️ {t('settings.mcp.toolsHint')}
      </p>
    </div>
  );
}
