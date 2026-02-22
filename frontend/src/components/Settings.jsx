import React, { useState, useEffect } from 'react';
import {
  fetchSettings, updateSettings,
  fetchMcpServers, addMcpServer, deleteMcpServer,
  reloadMcpTools, fetchMcpTools,
  fetchTelegramSettings, updateTelegramSettings,
  fetchTelegramStatus, restartTelegram, stopTelegram
} from '../services/api';
import ToolSettings from './ToolSettings';

export default function Settings({ onClose }) {
  const [apiKey, setApiKey] = useState('');
  const [apiKeyMasked, setApiKeyMasked] = useState('');
  const [model, setModel] = useState('openai/gpt-4o-mini');
  const [temperature, setTemperature] = useState(0.5);
  const [sttModel, setSttModel] = useState('');
  const [ttsModel, setTtsModel] = useState('');
  const [imageGenModel, setImageGenModel] = useState('');
  const [openaiKey, setOpenaiKey] = useState('');
  const [openaiKeyMasked, setOpenaiKeyMasked] = useState('');
  const [useWhisper, setUseWhisper] = useState(false);
  const [showOpenaiKey, setShowOpenaiKey] = useState(false);
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

  // Telegram
  const [tgToken, setTgToken] = useState('');
  const [tgTokenMasked, setTgTokenMasked] = useState('');
  const [tgShowToken, setTgShowToken] = useState(false);
  const [tgAllowedUsers, setTgAllowedUsers] = useState('');
  const [tgRunning, setTgRunning] = useState(false);
  const [tgSaving, setTgSaving] = useState(false);

  useEffect(() => {
    loadSettings();
    loadMcpServers();
    loadMcpTools();
    loadTelegramSettings();
  }, []);

  async function loadSettings() {
    const s = await fetchSettings();
    setApiKey(s.openrouter_api_key || '');
    setApiKeyMasked(s.openrouter_api_key_masked || '');
    setModel(s.model || 'openai/gpt-4o-mini');
    setTemperature(s.temperature ?? 0.5);
    setSttModel(s.stt_model || '');
    setTtsModel(s.tts_model || '');
    setImageGenModel(s.image_gen_model || '');
    setOpenaiKeyMasked(s.openai_api_key_masked || '');
    setUseWhisper(s.use_openai_whisper || false);
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
    const data = {
      model, temperature, stt_model: sttModel, tts_model: ttsModel, image_gen_model: imageGenModel,
      use_openai_whisper: useWhisper,
    };
    if (apiKey && apiKey !== '') data.openrouter_api_key = apiKey;
    if (openaiKey && openaiKey !== '') data.openai_api_key = openaiKey;
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

  async function loadTelegramSettings() {
    const s = await fetchTelegramSettings();
    setTgTokenMasked(s.bot_token_masked || '');
    setTgAllowedUsers((s.allowed_users || []).join('\n'));
    const status = await fetchTelegramStatus();
    setTgRunning(status.running || false);
  }

  async function handleTelegramSave() {
    setTgSaving(true);
    const users = tgAllowedUsers
      .split(/[\n,]+/)
      .map(u => u.trim().replace(/^@/, ''))
      .filter(Boolean);
    const data = { allowed_users: users };
    if (tgToken) data.bot_token = tgToken;
    await updateTelegramSettings(data);
    setTgToken('');
    setMessage('Telegram-Einstellungen gespeichert!');
    setTgSaving(false);
    setTimeout(() => setMessage(''), 3000);
    await loadTelegramSettings();
  }

  async function handleTelegramRestart() {
    setMessage('Telegram Gateway wird gestartet...');
    const res = await restartTelegram();
    if (res.success) {
      setTgRunning(true);
      setMessage('Telegram Gateway gestartet!');
    } else {
      setMessage('Fehler: ' + (res.error || 'Unbekannt'));
    }
    setTimeout(() => setMessage(''), 3000);
  }

  async function handleTelegramStop() {
    await stopTelegram();
    setTgRunning(false);
    setMessage('Telegram Gateway gestoppt.');
    setTimeout(() => setMessage(''), 3000);
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
              Chat-Modell
              <input
                type="text"
                value={model}
                onChange={(e) => setModel(e.target.value)}
                placeholder="openai/gpt-4o-mini"
              />
              <small>z.B. openai/gpt-4o, anthropic/claude-3.5-sonnet, google/gemini-pro — <a href="https://openrouter.ai/models" target="_blank" rel="noopener noreferrer" style={{color: 'var(--accent)'}}>Alle Modelle ansehen</a></small>
            </label>
            <label>
              Kreativität (Temperatur)
              <select
                value={temperature}
                onChange={(e) => setTemperature(parseFloat(e.target.value))}
                className="settings-select"
              >
                <option value={0.1}>Genau (0.1) — präzise, deterministisch</option>
                <option value={0.5}>Mittel (0.5) — ausgewogen</option>
                <option value={0.8}>Frei (0.8) — kreativ, variabel</option>
              </select>
              <small>Bestimmt wie kreativ / unvorhersehbar die Antworten sind</small>
            </label>
            <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={useWhisper}
                onChange={(e) => setUseWhisper(e.target.checked)}
                style={{ width: 'auto', margin: 0 }}
              />
              OpenAI Whisper für Spracherkennung (STT) verwenden
            </label>
            {useWhisper ? (
              <label>
                OpenAI API Key
                <div className="input-group">
                  <input
                    type={showOpenaiKey ? 'text' : 'password'}
                    value={openaiKey}
                    onChange={(e) => setOpenaiKey(e.target.value)}
                    placeholder={openaiKeyMasked || 'sk-...'}
                  />
                  <button
                    type="button"
                    className="btn-toggle-key"
                    onClick={() => setShowOpenaiKey(!showOpenaiKey)}
                  >
                    {showOpenaiKey ? 'Verbergen' : 'Anzeigen'}
                  </button>
                </div>
                <small>Verwendet <code>whisper-1</code> — zuverlässiger als OpenRouter für Audio. <a href="https://platform.openai.com/api-keys" target="_blank" rel="noopener noreferrer" style={{color: 'var(--accent)'}}>API Key erstellen</a></small>
              </label>
            ) : (
              <label>
                Speech-to-Text Modell via OpenRouter
                <input
                  type="text"
                  value={sttModel}
                  onChange={(e) => setSttModel(e.target.value)}
                  placeholder={`leer = Chat-Modell (${model}) verwenden`}
                />
                <small>Für Sprachnachrichten in Telegram. Empfohlen: <code>google/gemini-2.5-flash</code></small>
              </label>
            )}
            <label>
              Text-to-Speech Modell (TTS)
              <input
                type="text"
                value={ttsModel}
                onChange={(e) => setTtsModel(e.target.value)}
                placeholder={`leer = Chat-Modell (${model}) verwenden`}
              />
              <small>Für Sprachausgabe (zukünftige Funktion)</small>
            </label>
            <label>
              Bildgenerierungs-Modell
              <input
                type="text"
                value={imageGenModel}
                onChange={(e) => setImageGenModel(e.target.value)}
                placeholder={`leer = Chat-Modell (${model}) verwenden`}
              />
              <small>Empfohlen: <code>google/gemini-2.5-flash-image-preview</code> oder <code>black-forest-labs/flux-1.1-pro</code></small>
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

          <div className="settings-section">
            <h3>
              Telegram Gateway
              <span
                className="tg-status-badge"
                style={{
                  marginLeft: '10px',
                  fontSize: '0.75rem',
                  padding: '2px 8px',
                  borderRadius: '4px',
                  background: tgRunning ? '#1a4a1a' : '#3a1a1a',
                  color: tgRunning ? '#4caf50' : '#f44336',
                  border: `1px solid ${tgRunning ? '#4caf50' : '#f44336'}`,
                }}
              >
                {tgRunning ? 'AKTIV' : 'GESTOPPT'}
              </span>
            </h3>
            <label>
              Bot Token
              <div className="input-group">
                <input
                  type={tgShowToken ? 'text' : 'password'}
                  value={tgToken}
                  onChange={(e) => setTgToken(e.target.value)}
                  placeholder={tgTokenMasked || '1234567890:ABC...'}
                />
                <button
                  type="button"
                  className="btn-toggle-key"
                  onClick={() => setTgShowToken(!tgShowToken)}
                >
                  {tgShowToken ? 'Verbergen' : 'Anzeigen'}
                </button>
              </div>
              <small>Bot-Token von @BotFather</small>
            </label>
            <label>
              Erlaubte Nutzer (ein Username pro Zeile, ohne @)
              <textarea
                rows={4}
                value={tgAllowedUsers}
                onChange={(e) => setTgAllowedUsers(e.target.value)}
                placeholder={'maxmustermann\njohndoe'}
                style={{
                  width: '100%',
                  background: 'var(--bg-secondary)',
                  color: 'var(--text-primary)',
                  border: '1px solid var(--border)',
                  borderRadius: '4px',
                  padding: '8px',
                  fontFamily: 'inherit',
                  resize: 'vertical',
                  marginTop: '6px',
                }}
              />
              <small>Nur diese Telegram-Usernames dürfen Nachrichten senden</small>
            </label>
            <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginTop: '8px' }}>
              <button className="btn-save" onClick={handleTelegramSave} disabled={tgSaving}>
                {tgSaving ? 'Speichere...' : 'Speichern'}
              </button>
              <button className="btn-reload-mcp" onClick={handleTelegramRestart}>
                Gateway starten / neu starten
              </button>
              {tgRunning && (
                <button
                  className="btn-delete-server"
                  onClick={handleTelegramStop}
                  style={{ marginLeft: 'auto' }}
                >
                  Gateway stoppen
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
