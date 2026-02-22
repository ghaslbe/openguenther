import React, { useState, useEffect } from 'react';
import {
  fetchTelegramSettings, updateTelegramSettings,
  fetchTelegramStatus, restartTelegram, stopTelegram
} from '../../services/api';

export default function SettingsTelegram() {
  const [tgToken, setTgToken] = useState('');
  const [tgTokenMasked, setTgTokenMasked] = useState('');
  const [tgShowToken, setTgShowToken] = useState(false);
  const [tgAllowedUsers, setTgAllowedUsers] = useState('');
  const [tgRunning, setTgRunning] = useState(false);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');

  useEffect(() => {
    loadTelegramSettings();
  }, []);

  async function loadTelegramSettings() {
    const s = await fetchTelegramSettings();
    setTgTokenMasked(s.bot_token_masked || '');
    setTgAllowedUsers((s.allowed_users || []).join('\n'));
    const status = await fetchTelegramStatus();
    setTgRunning(status.running || false);
  }

  async function handleSave() {
    setSaving(true);
    const users = tgAllowedUsers
      .split(/[\n,]+/)
      .map(u => u.trim().replace(/^@/, ''))
      .filter(Boolean);
    const data = { allowed_users: users };
    if (tgToken) data.bot_token = tgToken;
    await updateTelegramSettings(data);
    setTgToken('');
    setMessage('Telegram-Einstellungen gespeichert!');
    setSaving(false);
    setTimeout(() => setMessage(''), 3000);
    await loadTelegramSettings();
  }

  async function handleRestart() {
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

  async function handleStop() {
    await stopTelegram();
    setTgRunning(false);
    setMessage('Telegram Gateway gestoppt.');
    setTimeout(() => setMessage(''), 3000);
  }

  return (
    <div>
      {message && <div className="settings-message">{message}</div>}

      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '20px' }}>
        <span style={{ fontSize: '14px', color: 'var(--text-secondary)' }}>Gateway-Status:</span>
        <span
          style={{
            fontSize: '12px',
            padding: '3px 10px',
            borderRadius: '4px',
            background: tgRunning ? '#1a4a1a' : '#3a1a1a',
            color: tgRunning ? '#4caf50' : '#f44336',
            border: `1px solid ${tgRunning ? '#4caf50' : '#f44336'}`,
            fontWeight: 700,
          }}
        >
          {tgRunning ? 'AKTIV' : 'GESTOPPT'}
        </span>
      </div>

      <div className="settings-section">
        <h3>Konfiguration</h3>
        <label>
          Bot Token
          <div className="input-group">
            <input
              type={tgShowToken ? 'text' : 'password'}
              value={tgToken}
              onChange={(e) => setTgToken(e.target.value)}
              placeholder={tgTokenMasked || '1234567890:ABC...'}
            />
            <button type="button" className="btn-toggle-key" onClick={() => setTgShowToken(!tgShowToken)}>
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
              display: 'block',
              width: '100%',
              marginTop: '4px',
              background: 'var(--bg-input)',
              color: 'var(--text-primary)',
              border: '1px solid var(--border)',
              borderRadius: '6px',
              padding: '10px 12px',
              fontFamily: 'inherit',
              fontSize: '14px',
              resize: 'vertical',
            }}
          />
          <small>Nur diese Telegram-Usernames dürfen Nachrichten senden</small>
        </label>
      </div>

      <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
        <button className="btn-save" onClick={handleSave} disabled={saving}>
          {saving ? 'Speichere...' : 'Speichern'}
        </button>
        <button className="btn-reload-mcp" style={{ width: 'auto', marginTop: '8px' }} onClick={handleRestart}>
          Gateway starten / neu starten
        </button>
        {tgRunning && (
          <button className="btn-delete-server" style={{ marginTop: '8px' }} onClick={handleStop}>
            Gateway stoppen
          </button>
        )}
      </div>
    </div>
  );
}
