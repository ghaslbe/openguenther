import React, { useState, useEffect } from 'react';
import {
  fetchSettings, updateSettings,
  fetchMcpServers, addMcpServer, deleteMcpServer,
  reloadMcpTools, fetchMcpTools
} from '../services/api';
import ToolSettings from './ToolSettings';

export default function Settings({ onClose }) {
  const [apiKey, setApiKey] = useState('');
  const [apiKeyMasked, setApiKeyMasked] = useState('');
  const [model, setModel] = useState('openai/gpt-4o-mini');
  const [showKey, setShowKey] = useState(false);
  const [mcpServers, setMcpServers] = useState([]);
  const [mcpTools, setMcpTools] = useState([]);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');
  const [toolSettingsOpen, setToolSettingsOpen] = useState(null);

  // New MCP server form
  const [newName, setNewName] = useState('');
  const [newCommand, setNewCommand] = useState('');
  const [newArgs, setNewArgs] = useState('');

  useEffect(() => {
    loadSettings();
    loadMcpServers();
    loadMcpTools();
  }, []);

  async function loadSettings() {
    const s = await fetchSettings();
    setApiKey(s.openrouter_api_key || '');
    setApiKeyMasked(s.openrouter_api_key_masked || '');
    setModel(s.model || 'openai/gpt-4o-mini');
  }

  async function loadMcpServers() {
    const servers = await fetchMcpServers();
    setMcpServers(servers);
  }

  async function loadMcpTools() {
    const tools = await fetchMcpTools();
    setMcpTools(tools);
  }

  async function handleSave() {
    setSaving(true);
    const data = { model };
    if (apiKey && apiKey !== '') {
      data.openrouter_api_key = apiKey;
    }
    await updateSettings(data);
    setMessage('Einstellungen gespeichert!');
    setSaving(false);
    setTimeout(() => setMessage(''), 3000);
  }

  async function handleAddServer() {
    if (!newName || !newCommand) return;
    const args = newArgs ? newArgs.split(' ').filter(Boolean) : [];
    await addMcpServer({
      name: newName,
      transport: 'stdio',
      command: newCommand,
      args
    });
    setNewName('');
    setNewCommand('');
    setNewArgs('');
    await loadMcpServers();
  }

  async function handleDeleteServer(id) {
    await deleteMcpServer(id);
    await loadMcpServers();
  }

  async function handleReload() {
    setMessage('MCP Tools werden neu geladen...');
    await reloadMcpTools();
    await loadMcpTools();
    setMessage('MCP Tools neu geladen!');
    setTimeout(() => setMessage(''), 3000);
  }

  // If a tool settings modal is open, show it instead
  if (toolSettingsOpen) {
    return (
      <ToolSettings
        toolName={toolSettingsOpen}
        onClose={() => setToolSettingsOpen(null)}
      />
    );
  }

  return (
    <div className="settings-overlay" onClick={onClose}>
      <div className="settings-modal" onClick={(e) => e.stopPropagation()}>
        <div className="settings-header">
          <h2>Einstellungen</h2>
          <button className="btn-close" onClick={onClose}>x</button>
        </div>

        <div className="settings-body">
          {message && <div className="settings-message">{message}</div>}

          <div className="settings-section">
            <h3>OpenRouter</h3>
            <label>
              API Key
              <div className="input-group">
                <input
                  type={showKey ? 'text' : 'password'}
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  placeholder={apiKeyMasked || 'sk-or-v1-...'}
                />
                <button
                  type="button"
                  className="btn-toggle-key"
                  onClick={() => setShowKey(!showKey)}
                >
                  {showKey ? 'Verbergen' : 'Anzeigen'}
                </button>
              </div>
            </label>
            <label>
              Modell
              <input
                type="text"
                value={model}
                onChange={(e) => setModel(e.target.value)}
                placeholder="openai/gpt-4o-mini"
              />
              <small>z.B. openai/gpt-4o, anthropic/claude-3.5-sonnet, google/gemini-pro — <a href="https://openrouter.ai/models" target="_blank" rel="noopener noreferrer" style={{color: 'var(--accent)'}}>Alle Modelle ansehen</a></small>
            </label>
            <button className="btn-save" onClick={handleSave} disabled={saving}>
              {saving ? 'Speichere...' : 'Speichern'}
            </button>
          </div>

          <div className="settings-section">
            <h3>Aktive Tools ({mcpTools.length})</h3>
            <div className="mcp-tools-list">
              {mcpTools.map((t, i) => (
                <div key={i} className="mcp-tool-item">
                  <span className="mcp-tool-name">{t.name}</span>
                  <span className="mcp-tool-badge">{t.builtin ? 'Built-in' : 'Extern'}</span>
                  {t.has_settings && (
                    <button
                      className="btn-tool-settings"
                      onClick={() => setToolSettingsOpen(t.name)}
                      title="Tool-Einstellungen"
                    >
                      Einstellungen
                    </button>
                  )}
                  <span className="mcp-tool-desc">{t.description}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="settings-section">
            <h3>Externe MCP Server</h3>
            <div className="mcp-servers-list">
              {mcpServers.map(s => (
                <div key={s.id} className="mcp-server-item">
                  <div className="mcp-server-info">
                    <strong>{s.name}</strong>
                    <span className="mcp-server-cmd">{s.command} {(s.args || []).join(' ')}</span>
                  </div>
                  <button
                    className="btn-delete-server"
                    onClick={() => handleDeleteServer(s.id)}
                  >
                    Entfernen
                  </button>
                </div>
              ))}
              {mcpServers.length === 0 && (
                <div className="mcp-servers-empty">Keine externen MCP Server konfiguriert</div>
              )}
            </div>

            <div className="mcp-add-form">
              <h4>Neuen MCP Server hinzufuegen</h4>
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
                Hinzufuegen
              </button>
            </div>

            <button className="btn-reload-mcp" onClick={handleReload}>
              MCP Tools neu laden
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
