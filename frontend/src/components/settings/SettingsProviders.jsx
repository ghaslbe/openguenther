import React, { useState } from 'react';
import { updateProvider } from '../../services/api';

const PROVIDER_ORDER = ['openrouter', 'ollama', 'lmstudio'];

export default function SettingsProviders({ providers, onProvidersChange }) {
  const [expanded, setExpanded] = useState({});
  const [editState, setEditState] = useState({});
  const [showKeys, setShowKeys] = useState({});
  const [saving, setSaving] = useState({});
  const [message, setMessage] = useState('');

  function getEdit(pid) {
    return editState[pid] || {
      name: providers[pid]?.name || '',
      base_url: providers[pid]?.base_url || '',
      api_key: '',
    };
  }

  function setEdit(pid, field, value) {
    setEditState(prev => ({
      ...prev,
      [pid]: { ...getEdit(pid), [field]: value }
    }));
  }

  function toggleExpand(pid) {
    setExpanded(prev => ({ ...prev, [pid]: !prev[pid] }));
    // Initialize edit state with current values
    if (!expanded[pid] && providers[pid]) {
      setEditState(prev => ({
        ...prev,
        [pid]: { name: providers[pid].name, base_url: providers[pid].base_url, api_key: '' }
      }));
    }
  }

  async function handleToggleEnabled(pid, e) {
    e.stopPropagation();
    const current = providers[pid] || {};
    await updateProvider(pid, { enabled: !current.enabled });
    onProvidersChange();
  }

  async function handleSave(pid) {
    setSaving(prev => ({ ...prev, [pid]: true }));
    const edit = getEdit(pid);
    await updateProvider(pid, edit);
    onProvidersChange();
    setEditState(prev => ({ ...prev, [pid]: { ...edit, api_key: '' } }));
    setMessage('Gespeichert!');
    setSaving(prev => ({ ...prev, [pid]: false }));
    setTimeout(() => setMessage(''), 3000);
  }

  const orderedProviders = [
    ...PROVIDER_ORDER.filter(pid => providers[pid]),
    ...Object.keys(providers).filter(pid => !PROVIDER_ORDER.includes(pid)),
  ];

  return (
    <div>
      {message && <div className="settings-message">{message}</div>}
      <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginBottom: '20px' }}>
        Alle Provider sind OpenAI-API-kompatibel. Für Ollama und LM Studio ist kein API Key nötig.
      </p>

      {orderedProviders.map(pid => {
        const p = providers[pid] || {};
        const edit = getEdit(pid);
        const isExpanded = expanded[pid];
        const isSaving = saving[pid];

        return (
          <div key={pid} className="provider-card">
            <div className="provider-card-header" onClick={() => toggleExpand(pid)}>
              <span className="provider-name">{p.name || pid}</span>
              <span className={`provider-badge ${p.enabled ? 'active' : 'inactive'}`}>
                {p.enabled ? 'Aktiv' : 'Inaktiv'}
              </span>
              <label className="provider-toggle" onClick={(e) => e.stopPropagation()}>
                <input
                  type="checkbox"
                  checked={!!p.enabled}
                  onChange={(e) => handleToggleEnabled(pid, e)}
                />
                <span className="provider-toggle-slider" />
              </label>
              <span className={`provider-expand-icon ${isExpanded ? 'open' : ''}`}>▼</span>
            </div>

            {isExpanded && (
              <div className="provider-card-body">
                <div className="settings-section" style={{ marginTop: '12px', marginBottom: 0 }}>
                  <label>
                    Name
                    <input
                      type="text"
                      value={edit.name}
                      onChange={(e) => setEdit(pid, 'name', e.target.value)}
                      placeholder={p.name || pid}
                    />
                  </label>
                  <label>
                    Base URL
                    <input
                      type="text"
                      value={edit.base_url}
                      onChange={(e) => setEdit(pid, 'base_url', e.target.value)}
                      placeholder="https://openrouter.ai/api/v1"
                    />
                    <small>Endet mit <code>/v1</code> — <code>/chat/completions</code> wird automatisch angehängt</small>
                  </label>
                  <label>
                    API Key {pid !== 'openrouter' && <span style={{ opacity: 0.6 }}>(optional)</span>}
                    <div className="input-group">
                      <input
                        type={showKeys[pid] ? 'text' : 'password'}
                        value={edit.api_key}
                        onChange={(e) => setEdit(pid, 'api_key', e.target.value)}
                        placeholder={p.api_key_masked || (pid === 'openrouter' ? 'sk-or-v1-...' : 'leer lassen wenn nicht nötig')}
                      />
                      <button
                        type="button"
                        className="btn-toggle-key"
                        onClick={() => setShowKeys(prev => ({ ...prev, [pid]: !prev[pid] }))}
                      >
                        {showKeys[pid] ? 'Verbergen' : 'Anzeigen'}
                      </button>
                    </div>
                    <small>Nur ausfüllen um den gespeicherten Key zu ändern</small>
                  </label>
                  <button className="btn-save" onClick={() => handleSave(pid)} disabled={isSaving}>
                    {isSaving ? 'Speichere...' : 'Speichern'}
                  </button>
                </div>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
