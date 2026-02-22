import React, { useState, useEffect } from 'react';
import { fetchMcpTools, fetchToolSettings, updateToolSettings, reloadMcpTools } from '../../services/api';

export default function SettingsTools({ providers }) {
  const [tools, setTools] = useState([]);
  const [expanded, setExpanded] = useState({});
  const [toolEdits, setToolEdits] = useState({});
  const [saving, setSaving] = useState({});
  const [message, setMessage] = useState('');
  const [reloading, setReloading] = useState(false);
  const [showPasswords, setShowPasswords] = useState({});

  useEffect(() => {
    loadTools();
  }, []);

  async function loadTools() {
    const data = await fetchMcpTools();
    setTools(data);
    // Initialize edit state from current values
    const edits = {};
    for (const t of data) {
      edits[t.name] = {
        provider: t.current_provider || '',
        model: t.current_model || '',
        timeout: '',
      };
      // Add schema fields
      for (const field of (t.settings_schema || [])) {
        // Will be loaded when expanded — keep empty for now
        edits[t.name][field.key] = '';
      }
    }
    setToolEdits(edits);
  }

  async function toggleExpand(tool) {
    const name = tool.name;
    const isOpen = expanded[name];
    if (!isOpen) {
      // Load full tool settings when opening
      const data = await fetchToolSettings(name);
      const vals = {
        provider: tool.current_provider || '',
        model: tool.current_model || '',
        timeout: data.values?.timeout ? String(data.values.timeout) : '',
      };
      for (const field of (data.schema || [])) {
        vals[field.key] = data.values?.[field.key] ?? field.default ?? '';
      }
      setToolEdits(prev => ({ ...prev, [name]: vals }));
    }
    setExpanded(prev => ({ ...prev, [name]: !isOpen }));
  }

  function setField(name, key, value) {
    setToolEdits(prev => ({ ...prev, [name]: { ...(prev[name] || {}), [key]: value } }));
  }

  async function handleSave(tool) {
    setSaving(prev => ({ ...prev, [tool.name]: true }));
    const vals = toolEdits[tool.name] || {};
    await updateToolSettings(tool.name, vals);
    // Refresh tool list to get updated current_provider/current_model
    const updated = await fetchMcpTools();
    setTools(updated);
    setMessage(`${tool.name} gespeichert!`);
    setSaving(prev => ({ ...prev, [tool.name]: false }));
    setTimeout(() => setMessage(''), 3000);
  }

  async function handleReload() {
    setReloading(true);
    await reloadMcpTools();
    await loadTools();
    setMessage('MCP Tools neu geladen!');
    setReloading(false);
    setTimeout(() => setMessage(''), 3000);
  }

  const activeProviders = Object.entries(providers || {}).filter(([, p]) => p.enabled);

  return (
    <div>
      {message && <div className="settings-message">{message}</div>}
      <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginBottom: '16px' }}>
        Pro Tool kannst du Provider und Modell überschreiben. Wenn alle ausgewählten Tools auf denselben Provider/Modell zeigen, wird dieser Override aktiviert.
      </p>

      {tools.map((tool) => {
        const edit = toolEdits[tool.name] || {};
        const isOpen = expanded[tool.name];
        const hasOverride = tool.current_provider || tool.current_model;
        const schema = tool.settings_schema || [];

        return (
          <div key={tool.name} className="tool-accordion-item">
            <div className="tool-accordion-header" onClick={() => toggleExpand(tool)}>
              <span className="tool-accordion-name">{tool.name}</span>
              <span className={`tool-accordion-badge ${hasOverride ? 'override' : ''}`}>
                {tool.builtin ? 'Built-in' : 'Extern'}
              </span>
              {hasOverride && (
                <span className="tool-accordion-badge override" title={`${tool.current_provider || 'std'} / ${tool.current_model || 'std'}`}>
                  Override
                </span>
              )}
              <span className={`tool-accordion-chevron ${isOpen ? 'open' : ''}`}>▼</span>
            </div>

            {isOpen && (
              <div className="tool-accordion-body">
                {tool.agent_overridable !== false && (
                  <>
                    <div className="tool-field-row">
                      <label>Provider Override</label>
                      <select
                        value={edit.provider || ''}
                        onChange={(e) => setField(tool.name, 'provider', e.target.value)}
                      >
                        <option value="">Standard verwenden</option>
                        {activeProviders.map(([pid, p]) => (
                          <option key={pid} value={pid}>{p.name}</option>
                        ))}
                      </select>
                    </div>
                    <div className="tool-field-row">
                      <label>Modell Override</label>
                      <input
                        type="text"
                        value={edit.model || ''}
                        onChange={(e) => setField(tool.name, 'model', e.target.value)}
                        placeholder="leer = Standard-Modell verwenden"
                      />
                    </div>
                  </>
                )}

                <div className="tool-field-row">
                  <label>Timeout (Sekunden)</label>
                  <input
                    type="number"
                    value={edit.timeout || ''}
                    onChange={(e) => setField(tool.name, 'timeout', e.target.value)}
                    placeholder="leer = Standard"
                    min="1"
                    max="600"
                  />
                </div>

                {schema.length > 0 && (
                  <div style={tool.agent_overridable !== false ? { borderTop: '1px solid var(--border)', paddingTop: '10px', marginTop: '2px' } : {}}>
                    {schema.map((field) => (
                      <div key={field.key} className="tool-field-row" style={{ marginBottom: '8px' }}>
                        <label>{field.label}</label>
                        {field.type === 'password' ? (
                          <div className="input-group" style={{ marginTop: 0 }}>
                            <input
                              type={showPasswords[`${tool.name}.${field.key}`] ? 'text' : 'password'}
                              value={edit[field.key] || ''}
                              onChange={(e) => setField(tool.name, field.key, e.target.value)}
                              placeholder={field.placeholder || ''}
                            />
                            <button
                              type="button"
                              className="btn-toggle-key"
                              onClick={() => setShowPasswords(prev => ({
                                ...prev, [`${tool.name}.${field.key}`]: !prev[`${tool.name}.${field.key}`]
                              }))}
                            >
                              {showPasswords[`${tool.name}.${field.key}`] ? 'Verbergen' : 'Anzeigen'}
                            </button>
                          </div>
                        ) : (
                          <input
                            type="text"
                            value={edit[field.key] || ''}
                            onChange={(e) => setField(tool.name, field.key, e.target.value)}
                            placeholder={field.placeholder || ''}
                          />
                        )}
                        {field.description && (
                          <small style={{ fontSize: '11px', color: 'var(--text-secondary)', opacity: 0.7 }}>{field.description}</small>
                        )}
                      </div>
                    ))}
                  </div>
                )}

                <button className="btn-tool-save" onClick={() => handleSave(tool)} disabled={saving[tool.name]}>
                  {saving[tool.name] ? 'Speichere...' : 'Speichern'}
                </button>
              </div>
            )}

            {!isOpen && (
              <div className="tool-accordion-desc">{tool.description}</div>
            )}
          </div>
        );
      })}

      <button className="btn-reload-mcp" onClick={handleReload} disabled={reloading}>
        {reloading ? 'Lade...' : 'MCP Tools neu laden'}
      </button>
    </div>
  );
}
