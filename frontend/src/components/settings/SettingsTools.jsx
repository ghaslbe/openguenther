import React, { useState, useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import ReactMarkdown from 'react-markdown';
import { fetchMcpTools, fetchToolSettings, updateToolSettings, reloadMcpTools, uploadCustomTool } from '../../services/api';

export default function SettingsTools({ providers }) {
  const { t } = useTranslation();
  const [tools, setTools] = useState([]);
  const [expanded, setExpanded] = useState({});
  const [toolEdits, setToolEdits] = useState({});
  const [saving, setSaving] = useState({});
  const [message, setMessage] = useState('');
  const [reloading, setReloading] = useState(false);
  const [showPasswords, setShowPasswords] = useState({});
  const [uploadWarning, setUploadWarning] = useState(false);
  const [pendingFile, setPendingFile] = useState(null);
  const uploadRef = useRef(null);

  useEffect(() => {
    loadTools();
  }, []);

  async function loadTools() {
    const data = await fetchMcpTools();
    setTools(data);
    // Initialize edit state from current values
    const edits = {};
    for (const tool of data) {
      edits[tool.name] = {
        provider: tool.current_provider || '',
        model: tool.current_model || '',
        timeout: '',
      };
      // Add schema fields
      for (const field of (tool.settings_schema || [])) {
        edits[tool.name][field.key] = '';
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
    setMessage(t('settings.tools.savedMsg', { name: tool.name }));
    setSaving(prev => ({ ...prev, [tool.name]: false }));
    setTimeout(() => setMessage(''), 3000);
  }

  async function handleReload() {
    setReloading(true);
    await reloadMcpTools();
    await loadTools();
    setMessage(t('settings.tools.reloaded'));
    setReloading(false);
    setTimeout(() => setMessage(''), 3000);
  }

  function handleUploadClick() {
    if (uploadRef.current) {
      uploadRef.current.value = '';
      uploadRef.current.click();
    }
  }

  function handleFileChange(e) {
    const file = e.target.files[0];
    if (!file) return;
    setPendingFile(file);
    setUploadWarning(true);
  }

  async function confirmUpload() {
    setUploadWarning(false);
    const result = await uploadCustomTool(pendingFile);
    setPendingFile(null);
    if (result.success) {
      setMessage(t('settings.tools.customUploaded', { name: result.tool_name }));
      await loadTools();
    } else {
      setMessage(t('settings.tools.customUploadError') + (result.error ? `: ${result.error}` : ''));
    }
    setTimeout(() => setMessage(''), 4000);
  }

  function cancelUpload() {
    setUploadWarning(false);
    setPendingFile(null);
  }

  const activeProviders = Object.entries(providers || {}).filter(([, p]) => p.enabled);
  const sortByName = (a, b) => a.name.localeCompare(b.name);
  const builtinTools = tools.filter(t => t.builtin && !t.custom).sort(sortByName);
  const customMcpTools = tools.filter(t => t.custom).sort(sortByName);
  const externalTools = tools.filter(t => !t.builtin).sort(sortByName);

  const TOOL_CATEGORY = {
    // Databases
    airtable:               { label: 'Airtable',      bg: '#fcb400', fg: '#000' },
    mysql:                  { label: 'MySQL',          bg: '#00758f', fg: '#fff' },
    postgresql:             { label: 'PostgreSQL',     bg: '#336791', fg: '#fff' },
    mongodb:                { label: 'MongoDB',        bg: '#4db33d', fg: '#fff' },
    pinecone:               { label: 'Pinecone',       bg: '#1c17ff', fg: '#fff' },
    // Project / Productivity
    trello:                 { label: 'Trello',         bg: '#0052cc', fg: '#fff' },
    notion:                 { label: 'Notion',         bg: '#333',    fg: '#fff' },
    todoist:                { label: 'Todoist',        bg: '#db4035', fg: '#fff' },
    // Communication
    slack:                  { label: 'Slack',          bg: '#4a154b', fg: '#fff' },
    discord:                { label: 'Discord',        bg: '#5865f2', fg: '#fff' },
    send_telegram:          { label: 'Telegram',       bg: '#0088cc', fg: '#fff' },
    send_email:             { label: 'SMTP',           bg: '#555',    fg: '#fff' },
    // Social / Publishing
    post_tweet:             { label: 'Twitter/X',      bg: '#111',    fg: '#fff' },
    post_bluesky:           { label: 'Bluesky',        bg: '#0085ff', fg: '#fff' },
    post_mastodon:          { label: 'Mastodon',       bg: '#6364ff', fg: '#fff' },
    // CRM
    hubspot:                { label: 'HubSpot',        bg: '#ff7a59', fg: '#fff' },
    pipedrive:              { label: 'Pipedrive',      bg: '#215732', fg: '#fff' },
    // Media / AI
    text_to_speech:         { label: 'ElevenLabs',     bg: '#ff6c2f', fg: '#fff' },
    get_youtube_transcript: { label: 'YouTube',        bg: '#ff0000', fg: '#fff' },
    generate_image:         { label: 'Image AI',       bg: '#7c3aed', fg: '#fff' },
    // Data / Web Services
    get_stock_price:        { label: 'Yahoo Finance',  bg: '#6001d2', fg: '#fff' },
    get_flights_nearby:     { label: 'OpenSky',        bg: '#0ea5e9', fg: '#fff' },
    get_weather:            { label: 'Open-Meteo',     bg: '#0284c7', fg: '#fff' },
    geocode_location:       { label: 'OpenStreetMap',  bg: '#7ebc6f', fg: '#000' },
    resolve_callsign:       { label: 'ADSB.one',       bg: '#334155', fg: '#fff' },
    wikipedia_search:       { label: 'Wikipedia',      bg: '#737373', fg: '#fff' },
    fetch_url:              { label: 'Web',            bg: '#475569', fg: '#fff' },
    seo:                    { label: 'Web Scraping',   bg: '#ea580c', fg: '#fff' },
    wordpress:              { label: 'WordPress',      bg: '#21759b', fg: '#fff' },
  };

  function renderTool(tool) {
    const edit = toolEdits[tool.name] || {};
    const isOpen = expanded[tool.name];
    const hasOverride = tool.current_provider || tool.current_model;
    const schema = tool.settings_schema || [];

    const cat = TOOL_CATEGORY[tool.name];

    return (
      <div key={tool.name} className="tool-accordion-item">
        <div className="tool-accordion-header" onClick={() => toggleExpand(tool)}>
          {tool.builtin && !tool.custom && (
            cat
              ? <span className="tool-accordion-badge" style={{ background: cat.bg, color: cat.fg }}>{cat.label}</span>
              : <span className="tool-accordion-badge" style={{ background: '#2a7a3b', color: '#fff' }}>Local</span>
          )}
          <span className="tool-accordion-name">{tool.name}</span>
          {tool.builtin && !tool.custom && (
            <span className="tool-accordion-badge" style={{ background: '#2a7a3b', color: '#fff' }}>
              Built-in
            </span>
          )}
          {tool.custom && (
            <span className="tool-accordion-badge" style={{ background: '#b85c00', color: '#fff' }}>
              Custom
            </span>
          )}
          {!tool.builtin && (
            <span className="tool-accordion-badge" style={{ background: '#1a5fa8', color: '#fff' }}>
              Extern
            </span>
          )}
          {hasOverride && (
            <span className="tool-accordion-badge override" title={`${tool.current_provider || 'std'} / ${tool.current_model || 'std'}`}>
              {t('settings.tools.override')}
            </span>
          )}
          <span className={`tool-accordion-chevron ${isOpen ? 'open' : ''}`}>▼</span>
        </div>

        {isOpen && (
          <div className="tool-accordion-body">
            {(tool.settings_info || tool.description) && (
              <div style={{
                marginBottom: '12px',
                padding: '10px 12px',
                background: 'var(--bg-dark)',
                border: '1px solid var(--border)',
                borderRadius: '6px',
                fontSize: '12px',
                color: 'var(--text-secondary)',
                lineHeight: '1.6',
              }}>
                <ReactMarkdown>{tool.settings_info || tool.description}</ReactMarkdown>
              </div>
            )}
            {tool.agent_overridable !== false && (
              <>
                <div className="tool-field-row">
                  <label>{t('settings.tools.providerOverride')}</label>
                  <select
                    value={edit.provider || ''}
                    onChange={(e) => setField(tool.name, 'provider', e.target.value)}
                  >
                    <option value="">{t('settings.tools.useDefault')}</option>
                    {activeProviders.map(([pid, p]) => (
                      <option key={pid} value={pid}>{p.name}</option>
                    ))}
                  </select>
                </div>
                <div className="tool-field-row">
                  <label>{t('settings.tools.modelOverride')}</label>
                  <input
                    type="text"
                    value={edit.model || ''}
                    onChange={(e) => setField(tool.name, 'model', e.target.value)}
                    placeholder={t('settings.tools.modelPlaceholder')}
                  />
                </div>
              </>
            )}

            <div className="tool-field-row">
              <label>{t('settings.tools.timeoutLabel')}</label>
              <input
                type="number"
                value={edit.timeout || ''}
                onChange={(e) => setField(tool.name, 'timeout', e.target.value)}
                placeholder={t('settings.tools.timeoutPlaceholder')}
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
                          {showPasswords[`${tool.name}.${field.key}`] ? t('settings.tools.hide') : t('settings.tools.show')}
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

            <div style={{ display: 'flex', gap: '8px', alignItems: 'center', flexWrap: 'wrap' }}>
              <button className="btn-tool-save" onClick={() => handleSave(tool)} disabled={saving[tool.name]}>
                {saving[tool.name] ? t('settings.tools.saving') : t('settings.tools.save')}
              </button>
              {tool.custom && (
                <a
                  href={`/api/custom-tools/${tool.name}/download`}
                  download={`${tool.name}.zip`}
                  className="btn-tool-save"
                  style={{ textDecoration: 'none' }}
                  onClick={e => e.stopPropagation()}
                >
                  {t('settings.tools.customDownload')}
                </a>
              )}
            </div>
          </div>
        )}

        {!isOpen && (
          <div className="tool-accordion-desc">{tool.description}</div>
        )}
      </div>
    );
  }

  return (
    <div>
      {message && <div className="settings-message">{message}</div>}
      <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginBottom: '16px' }}>
        {t('settings.tools.description')}
      </p>

      <div className="settings-section">
        <h3>{t('settings.tools.builtinSection')}</h3>
        {builtinTools.map(renderTool)}
      </div>

      <div className="settings-section">
        <h3>{t('settings.tools.customSection')}</h3>
        {customMcpTools.length === 0
          ? <p style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>{t('settings.tools.customEmpty')}</p>
          : customMcpTools.map(renderTool)
        }
        <div style={{ marginTop: '12px' }}>
          <input
            type="file"
            accept=".zip"
            ref={uploadRef}
            style={{ display: 'none' }}
            onChange={handleFileChange}
          />
          <button className="btn-reload-mcp" onClick={handleUploadClick}>
            {t('settings.tools.customUpload')}
          </button>
        </div>
      </div>

      <div className="settings-section">
        <h3>{t('settings.tools.externalSection')}</h3>
        {externalTools.length === 0
          ? <p style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>{t('settings.tools.noExternal')}</p>
          : externalTools.map(renderTool)
        }
      </div>

      <button className="btn-reload-mcp" onClick={handleReload} disabled={reloading}>
        {reloading ? t('settings.tools.reloading') : t('settings.tools.reload')}
      </button>

      {uploadWarning && (
        <div style={{
          position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)',
          display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000
        }}>
          <div style={{
            background: 'var(--bg-card)', border: '1px solid var(--border)',
            borderRadius: '10px', padding: '28px 32px', maxWidth: '440px', width: '90%'
          }}>
            <h3 style={{ marginTop: 0, marginBottom: '12px' }}>{t('settings.tools.warnTitle')}</h3>
            <p style={{ fontSize: '13px', color: 'var(--text-secondary)', lineHeight: '1.6', whiteSpace: 'pre-line', marginBottom: '20px' }}>
              {t('settings.tools.warnText')}
            </p>
            <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
              <button className="btn-tool-save" style={{ background: 'var(--bg-dark)', color: 'var(--text-secondary)' }} onClick={cancelUpload}>
                {t('settings.tools.warnCancel')}
              </button>
              <button className="btn-tool-save" onClick={confirmUpload}>
                {t('settings.tools.warnConfirm')}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
